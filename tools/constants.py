import datetime
import json
from pathlib import Path
import zoneinfo

REPO_ROOT = Path(__file__).parent.parent
SITE_JSON_FILE = REPO_ROOT / "src" / "_data" / "site.json"
SITE_JSON = json.loads(SITE_JSON_FILE.read_text())
CONFERENCE_TZ = zoneinfo.ZoneInfo(SITE_JSON["timezone"])
CONFERENCE_YEAR = SITE_JSON["conf_year"]

# TUTORIAL_DAY = datetime.date(CONFERENCE_YEAR, 9, 1)
TALK_DAY_1 = datetime.date(CONFERENCE_YEAR, 9, 8)
TALK_DAY_2 = datetime.date(CONFERENCE_YEAR, 9, 9)
TALK_DAY_3 = datetime.date(CONFERENCE_YEAR, 9, 10)
SPRINTS_DAY_1 = datetime.date(CONFERENCE_YEAR, 9, 11)
SPRINTS_DAY_2 = datetime.date(CONFERENCE_YEAR, 9, 12)

LARGE_TALK_ROOM = "Sauganash Ballroom"
SMALL_TALK_ROOM = "Wolf Point Ballroom"
SPRINTS_ROOM = "LaSalle Ballroom"

LUNCH_ROOM = "Sauganash & Wolf Point Ballrooms"
EARLY_LUNCH_ROOM = SMALL_TALK_ROOM

LACTATION_ROOM = "Lake House"
QUIET_ROOM = "Shakespeare House"
GREEN_ROOM = "American House"

# TUTORIAL_TRACK_A_ROOM = "Tutorial Track A (TBD)"
# TUTORIAL_TRACK_B_ROOM = "Tutorial Track B (TBD)"
# TUTORIAL_TRACK_C_ROOM = "Tutorial Track C (TBD)"

# TODO once the childcare post is live: update this with the relative
# link to that post
LACTATION_BLOG_POST_LINK = None

# TODO get organizer pages set up
DAY_1_OPENING_REMARKS_ORGANIZER_SLUG = "keanya-phelps"
DAY_2_OPENING_REMARKS_ORGANIZER_SLUG = None  # "jeanette-obrien"
DAY_3_OPENING_REMARKS_ORGANIZER_SLUG = DAY_1_OPENING_REMARKS_ORGANIZER_SLUG
CLOSING_REMARKS_ORGANIZER_SLUG = DAY_1_OPENING_REMARKS_ORGANIZER_SLUG
PANEL_ORGANIZER_SLUG = "velda-kiara"

LIGHTNING_TALKS_ORGANIZER_SLUG = "andrew-mshar"
LIGHTNING_TALK_START_TIME = datetime.time(12, 10)
LIGHTNING_TALK_END_TIME = datetime.time(13)
LUNCH_END_TIME = datetime.time(13, 45)

ORIENTATION_ORGANIZER_SLUG = "kojo-idrissa"
ORIENTATION_START = datetime.datetime.combine(
    TALK_DAY_1, datetime.time(8, 30), tzinfo=CONFERENCE_TZ
)
ORIENTATION_END = ORIENTATION_START + datetime.timedelta(minutes=30)

DAY_1_OPENING_REMARKS_START = ORIENTATION_END
DAY_1_OPENING_REMARKS_END = DAY_1_OPENING_REMARKS_START + datetime.timedelta(minutes=15)
DAY_1_KEYNOTE_START = DAY_1_OPENING_REMARKS_END
DAY_1_KEYNOTE_END = DAY_1_KEYNOTE_START + datetime.timedelta(minutes=45)

DAY_2_OPENING_REMARKS_START = datetime.datetime.combine(
    TALK_DAY_2, datetime.time(9), tzinfo=CONFERENCE_TZ
)
DAY_2_OPENING_REMARKS_END = DAY_2_OPENING_REMARKS_START + datetime.timedelta(minutes=15)
DAY_2_KEYNOTE_START = DAY_2_OPENING_REMARKS_END
DAY_2_KEYNOTE_END = DAY_2_KEYNOTE_START + datetime.timedelta(minutes=45)

