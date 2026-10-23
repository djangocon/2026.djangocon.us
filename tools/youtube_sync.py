# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "google-api-python-client",
#     "google-auth-oauthlib",
#     "python-frontmatter",
#     "rich",
#     "typer",
#     "yt-dlp",
# ]
# ///
"""
Match the videos in a YouTube playlist to our talk files and sync them up.

    uv run tools/youtube_sync.py PLAYLIST_ID            # dry run: report only
    uv run tools/youtube_sync.py PLAYLIST_ID --write    # also update front matter

For every video in the playlist we look for the talk it belongs to by:

1. the talk's permalink appearing in the video description (our YouTube
   descriptions include "https://YEAR.djangocon.us/talks/slug/"),
2. title similarity, ignoring the " with Presenter Name" suffix, and
3. presenter names showing up in the video title or description.

Each match gets a suggested YouTube title and description (presenter links,
talk abstract) written to OUTPUT_DIR/descriptions/, plus a report.csv of every
match, low-confidence match, and leftover video/talk.

With --write, matched talks get `video_url` and `youtube_id` added to (or
updated in) their front matter. Only those two lines are touched, so the rest
of the file stays byte-for-byte the same. Low-confidence matches are never
written; fix them by hand or re-run after adjusting the video title.

With --update-youtube, the suggested titles and descriptions are pushed to
YouTube through the Data API, signed in as a channel manager (see
tools/README.md for the one-time OAuth setup). Signing in also lets us read
private playlists. Before anything changes you get a summary and a prompt, and
the current title/description of every video about to change is saved to
OUTPUT_DIR/backups/ so it can be restored with --restore BACKUP_FILE.
"""

import csv
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs, urlparse

import frontmatter
import typer
from rich.console import Console
from rich.table import Table
from yt_dlp import YoutubeDL

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "src" / "_content"
SESSION_DIRS = ("talks", "tutorials")

# A match needs at least this score to be written. Anything between
# REVIEW_SCORE and MATCH_SCORE is reported for a human to check.
MATCH_SCORE = 60
REVIEW_SCORE = 35

YOUTUBE_TITLE_LIMIT = 100
YOUTUBE_DESCRIPTION_LIMIT = 5000

# OAuth: the client secret comes from Google Cloud Console (Desktop app client).
# The token is cached outside the repo so it can never be committed.
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CONFIG_DIR = Path.home() / ".config" / "djangocon-youtube-sync"
# If you already use the Google Workspace CLI (gws), its Desktop OAuth client
# works too, as long as the YouTube Data API is enabled on its GCP project.
GWS_CLIENT_SECRETS = Path.home() / ".config" / "gws" / "client_secret.json"

console = Console()
app = typer.Typer(add_completion=False)


@dataclass
class Presenter:
    slug: str
    name: str
    social: dict


@dataclass
class Talk:
    path: Path
    title: str
    permalink: str
    body: str
    presenters: list[Presenter]
    video_url: str | None = None

    @property
    def presenter_names(self) -> str:
        return join_names([p.name for p in self.presenters])


@dataclass
class Video:
    id: str
    title: str
    description: str

    @property
    def url(self) -> str:
        return f"https://youtu.be/{self.id}"


@dataclass
class Match:
    video: Video
    talk: Talk
    score: float
    reasons: list[str] = field(default_factory=list)


