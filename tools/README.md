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

## Sync talks with the YouTube playlist

`tools/youtube_sync.py` matches each video in a playlist to its talk file and
records the video on the talk. It needs [uv](https://docs.astral.sh/uv/), which
installs the script's dependencies for you.

1. `cd /path/to/year.djangocon.us`
2. Dry run: `uv run tools/youtube_sync.py PLAYLIST_ID`
3. Check the table. Green rows are confident matches; yellow rows are
   low-confidence and are never written. Videos with no talk and talks with no
   video are listed underneath.
4. Write the matches: `uv run tools/youtube_sync.py PLAYLIST_ID --write`.
   This adds `video_url` and `youtube_id` to each matched talk's front matter
   and leaves the rest of the file untouched. Re-running is safe.
5. Add and commit the changes in `src/_content/schedule/`

Matching uses the talk permalink in the video description first, then title
and presenter name similarity, so it works on fresh uploads too.

Each run also writes `.youtube-sync/report.csv` and
`.youtube-sync/descriptions/<talk>.txt`. Each `.txt` file holds a suggested YouTube
title and description (talk abstract plus presenter links), mirroring
`src/_includes/youtube-copy-and-paste.html`, to paste into YouTube Studio.
Pass `--location` if the conference wasn't in Chicago, and `--cache
playlist.json` to avoid refetching the playlist on every run.

### Push titles and descriptions to YouTube

The script can update the videos directly through the YouTube Data API,
signed in as someone who manages the DjangoCon US channel.

1. Sign in once: `uv run tools/youtube_sync.py --login`. It prints a link (and
   tries to open it). Pick the DjangoCon US channel's account (or brand
   account) and approve. The script then prints the channel you're signed in
   as. The token is saved to `~/.config/djangocon-youtube-sync/token.json`,
   outside the repo, and refreshes itself; `--logout` deletes it.
2. Try one video first:
   `uv run tools/youtube_sync.py PLAYLIST_ID --update-youtube --only TALK_FILE_NAME`
3. Then all confident matches: `uv run tools/youtube_sync.py PLAYLIST_ID --update-youtube`

Before anything changes, you get a table of what will change and a
confirmation prompt (`--yes` skips the prompt). The current title and
description of every video about to change are saved to
`.youtube-sync/backups/`. To undo a run:
`uv run tools/youtube_sync.py --restore .youtube-sync/backups/youtube-<timestamp>.json`.
Pass `--no-update-titles` to only update descriptions. Signing in also
lets the script read private and unlisted playlists.

**One-time OAuth client setup.** The sign-in needs an OAuth client of type
"Desktop app" in a Google Cloud project with the YouTube Data API v3
enabled:

1. In [Google Cloud Console](https://console.cloud.google.com/), pick or create a project
   and enable the **YouTube Data API v3**.
2. Configure the OAuth consent screen (External; add whoever will sign in as a
   test user).
3. Create credentials → OAuth client ID → **Desktop app**, and download the JSON to
   `~/.config/djangocon-youtube-sync/client_secret.json` (or pass `--client-secrets`).

If you already use the Google Workspace CLI (`gws`), the script falls back to
its client at `~/.config/gws/client_secret.json`. That only works if the YouTube
Data API is enabled on that client's project.

Each video update costs 50 units of the API's default 10,000/day quota, so
roughly 200 videos a day.

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