DAY_3_OPENING_REMARKS_START = datetime.datetime.combine(
    TALK_DAY_3, datetime.time(9), tzinfo=CONFERENCE_TZ
)
DAY_3_OPENING_REMARKS_END = DAY_3_OPENING_REMARKS_START + datetime.timedelta(minutes=15)
DAY_3_KEYNOTE_START = DAY_3_OPENING_REMARKS_END
DAY_3_KEYNOTE_END = DAY_3_KEYNOTE_START + datetime.timedelta(minutes=45)

CLOSING_REMARKS_START = datetime.datetime.combine(
    TALK_DAY_3, datetime.time(17, 45), tzinfo=CONFERENCE_TZ
)
CLOSING_REMARKS_END = CLOSING_REMARKS_START + datetime.timedelta(minutes=20)

PANEL_START = datetime.datetime.combine(
    TALK_DAY_3, datetime.time(13, 55), tzinfo=CONFERENCE_TZ
)
PANEL_END = PANEL_START + datetime.timedelta(minutes=45)

# TODO once catering menus are live: update this with the blog post
CATERING_MENU_LINK = None

if CATERING_MENU_LINK:
    SUNDAY_BREAKFAST_LINK = f"{CATERING_MENU_LINK}/#sunday-breakfast"
    MONDAY_BREAKFAST_LINK = f"{CATERING_MENU_LINK}/#monday-breakfast"
    TUESDAY_BREAKFAST_LINK = f"{CATERING_MENU_LINK}/#tuesday-breakfast"
    WEDNESDAY_BREAKFAST_LINK = f"{CATERING_MENU_LINK}/#wednesday-breakfast"
    MONDAY_MORNING_BREAK_LINK = f"{CATERING_MENU_LINK}/#monday-morning-break"
    TUESDAY_MORNING_BREAK_LINK = f"{CATERING_MENU_LINK}/#tuesday-morning-break"
    WEDNESDAY_MORNING_BREAK_LINK = f"{CATERING_MENU_LINK}/#wednesday-morning-break"
    SUNDAY_LUNCH_LINK = f"{CATERING_MENU_LINK}/#sunday-lunch"
    MONDAY_LUNCH_LINK = f"{CATERING_MENU_LINK}/#monday-lunch"
    TUESDAY_LUNCH_LINK = f"{CATERING_MENU_LINK}/#tuesday-lunch"
    WEDNESDAY_LUNCH_LINK = f"{CATERING_MENU_LINK}/#wednesday-lunch"
    MONDAY_AFTERNOON_BREAK_LINK = f"{CATERING_MENU_LINK}/#monday-afternoon-break"
    TUESDAY_AFTERNOON_BREAK_LINK = f"{CATERING_MENU_LINK}/#tuesday-afternoon-break"
    WEDNESDAY_AFTERNOON_BREAK_LINK = f"{CATERING_MENU_LINK}/#wednesday-afternoon-break"
else:
    SUNDAY_BREAKFAST_LINK = None
    MONDAY_BREAKFAST_LINK = None
    TUESDAY_BREAKFAST_LINK = None
    WEDNESDAY_BREAKFAST_LINK = None
    MONDAY_MORNING_BREAK_LINK = None
    TUESDAY_MORNING_BREAK_LINK = None
    WEDNESDAY_MORNING_BREAK_LINK = None
    SUNDAY_LUNCH_LINK = None
    MONDAY_LUNCH_LINK = None
    TUESDAY_LUNCH_LINK = None
    WEDNESDAY_LUNCH_LINK = None
    MONDAY_AFTERNOON_BREAK_LINK = None
    TUESDAY_AFTERNOON_BREAK_LINK = None
    WEDNESDAY_AFTERNOON_BREAK_LINK = None