def join_names(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def strip_presenters(yt_title: str) -> str:
    """'My Talk with Jane Doe and Sam Roe' -> 'My Talk'."""
    if " with " in yt_title:
        return yt_title.rsplit(" with ", 1)[0]
    return yt_title


def load_presenters() -> dict[str, Presenter]:
    presenters = {}
    for path in sorted((CONTENT_DIR / "presenters").glob("*.md")):
        post = frontmatter.load(path)
        presenters[path.stem] = Presenter(
            slug=path.stem,
            name=post.get("name", path.stem),
            social=post.get("social") or {},
        )
    return presenters


def load_talks(presenters: dict[str, Presenter]) -> list[Talk]:
    talks = []
    for directory in SESSION_DIRS:
        for path in sorted((CONTENT_DIR / "schedule" / directory).glob("*.md")):
            post = frontmatter.load(path)
            if post.get("hidden") or not post.get("permalink"):
                continue
            talks.append(
                Talk(
                    path=path,
                    title=post["title"],
                    permalink=post["permalink"],
                    body=post.content.strip(),
                    presenters=[
                        presenters[slug]
                        for slug in post.get("presenter_slugs") or []
                        if slug in presenters
                    ],
                    video_url=post.get("video_url"),
                )
            )
    return talks


def fetch_playlist(playlist: str, cache: Path | None, youtube=None) -> list[Video]:
    if youtube is not None:
        with console.status("Fetching playlist from the YouTube API..."):
            videos = fetch_playlist_api(youtube, playlist)
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps([v.__dict__ for v in videos], indent=2))
        return videos
    if cache and cache.exists():
        entries = json.loads(cache.read_text())
    else:
        url = f"https://www.youtube.com/playlist?list={playlist_id_from(playlist)}"
        options = {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True}
        with console.status("Fetching playlist from YouTube..."), YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            raise typer.BadParameter(f"Could not load playlist {playlist!r}. Is the ID complete?")
        entries = [
            {"id": e["id"], "title": e.get("title") or "", "description": e.get("description") or ""}
            for e in info.get("entries") or []
            if e
        ]
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(entries, indent=2))
    return [Video(**entry) for entry in entries]


def playlist_id_from(playlist: str) -> str:
    """Accept a bare playlist ID or any URL with ?list=..."""
    if playlist.startswith("http"):
        ids = parse_qs(urlparse(playlist).query).get("list")
        if not ids:
            raise typer.BadParameter(f"No list= parameter in {playlist!r}")
        return ids[0]
    return playlist


def youtube_client(client_secrets: Path, token_path: Path):
    """Build an authorized YouTube Data API client, signing in on first use."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials = None
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), YOUTUBE_SCOPES)
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    if not credentials or not credentials.valid:
        if not client_secrets.exists() and GWS_CLIENT_SECRETS.exists():
            console.print(f"[dim]No {client_secrets}; using the gws OAuth client at {GWS_CLIENT_SECRETS}.")
            client_secrets = GWS_CLIENT_SECRETS
        if not client_secrets.exists():
            raise typer.BadParameter(
                f"No OAuth client secret at {client_secrets}. See tools/README.md for setup."
            )
        console.print(
            "Sign in with the account (or brand account) that manages the DjangoCon US channel."
        )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), YOUTUBE_SCOPES)
        credentials = flow.run_local_server(
            port=0,
            authorization_prompt_message="Open this link to sign in (it should open automatically):\n\n{url}\n",
            success_message="Signed in. You can close this tab and go back to the terminal.",
            # Always show the account picker so the right channel account gets chosen.
            prompt="select_account consent",
        )
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json())
        token_path.chmod(0o600)
    return build("youtube", "v3", credentials=credentials)


def show_channels(youtube) -> None:
    response = youtube.channels().list(part="snippet", mine=True).execute()
    channels = response.get("items", [])
    if not channels:
        console.print("[red]Signed in, but this account has no YouTube channel. Sign in again and pick the DjangoCon US brand account.")
        return
    for channel in channels:
        console.print(f"[green]Signed in as YouTube channel:[/] {channel['snippet']['title']} ({channel['id']})")


def fetch_playlist_api(youtube, playlist: str) -> list[Video]:
    """Read a playlist through the API, which also works for private playlists."""
    videos, page_token = [], None
    while True:
        response = youtube.playlistItems().list(
            part="snippet,status",
            playlistId=playlist_id_from(playlist),
            maxResults=50,
            pageToken=page_token,
        ).execute()
        for item in response.get("items", []):
            snippet = item["snippet"]
            video_id = snippet.get("resourceId", {}).get("videoId")
            if not video_id or snippet.get("title") in ("Deleted video", "Private video"):
                continue
            videos.append(Video(id=video_id, title=snippet["title"], description=snippet.get("description", "")))
        page_token = response.get("nextPageToken")
        if not page_token:
            return videos


def current_snippets(youtube, video_ids: list[str]) -> dict[str, dict]:
    snippets = {}
    for start in range(0, len(video_ids), 50):
        response = youtube.videos().list(part="snippet", id=",".join(video_ids[start : start + 50])).execute()
        for item in response.get("items", []):
            snippets[item["id"]] = item["snippet"]
    return snippets


def update_snippet(youtube, video_id: str, snippet: dict, title: str, description: str) -> None:
    """videos.update replaces the whole snippet, so carry over everything we don't change."""
    body = {
        "id": video_id,
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": snippet["categoryId"],
            **{key: snippet[key] for key in ("tags", "defaultLanguage") if key in snippet},
        },
    }
    youtube.videos().update(part="snippet", body=body).execute()


