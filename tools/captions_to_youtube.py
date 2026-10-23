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
Captions -> YouTube: upload caption files to their videos.

    uv run tools/captions_to_youtube.py "captions.zip" --dry-mode     # show the plan
    uv run tools/captions_to_youtube.py "captions.zip" --only VIDEO   # upload one
    uv run tools/captions_to_youtube.py "captions.zip"                # upload the rest

Takes a .zip (or a folder) of caption files named after their YouTube video
ID, e.g. `z_cHhxzRozI.txt`. macOS `__MACOSX/` and dot files are ignored.

- `.txt` files are plain transcripts without timestamps. They're uploaded with
  sync=true so YouTube lines them up with the audio itself.
- `.srt`, `.vtt`, `.sbv`, and `.scc` files already have timing and are uploaded
  as-is.

For each video we look at its existing caption tracks first. If it already
has one of ours (not the auto-generated track) in the same language (en and
en-US count as the same), it's skipped, unless --replace is given or that track failed to process. So
re-running after a partial run only uploads what's missing.

YouTube API quota: listing a video's tracks costs 50 units, uploading costs
400, replacing 450, out of a default 10,000 per day. That's roughly 20 uploads
a day. If the quota runs out mid-run, the script stops; run it again tomorrow
and it picks up where it left off.

Every upload is logged to OUTPUT_DIR/captions-TIMESTAMP.json, and
--undo LOG_FILE deletes the tracks that run created.

