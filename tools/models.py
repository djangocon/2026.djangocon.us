import datetime as pydatetime  # rename is needed because of yaml conflict
from typing import Literal

from pydantic import BaseModel
from slugify import slugify

import constants


class FrontmatterModel(BaseModel):
    """
    Our base class for our default "Frontmatter" fields.
    """

    permalink: str | None = None
    redirect_from: list[str] | None = None
    redirect_to: str | None = None  # via the jekyll-redirect-from plugin
    title: str | None = None


class Social(BaseModel):
    github: str | None = None
    website: str | None = None
    mastodon: str | None = None
    twitter: str | None = None
    bluesky: str | None = None
    instagram: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.mastodon and self.mastodon.startswith("@"):
            self.mastodon = migrate_mastodon_handle(handle=self.mastodon)
            print(f"🚜 converting {self.mastodon=}")


class Organizer(FrontmatterModel):
    hidden: bool = False
    name: str
    photo: str | None = None
    slug: str | None = None
    title: str | None = None
    social: Social | None = None


class Page(FrontmatterModel):
    description: str | None = None
    heading: str | None = None
    hero_text_align: str | None = None  # homepage related
    hero_theme: str | None = None  # homepage related
    testimonial_img: str | None = None  # homepage related
    testimonial_img_mobile: str | None = None  # homepage related
    title: str | None = None


class Post(FrontmatterModel):
    author: str | None = None
    category: str | None = "General"  # TODO: build a list of these
    categories: list[str] | None = None
    date: pydatetime.datetime  # YYYY-MM-DD HH:MM:SS +/-TTTT
    image: str | None = None
    slug: str | None = None
    tags: list[str] | None = []


class Presenter(FrontmatterModel):
    company: str | None = None
    hidden: bool = False
    name: str
    override_schedule_title: str | None = None
    pronouns: str | None = None
    photo: str | None = None
    role: str | None = None
    social: Social | None = None

    def __init__(self, **data):
        super().__init__(**data)

        # if permalink is blank, let's build a new one
        if not self.permalink:
            self.permalink = f"/presenters/{slugify(self.name)}/"


class Schedule(FrontmatterModel):
    category: Literal[
        "break",
        "lunch",
        "rooms",
        "social-event",
        "sprints",
        "talks",
        "tutorials",
    ]
    difficulty: str | None = "All"
    end_datetime: pydatetime.datetime | None = None

    image: str | None = None
    presenter_slugs: list[str] | None = None
    room: str | None = None
    show_video_urls: bool | None = None
    slides_url: str | None = None
    start_datetime: pydatetime.datetime | None
    tags: list[str] | None = None
    track: str | None = None
    video_url: str | None = None

    def __init__(self, **data):
        super().__init__(**data)

    @property
    def filename(self) -> str:
        return (
            "-".join(
                [
                    self.start_datetime.strftime("%Y-%m-%d-%H-%M"),
                    self.track,
                    slugify(self.title),
                ]
            )
            + ".md"
        )


class ManualScheduleEntry(BaseModel):
    start_datetime: pydatetime.datetime
    end_datetime: pydatetime.datetime
    permalink: str | None
    room: str
    title: str
    track: str

    @property
    def filename(self) -> str:
        return (
            "-".join(
                [
                    self.start_datetime.strftime("%Y-%m-%d-%H-%M"),
                    "t0",
                    slugify(self.title),
                ]
            )
            + ".md"
        )


def migrate_mastodon_handle(*, handle: str) -> str:
    if not handle.startswith("@"):
        return handle

    username, domain = handle[1:].split("@")
    return f"https://{domain}/@{username}"