def push_to_youtube(youtube, matches: list["Match"], site: dict, location: str, output_dir: Path, update_titles: bool, assume_yes: bool) -> None:
    show_channels(youtube)
    snippets = current_snippets(youtube, [m.video.id for m in matches])

    changes = []
    for match in matches:
        snippet = snippets.get(match.video.id)
        if snippet is None:
            console.print(f"[red]Can't see video {match.video.id}; is this account a manager of the channel?")
            continue
        title = youtube_title(match.talk) if update_titles else snippet["title"]
        description = youtube_description(match.talk, site, location)
        if title != snippet["title"] or description != snippet.get("description", ""):
            changes.append((match, snippet, title, description))

    if not changes:
        console.print("[green]YouTube is already up to date.")
        return

    table = Table(title=f"{len(changes)} YouTube videos to update")
    for column in ("Video", "Title", "Description"):
        table.add_column(column)
    for match, snippet, title, description in changes:
        table.add_row(
            match.video.id,
            "unchanged" if title == snippet["title"] else f"[dim]{snippet['title']}[/]\n→ {title}",
            "unchanged" if description == snippet.get("description", "") else f"{len(description)} chars",
        )
    console.print(table)

    backups_dir = output_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    backup = backups_dir / f"youtube-{datetime.now():%Y%m%d-%H%M%S}.json"
    backup.write_text(json.dumps({match.video.id: snippet for match, snippet, _, _ in changes}, indent=2))
    console.print(f"Current titles and descriptions backed up to {backup}")

    if not assume_yes and not typer.confirm(f"Update {len(changes)} videos on YouTube?"):
        raise typer.Abort()

    from googleapiclient.errors import HttpError

    updated = 0
    for match, snippet, title, description in changes:
        try:
            update_snippet(youtube, match.video.id, snippet, title, description)
            updated += 1
        except HttpError as error:
            console.print(f"[red]Failed to update {match.video.id} ({match.talk.path.name}): {error}")
    console.print(f"[green]Updated {updated} of {len(changes)} videos on YouTube.")


def restore_from_backup(youtube, backup: Path, assume_yes: bool) -> None:
    saved = json.loads(backup.read_text())
    if not assume_yes and not typer.confirm(f"Restore {len(saved)} videos on YouTube from {backup}?"):
        raise typer.Abort()
    current = current_snippets(youtube, list(saved))
    for video_id, snippet in saved.items():
        update_snippet(youtube, video_id, current.get(video_id, snippet), snippet["title"], snippet.get("description", ""))
    console.print(f"[green]Restored {len(saved)} videos.")


def score(video: Video, talk: Talk) -> tuple[float, list[str]]:
    points = 0.0
    reasons = []

    if talk.permalink.rstrip("/") + "/" in video.description:
        points += 100
        reasons.append("permalink")

    similarity = SequenceMatcher(
        None, normalize(strip_presenters(video.title)), normalize(talk.title)
    ).ratio()
    points += similarity * 60
    reasons.append(f"title {similarity:.0%}")

    haystack = normalize(f"{video.title} {video.description}")
    found = [p.name for p in talk.presenters if normalize(p.name) and normalize(p.name) in haystack]
    if found:
        points += min(len(found) * 10, 20)
        reasons.append("presenter")

    return points, reasons


def match_videos(videos: list[Video], talks: list[Talk]) -> tuple[list[Match], list[Video], list[Talk]]:
    """Greedy one-to-one assignment, best scoring pairs first."""
    candidates = []
    for video in videos:
        for talk in talks:
            points, reasons = score(video, talk)
            if points >= REVIEW_SCORE:
                candidates.append(Match(video, talk, points, reasons))
    candidates.sort(key=lambda m: m.score, reverse=True)

    matches, used_videos, used_talks = [], set(), set()
    for candidate in candidates:
        if candidate.video.id in used_videos or candidate.talk.path in used_talks:
            continue
        matches.append(candidate)
        used_videos.add(candidate.video.id)
        used_talks.add(candidate.talk.path)

    unmatched_videos = [v for v in videos if v.id not in used_videos]
    unmatched_talks = [t for t in talks if t.path not in used_talks]
    return matches, unmatched_videos, unmatched_talks