This signs in to the YouTube Data API as a channel manager; see
tools/README.md for the one-time OAuth setup.
"""

import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Annotated

import frontmatter
import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "src" / "_content"
SESSION_DIRS = ("talks", "tutorials")

VIDEO_ID = re.compile(r"^[\w-]{11}$")
TIMED_FORMATS = {".srt", ".vtt", ".sbv", ".scc"}
CAPTION_FORMATS = TIMED_FORMATS | {".txt"}

QUOTA_LIST, QUOTA_INSERT, QUOTA_UPDATE = 50, 400, 450

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
class Caption:
    video_id: str
    filename: str
    data: bytes

    @property
    def timed(self) -> bool:
        return PurePosixPath(self.filename).suffix.lower() in TIMED_FORMATS


@dataclass
class Plan:
    caption: Caption
    action: str  # "upload", "replace", or "skip"
    reason: str = ""
    track_id: str | None = None


def read_captions(source: Path) -> list[Caption]:
    """Caption files from a zip or folder, keyed by the video ID in the file name."""
    if source.is_dir():
        files = [(str(p.relative_to(source)), p.read_bytes()) for p in source.rglob("*") if p.is_file()]
    else:
        with zipfile.ZipFile(source) as archive:
            files = [(info.filename, archive.read(info)) for info in archive.infolist() if not info.is_dir()]

    captions = []
    for name, data in files:
        path = PurePosixPath(name)
        if "__MACOSX" in path.parts or path.name.startswith("."):
            continue
        if path.suffix.lower() not in CAPTION_FORMATS:
            console.print(f"[dim]Skipping {name}: not a caption file.")
            continue
        if not VIDEO_ID.match(path.stem):
            console.print(f"[yellow]Skipping {name}: the file name isn't a YouTube video ID.")
            continue
        captions.append(Caption(video_id=path.stem, filename=name, data=data))
    return sorted(captions, key=lambda c: c.filename)


def talk_files_by_video() -> dict[str, str]:
    """youtube_id -> talk file name, just to make the output readable."""
    talks = {}
    for directory in SESSION_DIRS:
        for path in (CONTENT_DIR / "schedule" / directory).glob("*.md"):
            youtube_id = frontmatter.load(path).get("youtube_id")
            if youtube_id:
                talks[str(youtube_id)] = path.stem
    return talks


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


def is_quota_error(error) -> bool:
    return getattr(error, "resp", None) is not None and error.resp.status == 403 and "quota" in str(error).lower()


def primary_language(tag: str) -> str:
    return tag.split("-")[0].lower()


def plan_uploads(youtube, captions: list[Caption], language: str, replace: bool) -> list[Plan]:
    from googleapiclient.errors import HttpError

    plans = []
    with console.status("Checking existing caption tracks...") as status:
        for i, caption in enumerate(captions, 1):
            status.update(f"Checking existing caption tracks ({i}/{len(captions)})...")
            try:
                tracks = youtube.captions().list(part="snippet", videoId=caption.video_id).execute().get("items", [])
            except HttpError as error:
                if is_quota_error(error):
                    raise
                plans.append(Plan(caption, "skip", f"can't read video ({error.resp.status}); is it on this channel?"))
                continue
            # Compare primary language only: Studio uploads are often tagged
            # "en-US" while we upload "en", and both count as the same track.
            ours = [
                t for t in tracks
                if t["snippet"].get("trackKind", "").lower() != "asr"
                and primary_language(t["snippet"].get("language", "")) == primary_language(language)
            ]
            if not ours:
                plans.append(Plan(caption, "upload"))
            elif ours[0]["snippet"].get("status") == "failed":
                plans.append(Plan(caption, "replace", "existing track failed to process", ours[0]["id"]))
            elif replace:
                plans.append(Plan(caption, "replace", "--replace", ours[0]["id"]))
            else:
                plans.append(Plan(caption, "skip", f"already has a '{language}' track"))
    return plans


def upload(youtube, plan: Plan, language: str, name: str, draft: bool) -> dict:
    from googleapiclient.http import MediaInMemoryUpload

    media = MediaInMemoryUpload(plan.caption.data, mimetype="application/octet-stream", resumable=False)
    sync = not plan.caption.timed
    if plan.action == "replace":
        body = {"id": plan.track_id, "snippet": {"isDraft": draft}}
        return youtube.captions().update(part="snippet", body=body, media_body=media, sync=sync).execute()
    body = {"snippet": {"videoId": plan.caption.video_id, "language": language, "name": name, "isDraft": draft}}
    return youtube.captions().insert(part="snippet", body=body, media_body=media, sync=sync).execute()


@app.command()
def main(
    source: Annotated[Path | None, typer.Argument(help="Zip file or folder of <video_id>.txt/.srt/.vtt caption files")] = None,
    dry_mode: Annotated[bool, typer.Option("--dry-mode", "--dry-run", help="Show what would be uploaded without uploading")] = False,
    only: Annotated[list[str] | None, typer.Option(help="Limit to these video IDs or talk file names (repeatable)")] = None,
    replace: Annotated[bool, typer.Option("--replace", help="Replace our existing caption track instead of skipping it")] = False,
    language: Annotated[str, typer.Option(help="Caption language (BCP-47)")] = "en",
    name: Annotated[str, typer.Option(help="Caption track name shown in the YouTube player")] = "English",
    draft: Annotated[bool, typer.Option("--draft", help="Upload as unpublished drafts")] = False,
    yes: Annotated[bool, typer.Option("--yes", help="Don't ask before uploading")] = False,
    output_dir: Annotated[Path, typer.Option(help="Where to write upload logs")] = ROOT / ".youtube-sync",
    undo: Annotated[Path | None, typer.Option(help="Delete the caption tracks created by a logged run and exit")] = None,
    login: Annotated[bool, typer.Option("--login", help="Sign in to YouTube, show the channel, and exit")] = False,
    logout: Annotated[bool, typer.Option("--logout", help="Forget the saved YouTube sign-in and exit")] = False,
    client_secrets: Annotated[Path, typer.Option(help="OAuth client secret JSON from Google Cloud")] = CONFIG_DIR / "client_secret.json",
    token: Annotated[Path, typer.Option(help="Where to cache the signed-in OAuth token")] = CONFIG_DIR / "token.json",
) -> None:
    from googleapiclient.errors import HttpError

    if logout:
        token.unlink(missing_ok=True)
        console.print(f"Removed {token}")
        return
    youtube = youtube_client(client_secrets, token)
    show_channels(youtube)
    if login:
        return

    if undo:
        created = [entry for entry in json.loads(undo.read_text()) if entry["action"] == "upload"]
        if not created:
            console.print("Nothing to undo: that run didn't create any new tracks.")
            return
        if not yes and not typer.confirm(f"Delete {len(created)} caption tracks created by {undo}?"):
            raise typer.Abort()
        for entry in created:
            youtube.captions().delete(id=entry["caption_id"]).execute()
            console.print(f"Deleted caption {entry['caption_id']} on {entry['video_id']}")
        return

    if not source:
        raise typer.BadParameter("Missing zip file or folder of captions")
    captions = read_captions(source)
    talks = talk_files_by_video()
    if only:
        captions = [c for c in captions if c.video_id in only or talks.get(c.video_id) in only]
    if not captions:
        console.print("No caption files to upload.")
        return
    console.print(f"{len(captions)} caption files in {source}")

    try:
        plans = plan_uploads(youtube, captions, language, replace)
    except HttpError as error:
        if is_quota_error(error):
            console.print("[red]YouTube API quota is used up for today. Try again after it resets (midnight Pacific).")
            raise typer.Exit(1)
        raise

    table = Table(title="Caption plan")
    for column in ("Video", "Talk", "File", "Action"):
        table.add_column(column)
    styles = {"upload": "green", "replace": "yellow", "skip": "dim"}
    for plan in plans:
        kind = "timed" if plan.caption.timed else "transcript, auto-sync"
        action = plan.action + (f" ({plan.reason})" if plan.reason else "")
        table.add_row(plan.caption.video_id, talks.get(plan.caption.video_id, "?"),
                      f"{PurePosixPath(plan.caption.filename).name} [{kind}]", action, style=styles[plan.action])
    console.print(table)

    todo = [p for p in plans if p.action != "skip"]
    cost = sum(QUOTA_UPDATE if p.action == "replace" else QUOTA_INSERT for p in todo)
    console.print(
        f"{len(todo)} to upload, {len(plans) - len(todo)} skipped. "
        f"Quota: about {cost} units for the uploads (checking used {len(captions) * QUOTA_LIST}); the daily limit is 10,000."
    )
    if not todo:
        return
    if dry_mode:
        console.print("Dry mode: nothing uploaded. Re-run without --dry-mode to upload (try --only VIDEO first).")
        return
    if not yes and not typer.confirm(f"Upload {len(todo)} caption tracks to YouTube{' as drafts' if draft else ''}?"):
        raise typer.Abort()

    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"captions-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
    log = []
    for plan in todo:
        try:
            result = upload(youtube, plan, language, name, draft)
        except HttpError as error:
            if is_quota_error(error):
                console.print(f"[red]Quota used up after {len(log)} uploads. Run the same command again tomorrow; finished videos are skipped.")
                break
            console.print(f"[red]Failed {plan.caption.video_id} ({plan.caption.filename}): {error}")
            continue
        log.append({"video_id": plan.caption.video_id, "caption_id": result["id"], "action": plan.action,
                    "file": plan.caption.filename})
        log_path.write_text(json.dumps(log, indent=2))
        verb = "Replaced" if plan.action == "replace" else "Uploaded"
        console.print(f"[green]{verb}[/] {plan.caption.video_id} ({talks.get(plan.caption.video_id, plan.caption.filename)})")

    if log:
        console.print(f"Done: {len(log)} of {len(todo)}. Log: {log_path} (undo with --undo {log_path})")
        console.print("YouTube syncs transcripts in the background; tracks can take a few minutes to show up.")


if __name__ == "__main__":
    app()
