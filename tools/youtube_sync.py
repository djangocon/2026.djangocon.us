# /// script
# requires-python = ">=3.12"
# dependencies = [
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
"""

import csv
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Annotated

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


def fetch_playlist(playlist: str, cache: Path | None) -> list[Video]:
    if cache and cache.exists():
        entries = json.loads(cache.read_text())
    else:
        url = playlist if playlist.startswith("http") else f"https://www.youtube.com/playlist?list={playlist}"
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
    playlist: Annotated[str, typer.Argument(help="YouTube playlist ID or URL")],
    write: Annotated[bool, typer.Option(help="Write video_url/youtube_id into matched talk files")] = False,
    output_dir: Annotated[Path, typer.Option(help="Where to write report.csv and descriptions/")] = ROOT / ".youtube-sync",
    location: Annotated[str, typer.Option(help="Where the conference was held")] = "Chicago, Illinois, USA",
    cache: Annotated[Path | None, typer.Option(help="Cache the playlist JSON here to avoid refetching")] = None,
) -> None:
    site = json.loads((ROOT / "src" / "_data" / "site.json").read_text())
    talks = load_talks(load_presenters())
    videos = fetch_playlist(playlist, cache)
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
        console.print("Dry run. Re-run with --write to update talk front matter.")
    console.print(f"Report and descriptions: {output_dir}")


if __name__ == "__main__":
    app()