def markdown_to_text(markdown: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", markdown)  # links
    text = re.sub(r"(\*\*|__|\*|_)(\S.*?\S|\S)\1", r"\2", text)  # emphasis
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)  # headings
    return text.replace("<", "").replace(">", "")  # YouTube rejects angle brackets


def youtube_title(talk: Talk) -> str:
    title = f"{talk.title} with {talk.presenter_names}" if talk.presenters else talk.title
    return title if len(title) <= YOUTUBE_TITLE_LIMIT else title[: YOUTUBE_TITLE_LIMIT - 1] + "…"


def youtube_description(talk: Talk, site: dict, location: str) -> str:
    """Mirrors src/_includes/youtube-copy-and-paste.html."""
    lines = []
    if talk.body:
        lines += [markdown_to_text(talk.body), ""]
    presented = f"This talk was presented by {talk.presenter_names} at " if talk.presenters else "This talk was presented at "
    lines += [
        f"{presented}DjangoCon US {site['conf_year']} in {location}",
        f"{site['domain']}{talk.permalink}",
        "",
        "LINKS:",
    ]
    for presenter in talk.presenters:
        social = presenter.social
        links = []
        if social.get("github"):
            links.append(f"On GitHub: https://github.com/{social['github']}")
        if social.get("mastodon"):
            links.append(f"On Mastodon: {social['mastodon']}")
        if social.get("twitter"):
            links.append(f"On X: https://x.com/{social['twitter']}")
        if social.get("website"):
            links.append(f"Website: {social['website']}")
        if links:
            lines += [f"Follow {presenter.name} 👇", *links, ""]

    social = site.get("social", {})
    lines += ["Follow DjangoCon US 👇"]
    lines += [social[key] for key in ("mastodon", "bluesky", "x", "linkedin") if social.get(key)]
    lines += [
        "",
        "Follow DEFNA 👇",
        "https://www.defna.org/",
        "",
        f"Video production by the presenter and DjangoCon US {site['conf_year']} volunteers.",
    ]

    description = re.sub(r"\n\s*\n\s*\n+", "\n\n", "\n".join(lines)).strip()
    if len(description) > YOUTUBE_DESCRIPTION_LIMIT:
        # Trim the abstract, never the links.
        overflow = len(description) - YOUTUBE_DESCRIPTION_LIMIT + 1
        abstract = markdown_to_text(talk.body)
        description = description.replace(abstract, abstract[:-overflow].rstrip() + "…", 1)
    return description


def set_front_matter(path: Path, values: dict[str, str]) -> bool:
    """Set single-line keys in the front matter without reformatting anything else.

    Keys are placed in alphabetical order among the existing top-level keys,
    matching how our talk files are generated. Returns True if the file changed.
    """
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} has no front matter")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")

    head = [line for line in lines[1:end] if not any(line.startswith(f"{key}:") for key in values)]
    for key in sorted(values):
        new_line = f"{key}: {values[key]}\n"
        position = len(head)
        for i, line in enumerate(head):
            top_level = re.match(r"^([A-Za-z_][\w-]*):", line)
            if top_level and top_level.group(1) > key:
                position = i
                break
        head.insert(position, new_line)

    updated = "".join([lines[0], *head, *lines[end:]])
    if updated == text:
        return False
    path.write_text(updated)
    return True


