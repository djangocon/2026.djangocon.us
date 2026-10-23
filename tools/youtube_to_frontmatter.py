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
YouTube -> front matter: match playlist videos to talk files and record them.

    uv run tools/youtube_to_frontmatter.py PLAYLIST_ID --dry-mode   # report only
    uv run tools/youtube_to_frontmatter.py PLAYLIST_ID              # update front matter

For every video in the playlist we look for the talk it belongs to by:

1. the talk's permalink appearing in the video description (our YouTube
   descriptions include "https://YEAR.djangocon.us/talks/slug/"),
2. title similarity, ignoring the " with Presenter Name" suffix, and
3. presenter names showing up in the video title or description.

Every run writes OUTPUT_DIR/report.csv with each match, low-confidence match,
and leftover video/talk.

Unless --dry-mode is given, matched talks get `video_url` and `youtube_id`
added to (or updated in) their front matter. Only those two lines are touched, so the rest
of the file stays byte-for-byte the same. Low-confidence matches are never
written; fix them by hand or re-run after adjusting the video title.

If you've signed in with --login (see tools/README.md), the playlist is read
through the YouTube Data API, which also works for private playlists.
Otherwise it's read anonymously with yt-dlp.

The other direction (front matter -> YouTube titles/descriptions) is
tools/frontmatter_to_youtube.py.
"""

import csv
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Annotated
from urllib.parse import parse_qs, urlparse

import frontmatter
import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "src" / "_content"
SESSION_DIRS = ("talks", "tutorials")

# A match needs at least this score to be written. Anything between
# REVIEW_SCORE and MATCH_SCORE is reported for a human to check.
MATCH_SCORE = 60
REVIEW_SCORE = 35

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
class Talk:
    path: Path
    title: str
    permalink: str
    presenter_names: list[str]


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


def normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def strip_presenters(yt_title: str) -> str:
    """'My Talk with Jane Doe and Sam Roe' -> 'My Talk'."""
    if " with " in yt_title:
        return yt_title.rsplit(" with ", 1)[0]
    return yt_title


def load_talks() -> list[Talk]:
    names = {
        path.stem: frontmatter.load(path).get("name", path.stem)
        for path in (CONTENT_DIR / "presenters").glob("*.md")
    }
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
                    presenter_names=[names[slug] for slug in post.get("presenter_slugs") or [] if slug in names],
                )
            )
    return talks


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
            raise typer.BadParameter(f"No OAuth client secret at {client_secrets}. See tools/README.md for setup.")
        console.print("Sign in with the account (or brand account) that manages the DjangoCon US channel.")
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
    channels = youtube.channels().list(part="snippet", mine=True).execute().get("items", [])
    if not channels:
        console.print("[red]Signed in, but this account has no YouTube channel. Sign in again and pick the DjangoCon US brand account.")
    for channel in channels:
        console.print(f"[green]Signed in as YouTube channel:[/] {channel['snippet']['title']} ({channel['id']})")


def fetch_playlist_api(youtube, playlist: str) -> list[Video]:
    """Read a playlist through the API, which also works for private playlists."""
    videos, page_token = [], None
    while True:
        response = youtube.playlistItems().list(
            part="snippet", playlistId=playlist_id_from(playlist), maxResults=50, pageToken=page_token
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


def fetch_playlist_ytdlp(playlist: str) -> list[Video]:
    from yt_dlp import YoutubeDL

    url = f"https://www.youtube.com/playlist?list={playlist_id_from(playlist)}"
    options = {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True}
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise typer.BadParameter(
            f"Could not load playlist {playlist!r}. Is the ID complete? Private playlists need --login first."
        )
    return [
        Video(id=e["id"], title=e.get("title") or "", description=e.get("description") or "")
        for e in info.get("entries") or []
        if e
    ]


def fetch_playlist(playlist: str, cache: Path | None, youtube) -> list[Video]:
    if cache and cache.exists():
        return [Video(**entry) for entry in json.loads(cache.read_text())]
    with console.status("Fetching playlist from YouTube..."):
        videos = fetch_playlist_api(youtube, playlist) if youtube else fetch_playlist_ytdlp(playlist)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps([v.__dict__ for v in videos], indent=2))
    return videos


def score(video: Video, talk: Talk) -> tuple[float, list[str]]:
    points = 0.0
    reasons = []

    if talk.permalink.rstrip("/") + "/" in video.description:
        points += 100
        reasons.append("permalink")

    similarity = SequenceMatcher(None, normalize(strip_presenters(video.title)), normalize(talk.title)).ratio()
    points += similarity * 60
    reasons.append(f"title {similarity:.0%}")

    haystack = normalize(f"{video.title} {video.description}")
    found = [name for name in talk.presenter_names if normalize(name) and normalize(name) in haystack]
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
        position = len(head)
        for i, line in enumerate(head):
            top_level = re.match(r"^([A-Za-z_][\w-]*):", line)
            if top_level and top_level.group(1) > key:
                position = i
                break
        head.insert(position, f"{key}: {values[key]}\n")

    updated = "".join([lines[0], *head, *lines[end:]])
    if updated == text:
        return False
    path.write_text(updated)
    return True


@app.command()
def main(
    playlist: Annotated[str | None, typer.Argument(help="YouTube playlist ID or URL")] = None,
    dry_mode: Annotated[bool, typer.Option("--dry-mode", "--dry-run", help="Report matches without changing any talk files")] = False,
    output_dir: Annotated[Path, typer.Option(help="Where to write report.csv")] = ROOT / ".youtube-sync",
    cache: Annotated[Path | None, typer.Option(help="Cache the playlist JSON here to avoid refetching")] = None,
    login: Annotated[bool, typer.Option("--login", help="Sign in to YouTube, show the channel, and exit")] = False,
    logout: Annotated[bool, typer.Option("--logout", help="Forget the saved YouTube sign-in and exit")] = False,
    client_secrets: Annotated[Path, typer.Option(help="OAuth client secret JSON from Google Cloud")] = CONFIG_DIR / "client_secret.json",
    token: Annotated[Path, typer.Option(help="Where to cache the signed-in OAuth token")] = CONFIG_DIR / "token.json",
) -> None:
    if logout:
        token.unlink(missing_ok=True)
        console.print(f"Removed {token}")
        return
    # Use the API whenever we're signed in, since it can see private playlists.
    youtube = youtube_client(client_secrets, token) if (login or token.exists()) else None
    if login:
        show_channels(youtube)
        return
    if not playlist:
        raise typer.BadParameter("Missing playlist ID or URL")

    talks = load_talks()
    videos = fetch_playlist(playlist, cache, youtube)
    matches, unmatched_videos, unmatched_talks = match_videos(videos, talks)
    confident = [m for m in matches if m.score >= MATCH_SCORE]
    review = [m for m in matches if m.score < MATCH_SCORE]

    output_dir.mkdir(parents=True, exist_ok=True)
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

    if not dry_mode:
        changed = sum(
            set_front_matter(m.talk.path, {"video_url": m.video.url, "youtube_id": json.dumps(m.video.id)})
            for m in confident
        )
        console.print(f"[green]Updated {changed} talk files.")
    else:
        console.print("Dry mode: no talk files changed. Re-run without --dry-mode to write them.")
    console.print(f"Report: {output_dir / 'report.csv'}")


if __name__ == "__main__":
    app()