MANUAL_SCHEDULE_ENTRIES = [
    # Sunday breakfast
    # ManualScheduleEntry(
    #     start_datetime=pydatetime.datetime.combine(
    #         constants.TUTORIAL_DAY,
    #         pydatetime.time(8),
    #         tzinfo=constants.CONFERENCE_TZ,
    #     ),
    #     end_datetime=pydatetime.datetime.combine(
    #         constants.TUTORIAL_DAY,
    #         pydatetime.time(9),
    #         tzinfo=constants.CONFERENCE_TZ,
    #     ),
    #     group="lunch",
    #     permalink=constants.SUNDAY_BREAKFAST_LINK,
    #     room=constants.LUNCH_ROOM,
    #     title="Continental Breakfast",
    #     track="t0",
    # ),
    # # TODO decide whether we'll have quiet/lactation rooms on tutorial day
    # ManualScheduleEntry(
    #     start_datetime=pydatetime.datetime.combine(
    #         constants.TUTORIAL_DAY,
    #         pydatetime.time(8),
    #         tzinfo=constants.CONFERENCE_TZ,
    #     ),
    #     end_datetime=pydatetime.datetime.combine(
    #         constants.TUTORIAL_DAY,
    #         pydatetime.time(18),
    #         tzinfo=constants.CONFERENCE_TZ,
    #     ),
    #     group="break",
    #     permalink=None,
    #     room=f"In front of {constants.LARGE_TALK_ROOM}",
    #     title="Registration",
    #     track="t0",
    # ),
    # # sunday lunch
    # ManualScheduleEntry(
    #     start_datetime=pydatetime.datetime.combine(
    #         constants.TUTORIAL_DAY,
    #         pydatetime.time(12, 30),
    #         tzinfo=constants.CONFERENCE_TZ,
    #     ),
    #     end_datetime=pydatetime.datetime.combine(
    #         constants.TUTORIAL_DAY,
    #         pydatetime.time(13, 30),
    #         tzinfo=constants.CONFERENCE_TZ,
    #     ),
    #     group="lunch",
    #     permalink=constants.SUNDAY_LUNCH_LINK,
    #     room=constants.LUNCH_ROOM,
    #     title="Lunch",
    #     track="t0",
    # ),
    # Monday!
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(7, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(8, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.MONDAY_BREAKFAST_LINK,
        room=constants.LUNCH_ROOM,
        title="Continental Breakfast",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(7, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=f"In front of {constants.LARGE_TALK_ROOM}",
        title="Registration",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.LACTATION_BLOG_POST_LINK,
        room=constants.LACTATION_ROOM,
        title="Private Wellness Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=constants.QUIET_ROOM,
        title="Quiet Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=constants.GREEN_ROOM,
        title="Speaker Green Room",
        track="t0",
    ),
    # monday AM break
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(10, 20),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(10, 45),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.MONDAY_MORNING_BREAK_LINK,
        room=constants.LUNCH_ROOM,
        title="Break",
        track="t0",
    ),
    # monday early lunch
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            constants.LIGHTNING_TALK_START_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            constants.LIGHTNING_TALK_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.MONDAY_LUNCH_LINK,
        room=constants.EARLY_LUNCH_ROOM,
        title="Early Lunch",
        track="t0",
    ),
    # monday main lunch
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            constants.LIGHTNING_TALK_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            # NOTE this must match the length of the online talk
            constants.LUNCH_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.MONDAY_LUNCH_LINK,
        room=constants.LUNCH_ROOM,
        title="Lunch",
        track="t0",
    ),
    # monday PM break
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(15, 10),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(15, 35),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.MONDAY_AFTERNOON_BREAK_LINK,
        room=constants.LUNCH_ROOM,
        title="Break",
        track="t0",
    ),
    # board game night
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(19),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_1,
            pydatetime.time(22),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,  # TODO add social link here
        room=constants.LARGE_TALK_ROOM,
        title="Board Game Night",
        track="t0",
    ),
    # Tuesday!
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(9),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.TUESDAY_BREAKFAST_LINK,
        room=constants.LUNCH_ROOM,
        title="Continental Breakfast",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(17),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=f"In front of {constants.LARGE_TALK_ROOM}",
        title="Registration",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.LACTATION_BLOG_POST_LINK,
        room=constants.LACTATION_ROOM,
        title="Private Wellness Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=constants.QUIET_ROOM,
        title="Quiet Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=constants.GREEN_ROOM,
        title="Speaker Green Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(10, 20),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(10, 45),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.TUESDAY_MORNING_BREAK_LINK,
        room=constants.LUNCH_ROOM,
        title="Break",
        track="t0",
    ),
    # tuesday early lunch
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            constants.LIGHTNING_TALK_START_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            constants.LIGHTNING_TALK_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.TUESDAY_LUNCH_LINK,
        room=constants.EARLY_LUNCH_ROOM,
        title="Early Lunch",
        track="t0",
    ),
    # tuesday main lunch
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            constants.LIGHTNING_TALK_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            # NOTE this must match the length of the online talk
            constants.LUNCH_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.TUESDAY_LUNCH_LINK,
        room=constants.LUNCH_ROOM,
        title="Lunch",
        track="t0",
    ),
    # tuesday PM break
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(15, 10),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_2,
            pydatetime.time(15, 35),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.TUESDAY_AFTERNOON_BREAK_LINK,
        room=constants.LUNCH_ROOM,
        title="Break",
        track="t0",
    ),
    # Wednesday!
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(9),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.WEDNESDAY_BREAKFAST_LINK,
        room=constants.LUNCH_ROOM,
        title="Continental Breakfast",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(17),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=f"In front of {constants.LARGE_TALK_ROOM}",
        title="Registration",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.LACTATION_BLOG_POST_LINK,
        room=constants.LACTATION_ROOM,
        title="Private Wellness Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=constants.QUIET_ROOM,
        title="Quiet Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(8),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(17, 30),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=None,
        room=constants.GREEN_ROOM,
        title="Speaker Green Room",
        track="t0",
    ),
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(10, 20),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(10, 45),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.WEDNESDAY_MORNING_BREAK_LINK,
        room=constants.LUNCH_ROOM,
        title="Break",
        track="t0",
    ),
    # wed early lunch
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            constants.LIGHTNING_TALK_START_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            constants.LIGHTNING_TALK_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.WEDNESDAY_LUNCH_LINK,
        room=constants.EARLY_LUNCH_ROOM,
        title="Early Lunch",
        track="t0",
    ),
    # wed main lunch
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            constants.LIGHTNING_TALK_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            # NOTE this must match the length of the online talk
            constants.LUNCH_END_TIME,
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="lunch",
        permalink=constants.WEDNESDAY_LUNCH_LINK,
        room=constants.LUNCH_ROOM,
        title="Lunch",
        track="t0",
    ),
    # wed PM break
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(15, 45),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.TALK_DAY_3,
            pydatetime.time(16, 15),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="break",
        permalink=constants.WEDNESDAY_AFTERNOON_BREAK_LINK,
        room=constants.LUNCH_ROOM,
        title="Break",
        track="t0",
    ),
    # Thursday!
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.SPRINTS_DAY_1,
            pydatetime.time(9),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.SPRINTS_DAY_1,
            pydatetime.time(17),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="talks",
        permalink=None,
        room=constants.SPRINTS_ROOM,
        title="Contribution Sprints",
        track="t0",
    ),
    # Friday!
    ManualScheduleEntry(
        start_datetime=pydatetime.datetime.combine(
            constants.SPRINTS_DAY_2,
            pydatetime.time(9),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        end_datetime=pydatetime.datetime.combine(
            constants.SPRINTS_DAY_2,
            pydatetime.time(17),
            tzinfo=constants.CONFERENCE_TZ,
        ),
        group="talks",
        permalink=None,
        room=constants.SPRINTS_ROOM,
        title="Contribution Sprints",
        track="t0",
    ),
]
