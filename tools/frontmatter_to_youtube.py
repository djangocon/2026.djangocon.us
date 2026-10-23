# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "google-api-python-client",
#     "google-auth-oauthlib",
#     "python-frontmatter",
#     "rich",
#     "typer",
# ]
# ///
"""
Front matter -> YouTube: push talk titles and descriptions to their videos.

    uv run tools/frontmatter_to_youtube.py --dry-mode       # show what would change
    uv run tools/frontmatter_to_youtube.py --only TALK      # update one video
    uv run tools/frontmatter_to_youtube.py                  # update every talk with a youtube_id

Every talk whose front matter has a `youtube_id` (or a `video_url`) gets the
YouTube title and description from our template page, /speaking/youtube/
(src/youtube-talks.html + src/_includes/youtube-copy-and-paste.html): presenter
details and social links, then the DjangoCon US and DEFNA links. The page is the
single source of truth, so edit the template there, not here. By default we read
the live page on site.domain; pass --template dist/speaking/youtube/index.html
to use a local build instead. Run tools/youtube_to_frontmatter.py first to fill
in the IDs.

This always signs in to the YouTube Data API as a channel manager (see
tools/README.md for the one-time OAuth setup), so it can compare against what's
on YouTube now. Every run writes previews to OUTPUT_DIR/descriptions/ and lists
the videos that would change; --dry-mode stops there. Otherwise you get a
prompt, and the current title/description of every video about to change is
saved to OUTPUT_DIR/backups/ first, so --restore BACKUP_FILE can put them back.
"""

import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated

import frontmatter
import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "src" / "_content"
SESSION_DIRS = ("talks", "tutorials")

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
class Talk:
    path: Path
    youtube_id: str
    permalink: str


@dataclass
class TemplateEntry:
    title: str
    description: str


def youtube_id_from(post) -> str | None:
    if post.get("youtube_id"):
        return str(post["youtube_id"])
    match = re.search(r"(?:youtu\.be/|[?&]v=)([\w-]{11})", str(post.get("video_url") or ""))
    return match.group(1) if match else None


def load_talks() -> list[Talk]:
    talks = []
    for directory in SESSION_DIRS:
        for path in sorted((CONTENT_DIR / "schedule" / directory).glob("*.md")):
            post = frontmatter.load(path)
            youtube_id = youtube_id_from(post)
            if post.get("hidden") or not youtube_id:
                continue
            talks.append(Talk(path=path, youtube_id=youtube_id, permalink=post["permalink"]))
    return talks


def youtube_safe(text: str) -> str:
    return text.replace("<", "").replace(">", "")  # YouTube rejects angle brackets


def load_template(template: str) -> dict[str, TemplateEntry]:
    """Parse the /speaking/youtube/ page into {permalink: TemplateEntry}.

    Each talk on that page has a title span (id="copy-SLUG-title") and a
    textarea (id="copy-SLUG") holding the description. We key entries by the
    talk URL inside the description, so we never have to re-create the
    template's slugify rules.
    """
    if template.startswith("http"):
        with urllib.request.urlopen(template) as response:
            page = response.read().decode()
    else:
        page = Path(template).read_text()

    titles = {
        slug: " ".join(html.unescape(re.sub(r"<[^>]+>", "", raw)).split())
        for slug, raw in re.findall(r'<span id="copy-([^"]+)-title">(.*?)</span>', page, re.S)
    }
    entries = {}
    for slug, raw in re.findall(r'<textarea[^>]*id="copy-([^"]+)"[^>]*>(.*?)</textarea>', page, re.S):
        description = youtube_safe(html.unescape(raw).strip())
        url = re.search(r"https?://[^\s]+/talks/[^\s]+/", description)
        if not url or slug not in titles:
            continue
        title = youtube_safe(titles[slug])
        if len(title) > YOUTUBE_TITLE_LIMIT:
            title = title[: YOUTUBE_TITLE_LIMIT - 1] + "…"
        entries[urllib.parse.urlparse(url.group(0)).path] = TemplateEntry(title, description[:YOUTUBE_DESCRIPTION_LIMIT])
    return entries


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


def restore_from_backup(youtube, backup: Path, assume_yes: bool) -> None:
    saved = json.loads(backup.read_text())
    if not assume_yes and not typer.confirm(f"Restore {len(saved)} videos on YouTube from {backup}?"):
        raise typer.Abort()
    current = current_snippets(youtube, list(saved))
    for video_id, snippet in saved.items():
        update_snippet(youtube, video_id, current.get(video_id, snippet), snippet["title"], snippet.get("description", ""))
    console.print(f"[green]Restored {len(saved)} videos.")