@app.command()
def main(
    playlist: Annotated[str | None, typer.Argument(help="YouTube playlist ID or URL")] = None,
    write: Annotated[bool, typer.Option(help="Write video_url/youtube_id into matched talk files")] = False,
    output_dir: Annotated[Path, typer.Option(help="Where to write report.csv and descriptions/")] = ROOT / ".youtube-sync",
    location: Annotated[str, typer.Option(help="Where the conference was held")] = "Chicago, Illinois, USA",
    cache: Annotated[Path | None, typer.Option(help="Cache the playlist JSON here to avoid refetching")] = None,
    update_youtube: Annotated[bool, typer.Option(help="Push suggested titles/descriptions to YouTube (signs in)")] = False,
    update_titles: Annotated[bool, typer.Option(help="With --update-youtube, also replace video titles")] = True,
    only: Annotated[list[str] | None, typer.Option(help="Limit YouTube updates to these video IDs or talk file names (repeatable)")] = None,
    yes: Annotated[bool, typer.Option("--yes", help="Don't ask before updating YouTube")] = False,
    login: Annotated[bool, typer.Option("--login", help="Sign in to YouTube, show the channel, and exit")] = False,
    logout: Annotated[bool, typer.Option("--logout", help="Forget the saved YouTube sign-in and exit")] = False,
    restore: Annotated[Path | None, typer.Option(help="Restore YouTube titles/descriptions from a backup file and exit")] = None,
    client_secrets: Annotated[Path, typer.Option(help="OAuth client secret JSON from Google Cloud")] = CONFIG_DIR / "client_secret.json",
    token: Annotated[Path, typer.Option(help="Where to cache the signed-in OAuth token")] = CONFIG_DIR / "token.json",
) -> None:
    if logout:
        token.unlink(missing_ok=True)
        console.print(f"Removed {token}")
        return
    # Read through the API whenever we're signed in (it can see private
    # playlists); only force a sign-in when we need to write to YouTube.
    signed_in = token.exists()
    youtube = youtube_client(client_secrets, token) if (update_youtube or restore or login or signed_in) else None
    if login:
        show_channels(youtube)
        return
    if restore:
        restore_from_backup(youtube, restore, yes)
        return
    if not playlist:
        raise typer.BadParameter("Missing playlist ID or URL")

    site = json.loads((ROOT / "src" / "_data" / "site.json").read_text())
    talks = load_talks(load_presenters())
    videos = fetch_playlist(playlist, cache, youtube)
    matches, unmatched_videos, unmatched_talks = match_videos(videos, talks)

    confident = [m for m in matches if m.score >= MATCH_SCORE]
    review = [m for m in matches if m.score < MATCH_SCORE]

    descriptions_dir = output_dir / "descriptions"
    descriptions_dir.mkdir(parents=True, exist_ok=True)
    for match in matches:
        slug = match.talk.path.stem
        (descriptions_dir / f"{slug}.txt").write_text(
            f"{youtube_title(match.talk)}\n\n{youtube_description(match.talk, site, location)}\n"
        )

    with open(output_dir / "report.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["status", "score", "reasons", "youtube_id", "youtube_title", "talk_file", "talk_title"])
        for status, group in (("match", confident), ("review", review)):
            for m in group:
                writer.writerow([status, f"{m.score:.0f}", "; ".join(m.reasons), m.video.id, m.video.title,
                                 m.talk.path.relative_to(ROOT), m.talk.title])
        for v in unmatched_videos:
            writer.writerow(["unmatched video", "", "", v.id, v.title, "", ""])
        for t in unmatched_talks:
            writer.writerow(["no video", "", "", "", "", t.path.relative_to(ROOT), t.title])

    table = Table(title=f"{len(videos)} videos, {len(talks)} talks")
    for column in ("", "Score", "YouTube", "Talk file"):
        table.add_column(column)
    for status, group, style in (("✓", confident, "green"), ("?", review, "yellow")):
        for m in group:
            table.add_row(status, f"{m.score:.0f}", m.video.title, m.talk.path.name, style=style)
    console.print(table)

    if review:
        console.print(f"[yellow]{len(review)} low-confidence matches need review (not written).")
    for v in unmatched_videos:
        console.print(f"[red]No talk for video:[/] {v.title} ({v.url})")
    for t in unmatched_talks:
        console.print(f"[dim]No video for talk:[/] {t.path.name}")

    if write:
        changed = 0
        for m in confident:
            changed += set_front_matter(
                m.talk.path,
                {"video_url": m.video.url, "youtube_id": json.dumps(m.video.id)},
            )
        console.print(f"[green]Updated {changed} talk files.")
    else:
        console.print("Re-run with --write to update talk front matter.")

    if update_youtube:
        selected = confident
        if only:
            selected = [m for m in confident if m.video.id in only or m.talk.path.stem in only or m.talk.path.name in only]
        push_to_youtube(youtube, selected, site, location, output_dir, update_titles, yes)
    console.print(f"Report and descriptions: {output_dir}")


if __name__ == "__main__":
    app()
