# Python tools for 2025 schedule generation

## Getting started

1. Download and install Python 3.13 (or newer)
2. `cd /path/to/repo/root/`
3. `python3.12 -m venv .venv`
4. `pip install --upgrade pip setuptools wheel pip-tools`
5. `pip install -r tools/requirements.txt`

### If you're going to be taking screenshots of pages
1. `playwright install-deps`
2. `playwright install`

## Update dependencies

1. `cd /path/to/repo/root`
2. `source .venv/bin/activate`
3. `pip-compile tools/requirements.in`
4. `git add requirements.txt`
5. Commit and push your changes

## Import the schedule from Pretalx

1. Create your schedule in pretalx. This requires marking accepted talks as confirmed
2. Release the schedule in pretalx.
3. Export both the speakers (only with confirmed talks is fine) and sessions (only confirmed ones) as JSON, using all available fields.
4. Clone the [pretalx-api-export](https://github.com/djangocon/pretalx-api-import) repo and move over to that directory
5. Using Python 3.12 or newer, create a virtual environment and `pip install -r requirements.in`
6. Import the speakers: `python main.py presenters /path/to/speakers.json --output-folder /path/to/year.djangocon.us/`
7. Import the schedule: `python main.py main /path/to/sessions.json --output-folder /path/to/year.djangocon.us/`
8. Add and commit the result in `src/_content/`

## Update the manual schedule bits (lunch, break, registration)
1. Edit the `ManualScheduleEntry` records in models.py
2. `cd /path/to/year.djangocon.us`
3. `python tools/process.py generate-manual-schedule-data`

## Generate the list of talks blog post

Before you start, edit `tools/generate_speaker_blog_post.py` and adjust
the template bits to get the year and conference info right.

1. After importing the schedule, `cd /path/to/year.djangocon.us/tools/`
2. `python generate_speaker_blog_post.py`
3. Copy the output into `src/_content/posts/announcing-lineup.md`
4. Add and commit it

## Create placeholders for keynotes, orientation, etc.
**WARNING**: If you have an organizer who is also presenting a talk, this will overwrite
their presenter bio.

1. Edit the start/stop times and organizer slugs in `tools/constants.py`
2. `python tools/process.py generate-placeholders`
3. Add and commit the changes made to `src/_content`

## Generate a CSV for Sendy to use with the "confirm your talk time" email

1. Open a Python shell, ideally in the directory where you saved the speaker/session files
2. Run some Python code:
```python
import csv
import zoneinfo
import datetime
from pathlib import Path

session_file = Path('/path/to/sessions.json')
speaker_file = Path('/path/to/speakers.json')
session_data = json.loads(session_file.read_text())
speaker_data = json.loads(speaker_file.read_text())

speakers = {speaker['ID']: speaker for speaker in speaker_data}

output = []

tz = zoneinfo.ZoneInfo('America/New_York')  # adjust for future years as needed

for talk in session_data:
    for speaker_id in talk['Speaker IDs']:
        speaker = speakers[speaker_id]
        time = datetime.datetime.fromisoformat(talk['Start']).astimezone(tz).strftime('%A, %B %d at %I:%M %p %Z')
        output.append({'Name': speaker['Name'], 'Email': speaker['Email'], 'Title': talk['Proposal title'], 'Start time': time})

with open('schedule_mail_merge.csv', 'w') as outfile:
    field_names = list(output[0].keys())
    writer = csv.DictWriter(outfile, fieldnames=field_names)
    writer.writeheader()
    writer.writerows(output)
```
3. Look over that CSV to make sure nobody has quotes in their talk titles or names because that will cause Sendy to throw a 500.
4. Upload that list to Sendy (ask the automation team for help if needed)