@app.command()
def main(
    dry_mode: Annotated[bool, typer.Option("--dry-mode", "--dry-run", help="Show what would change without updating YouTube")] = False,
    only: Annotated[list[str] | None, typer.Option(help="Limit to these video IDs or talk file names (repeatable)")] = None,
    update_titles: Annotated[bool, typer.Option(help="Also replace video titles")] = True,
    template: Annotated[str | None, typer.Option(help="URL or local file of the /speaking/youtube/ page (default: live site)")] = None,
    yes: Annotated[bool, typer.Option("--yes", help="Don't ask before updating YouTube")] = False,
    output_dir: Annotated[Path, typer.Option(help="Where to write descriptions/ and backups/")] = ROOT / ".youtube-sync",
    restore: Annotated[Path | None, typer.Option(help="Restore YouTube titles/descriptions from a backup file and exit")] = None,
    login: Annotated[bool, typer.Option("--login", help="Sign in to YouTube, show the channel, and exit")] = False,
    logout: Annotated[bool, typer.Option("--logout", help="Forget the saved YouTube sign-in and exit")] = False,
    client_secrets: Annotated[Path, typer.Option(help="OAuth client secret JSON from Google Cloud")] = CONFIG_DIR / "client_secret.json",
    token: Annotated[Path, typer.Option(help="Where to cache the signed-in OAuth token")] = CONFIG_DIR / "token.json",
) -> None:
    if logout:
        token.unlink(missing_ok=True)
        console.print(f"Removed {token}")
        return
    youtube = youtube_client(client_secrets, token)
    show_channels(youtube)
    if login:
        return
    if restore:
        restore_from_backup(youtube, restore, yes)
        return

    site = json.loads((ROOT / "src" / "_data" / "site.json").read_text())
    template = template or f"{site['domain']}/speaking/youtube/"
    entries = load_template(template)
    console.print(f"Template: {template} ({len(entries)} talks)")
    talks = load_talks()
    if only:
        talks = [t for t in talks if t.youtube_id in only or t.path.stem in only or t.path.name in only]
    if not talks:
        console.print("No talks with a youtube_id. Run tools/youtube_to_frontmatter.py first.")
        return

    descriptions_dir = output_dir / "descriptions"
    descriptions_dir.mkdir(parents=True, exist_ok=True)
    snippets = current_snippets(youtube, [t.youtube_id for t in talks])

    changes = []
    for talk in talks:
        entry = entries.get(talk.permalink)
        if entry is None:
            console.print(f"[red]{talk.path.name} isn't on the template page ({talk.permalink}); skipping.")
            continue
        description = entry.description
        (descriptions_dir / f"{talk.path.stem}.txt").write_text(f"{entry.title}\n\n{description}\n")
        snippet = snippets.get(talk.youtube_id)
        if snippet is None:
            console.print(f"[red]Can't see video {talk.youtube_id} ({talk.path.name}); is this account a manager of the channel?")
            continue
        title = entry.title if update_titles else snippet["title"]
        if title != snippet["title"] or description != snippet.get("description", ""):
            changes.append((talk, snippet, title, description))

    console.print(f"Previews: {descriptions_dir}")
    if not changes:
        console.print(f"[green]All {len(talks)} videos are already up to date.")
        return

    table = Table(title=f"{len(changes)} of {len(talks)} videos would change")
    for column in ("Talk", "Title", "Description"):
        table.add_column(column)
    for talk, snippet, title, description in changes:
        table.add_row(
            talk.path.name,
            "unchanged" if title == snippet["title"] else f"[dim]{snippet['title']}[/]\n→ {title}",
            "unchanged" if description == snippet.get("description", "") else f"{len(description)} chars",
        )
    console.print(table)

    if dry_mode:
        console.print("Dry mode: nothing changed on YouTube. Re-run without --dry-mode to update (try --only TALK first).")
        return

    backups_dir = output_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    backup = backups_dir / f"youtube-{datetime.now():%Y%m%d-%H%M%S}.json"
    backup.write_text(json.dumps({talk.youtube_id: snippet for talk, snippet, _, _ in changes}, indent=2))
    console.print(f"Current titles and descriptions backed up to {backup}")

    if not yes and not typer.confirm(f"Update {len(changes)} videos on YouTube?"):
        raise typer.Abort()

    from googleapiclient.errors import HttpError

    updated = 0
    for talk, snippet, title, description in changes:
        try:
            update_snippet(youtube, talk.youtube_id, snippet, title, description)
            updated += 1
        except HttpError as error:
            console.print(f"[red]Failed to update {talk.youtube_id} ({talk.path.name}): {error}")
    console.print(f"[green]Updated {updated} of {len(changes)} videos on YouTube.")


if __name__ == "__main__":
    app()
