import datetime
from pathlib import Path

import frontmatter
from slugify import slugify
import typer
import yaml

import constants
import models


app = typer.Typer()
REPO_ROOT = Path(__file__).parent.parent
PRESENTER_PATH = REPO_ROOT / "src" / "_content" / "presenters"
ORGANIZER_PATH = REPO_ROOT / "src" / "_content" / "organizers"


@app.command()
def generate_manual_schedule_data(
    output_path: str = "src/_content/schedule/manual.yaml",
):
    """Take the manual schedule entries and write them to YAML"""
    output_file = constants.REPO_ROOT / output_path
    items = [
        schedule_item.model_dump(exclude_unset=True)
        for schedule_item in models.MANUAL_SCHEDULE_ENTRIES
    ]
    data = yaml.dump(items)
    output_file.write_text(data)


@app.command()
def generate_placeholders():
    """Generate placeholders for keynotes and lightning talks"""
    for schedule_item in [
        # opening remarks
        create_opening_remarks(
            constants.DAY_1_OPENING_REMARKS_START,
            constants.DAY_1_OPENING_REMARKS_END,
            constants.DAY_1_OPENING_REMARKS_ORGANIZER_SLUG,
        ),
        create_opening_remarks(
            constants.DAY_2_OPENING_REMARKS_START,
            constants.DAY_2_OPENING_REMARKS_END,
            constants.DAY_2_OPENING_REMARKS_ORGANIZER_SLUG,
        ),
        create_opening_remarks(
            constants.DAY_3_OPENING_REMARKS_START,
            constants.DAY_3_OPENING_REMARKS_END,
            constants.DAY_3_OPENING_REMARKS_ORGANIZER_SLUG,
        ),
        # orientation
        create_orientation(
            constants.ORIENTATION_START,
            constants.ORIENTATION_END,
            constants.ORIENTATION_ORGANIZER_SLUG,
        ),
        # lightning talks
        create_lightning_talks(
            date=constants.TALK_DAY_1,
            organizer_slug=constants.LIGHTNING_TALKS_ORGANIZER_SLUG,
        ),
        create_lightning_talks(
            date=constants.TALK_DAY_2,
            organizer_slug=constants.LIGHTNING_TALKS_ORGANIZER_SLUG,
        ),
        create_lightning_talks(
            date=constants.TALK_DAY_3,
            organizer_slug=constants.LIGHTNING_TALKS_ORGANIZER_SLUG,
        ),
        # closing remarks
        create_closing_remarks(
            start_time=constants.CLOSING_REMARKS_START,
            end_time=constants.CLOSING_REMARKS_END,
            organizer_slug=constants.CLOSING_REMARKS_ORGANIZER_SLUG,
        ),
        # keynotes
        create_placeholder_keynote(
            start_time=constants.DAY_1_KEYNOTE_START,
            end_time=constants.DAY_1_KEYNOTE_END,
        ),
        create_placeholder_keynote(
            start_time=constants.DAY_2_KEYNOTE_START,
            end_time=constants.DAY_2_KEYNOTE_END,
        ),
        create_placeholder_keynote(
            start_time=constants.DAY_3_KEYNOTE_START,
            end_time=constants.DAY_3_KEYNOTE_END,
        ),
        # panel
        copy_organizer_and_create_schedule(
            start_time=constants.PANEL_START,
            end_time=constants.PANEL_END,
            organizer_slug=constants.PANEL_ORGANIZER_SLUG,
            title="Panel Discussion (details TBA)",
        ),
    ]:
        filename = (
            REPO_ROOT
            / "src"
            / "_content"
            / "schedule"
            / "talks"
            / schedule_item.filename
        )
        post = frontmatter.loads("")
        post.metadata.update(schedule_item.model_dump(exclude_unset=True))
        filename.write_text(frontmatter.dumps(post, indent=4) + "\n")
        print(f"Created {filename}")


def create_opening_remarks(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    organizer_slug: str,
) -> models.Schedule:
    if organizer_slug:
        return copy_organizer_and_create_schedule(
            start_time=start_time,
            end_time=end_time,
            organizer_slug=organizer_slug,
            title=f"Opening Remarks ({start_time.strftime('%A')})",
        )
    return models.Schedule(
        category="talks",
        difficulty="All",
        end_datetime=end_time,
        start_datetime=start_time,
        track="t0",
        title=f"Opening Remarks ({start_time.strftime('%A')})",
        permalink=f'/talks/opening-remarks-{start_time.strftime("%A").lower()}/',
        room=constants.LARGE_TALK_ROOM,
    )


def create_orientation(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    organizer_slug: str,
) -> models.Schedule:
    return copy_organizer_and_create_schedule(
        start_time=start_time,
        end_time=end_time,
        organizer_slug=organizer_slug,
        title="Orientation",
    )


def create_lightning_talks(
    date: datetime.date,
    organizer_slug: str,
) -> models.Schedule:
    start_time = datetime.datetime.combine(
        date,
        constants.LIGHTNING_TALK_START_TIME,
        tzinfo=constants.CONFERENCE_TZ,
    )
    end_time = datetime.datetime.combine(
        date,
        constants.LIGHTNING_TALK_END_TIME,
        tzinfo=constants.CONFERENCE_TZ,
    )
    return copy_organizer_and_create_schedule(
        start_time=start_time,
        end_time=end_time,
        organizer_slug=organizer_slug,
        title=f"Lightning Talks ({start_time.strftime('%A')})",
    )


def create_closing_remarks(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    organizer_slug: str,
) -> models.Schedule:
    return copy_organizer_and_create_schedule(
        start_time=start_time,
        end_time=end_time,
        organizer_slug=organizer_slug,
        title="Closing Remarks",
    )


def create_placeholder_keynote(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
) -> models.Schedule:
    return models.Schedule(
        category="talks",
        difficulty="All",
        end_datetime=end_time,
        presenter_slugs=None,
        start_datetime=start_time,
        track="t0",
        title=f"Keynote (to be announced) ({start_time.strftime('%A')})",
        permalink=f"/talks/keynote-{start_time.strftime('%A').lower()}/",
        room=constants.LARGE_TALK_ROOM,
    )


def copy_organizer_and_create_schedule(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    organizer_slug: str,
    title: str,
) -> models.Schedule:
    if organizer_slug:
        copy_organizer_to_presenter(organizer_slug)
    return models.Schedule(
        category="talks",
        difficulty="All",
        end_datetime=end_time,
        presenter_slugs=[organizer_slug] if organizer_slug else [],
        start_datetime=start_time,
        track="t0",
        title=title,
        permalink=f"/talks/{slugify(title)}/",
        room=constants.LARGE_TALK_ROOM,
    )


def copy_organizer_to_presenter(slug: str) -> None:
    """Copy an organizer's bio and picture into the presenters folder

    This is a placeholder in case they want to edit the presenter bio separately.
    """
    organizer_file = ORGANIZER_PATH / f"{slug}.md"
    presenter_file = PRESENTER_PATH / f"{slug}.md"
    organizer_text = organizer_file.read_text()
    presenter_file.write_text(organizer_text)
    organizer_data = frontmatter.loads(organizer_text)
    if filename := organizer_data.metadata.get("photo"):
        organizer_photo: Path = ORGANIZER_PATH / filename
        organizer_bytes = organizer_photo.read_bytes()
        output_file: Path = PRESENTER_PATH / filename
        output_file.write_bytes(organizer_bytes)


if __name__ == "__main__":
    app()
