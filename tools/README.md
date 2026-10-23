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

## Sync talks with YouTube

Two scripts, one per direction, plus one for captions. Both need [uv](https://docs.astral.sh/uv/),
which installs each script's dependencies for you. All three take `--dry-mode`
(or `--dry-run`) to show what would change without changing anything.

| Script | Direction | What it changes |
|---|---|---|
| `tools/youtube_to_frontmatter.py` | YouTube → front matter | adds `video_url` and `youtube_id` to talk files |
| `tools/frontmatter_to_youtube.py` | front matter → YouTube | sets video titles and descriptions from our template |
| `tools/captions_to_youtube.py` | caption files → YouTube | uploads caption tracks |

### YouTube → front matter

1. `cd /path/to/year.djangocon.us`
2. Preview: `uv run tools/youtube_to_frontmatter.py PLAYLIST_ID --dry-mode`
3. Check the table. Green rows are confident matches; yellow rows are
   low-confidence and are never written. Videos with no talk and talks with no
   video are listed underneath, and everything is in `.youtube-sync/report.csv`.
4. Write the matches: `uv run tools/youtube_to_frontmatter.py PLAYLIST_ID`.
   This adds `video_url` and `youtube_id` to each matched talk's front matter
   and leaves the rest of the file untouched. Re-running is safe.
5. Add and commit the changes in `src/_content/schedule/`

Matching uses the talk permalink in the video description first, then title
and presenter name similarity, so it works on fresh uploads too. Pass `--cache
playlist.json` to avoid refetching the playlist on every run. Private playlists
need you to be signed in (`--login`, below).

### Front matter → YouTube

The YouTube title and description for each talk come from our template page,
[/speaking/youtube/](https://2026.djangocon.us/speaking/youtube/)
(`src/youtube-talks.html` and `src/_includes/youtube-copy-and-paste.html`):
presenter details and social links, then the DjangoCon US and DEFNA links. The
script reads that page, so change the template there. By default it reads the
live site; `--template dist/speaking/youtube/index.html` uses a local build.

1. Preview: `uv run tools/frontmatter_to_youtube.py --dry-mode`. This lists the
   videos that would change and writes each title and description to
   `.youtube-sync/descriptions/<talk>.txt`.
2. Try one video: `uv run tools/frontmatter_to_youtube.py --only TALK_FILE_NAME`
3. Then the rest: `uv run tools/frontmatter_to_youtube.py`

It always asks before updating (`--yes` skips the prompt) and backs up the
current titles and descriptions to `.youtube-sync/backups/` first. To undo a run:
`uv run tools/frontmatter_to_youtube.py --restore .youtube-sync/backups/youtube-<timestamp>.json`.
Pass `--no-update-titles` to only update descriptions.

### Captions → YouTube

`tools/captions_to_youtube.py` uploads caption files to their videos. Give it a
zip (or folder) of files named after the YouTube video ID, like
`z_cHhxzRozI.txt`; macOS `__MACOSX/` entries are ignored.

1. Preview: `uv run tools/captions_to_youtube.py captions.zip --dry-mode`
2. Try one video: `uv run tools/captions_to_youtube.py captions.zip --only VIDEO_ID`
3. Then the rest: `uv run tools/captions_to_youtube.py captions.zip`

- `.txt` files are plain transcripts. YouTube's auto-sync (`sync=true`)
  rejects them now (`unknownFormat`), so the script times them itself: it
  downloads the video's automatic (ASR) captions, lines the transcript's words
  up with them, and uploads the result as SRT. The SRT is saved to
  `.youtube-sync/srt/` for review. Videos without automatic captions yet, or
  where under half the words match, are skipped. `.srt`, `.vtt`, `.sbv`, and
  `.scc` keep their own timing.
- Videos that already have one of our tracks in the same language (`en` and
  `en-US` count as the same) are skipped, so re-running only uploads what's
  missing. A track that failed to process gets replaced; `--replace`
  replaces working ones too.
- **Quota:** checking a video costs 50 units, downloading its automatic
  captions 200, and uploading 400, out of 10,000 a day. That's about 650 per
  transcript, or about 15 a day. If the quota runs out
  mid-run, the script stops; run the same command the next day (quota resets
  at midnight Pacific).
- Each run logs what it created to `.youtube-sync/captions-<timestamp>.json`;
  `--undo` with that file deletes those tracks. `--draft` uploads unpublished
  drafts, and `--language` and `--name` set the track language (default `en`)
  and name (default "English").

### YouTube API setup

How the DjangoCon US YouTube sync was set up, step by step, so it can be redone
(new machine, expired client, a new organizer taking over).

#### What you end up with

| Thing | Value |
|---|---|
| Google account | one that owns or manages the DjangoCon US channel |
| Google Cloud project | **DjangoCon US YouTube** (`djangocon-us-youtube`), no organization |
| API enabled | YouTube Data API v3 |
| OAuth consent screen | "DjangoCon US YouTube Sync", External, **Testing** |
| Test users | everyone who will run the script |
| OAuth client | Desktop app named `youtube_sync.py` (any name works) |
| Client secret file | `~/.config/djangocon-youtube-sync/client_secret.json` (mode 600) |
| Saved sign-in token | `~/.config/djangocon-youtube-sync/token.json` (mode 600, written by `--login`) |
| Signed-in channel | DjangoCon US (`UC0yY6a79pPY9J0ShIHRf6yw`) |

Neither file lives in the repo, so neither can be committed by accident.

#### Before you start

Open <https://console.cloud.google.com/> and check that the avatar in the top
right is the Google account that owns or manages the DjangoCon US channel.
If it's a work (or any other) account, click the avatar and switch. Every
step below happens in that account.

#### Step 1: Create the project

1. Open <https://console.cloud.google.com/projectcreate>
2. Fill in:
   - **Project name:** `DjangoCon US YouTube` (project ID `djangocon-us-youtube`)
   - **Location:** leave as **No organization**
3. Click **Create**.
4. When the notification bell says it's done, click **Select Project** in
   that notification. The project picker at the top should now say
   **DjangoCon US YouTube**.

#### Step 2: Enable the YouTube Data API

1. Open <https://console.cloud.google.com/apis/library/youtube.googleapis.com>
2. Check that the project picker still says **DjangoCon US YouTube**.
3. Click **Enable**.
4. You land on the "YouTube Data API v3" overview page, which shows a
   **Disable API** button. That means it worked.

**Skip the "Create credentials" prompt** on that page. The consent screen has
to exist first (step 3), and the credentials are created in step 5.

#### Step 3: Set up the consent screen

1. Open <https://console.cloud.google.com/auth/overview>
2. Click **Get started** and go through the four sections:
   - **App information**
     - **App name:** `DjangoCon US YouTube Sync`
     - **User support email:** your account
     - **Next**
   - **Audience:** **External**, then **Next**
   - **Contact information:** your email, then **Next**
   - **Finish:** check the box to agree to the Google API Services User Data
     Policy, then **Continue**
3. Click **Create**.

You end up on the "OAuth Overview" page. Don't click its **Create OAuth
client** button; step 5 covers that.

#### Step 4: Add yourself as a test user

1. Open <https://console.cloud.google.com/auth/audience> (or **Audience** in
   the left sidebar).
2. Leave **Publishing status** on **Testing**. Don't click "Publish app".
3. Under **Test users**, click **+ Add users**.
4. Add your account and click **Save**.
5. Confirm it's listed under Test users.

Add anyone else who will run the script here too. Only listed test users can
sign in while the app is in Testing.

#### Step 5: Create the Desktop client and download it

1. Open <https://console.cloud.google.com/auth/clients> (or **Clients** in the
   left sidebar).
2. Click **+ Create client**.
3. Fill in:
   - **Application type:** `Desktop app`
   - **Name:** `youtube_sync.py`
4. Click **Create**.
5. In the dialog that shows the Client ID and secret, click **Download JSON**.
   It saves `client_secret_<id>.apps.googleusercontent.com.json` to
   `~/Downloads`.
   - If you closed the dialog, click the client's name in the list, then the
     download icon next to the client secret.
6. Click **OK**.

#### Step 6: Put the client secret in place

```sh
mkdir -p ~/.config/djangocon-youtube-sync
mv ~/Downloads/client_secret_*.json ~/.config/djangocon-youtube-sync/client_secret.json
chmod 700 ~/.config/djangocon-youtube-sync
chmod 600 ~/.config/djangocon-youtube-sync/client_secret.json
```

Optional check that it's the right kind of client, without printing the
secret. You want `type: installed` and `project: djangocon-us-youtube`:

```sh
python3 -c "import json; d=json.load(open('$HOME/.config/djangocon-youtube-sync/client_secret.json')); k=list(d)[0]; print('type:', k, '| project:', d[k]['project_id'])"
```

#### Step 7: Sign in

From the repo root:

```sh
uv run tools/frontmatter_to_youtube.py --login
```

All three scripts share the same sign-in, so `--login` on any of them is enough.

It prints a sign-in link and tries to open it. The script waits until you
finish in the browser.

1. On **Choose an account**, pick the account that owns or manages the channel.
2. If it asks you to choose a channel, pick **DjangoCon US**.
3. On "Google hasn't verified this app", click **Continue**. That's expected
   for an app in Testing mode.
4. Approve the "Manage your YouTube account" permission.
5. The tab says "Signed in. You can close this tab and go back to the
   terminal."

The terminal should then print:

```
Signed in as YouTube channel: DjangoCon US (UC0yY6a79pPY9J0ShIHRf6yw)
```

If it shows a different channel, or says the account has no channel, run
`uv run tools/frontmatter_to_youtube.py --logout` and then `--login` again.

**If you click the wrong account:** close that tab and stop the waiting
script with Ctrl-C. A link only works while the script that printed it is
running. Run `--login` again for a fresh link. The link always shows the
account picker, so the browser can't reuse the wrong account silently. A
non-test-user account gets "access blocked" and nothing is saved.

#### Using it

```sh
# YouTube -> front matter: preview, then record video_url + youtube_id
uv run tools/youtube_to_frontmatter.py PLFQg7E3if2as --dry-mode
uv run tools/youtube_to_frontmatter.py PLFQg7E3if2as

# Front matter -> YouTube: preview, one video, then all
uv run tools/frontmatter_to_youtube.py --dry-mode
uv run tools/frontmatter_to_youtube.py --only 2026-08-24-08-15-t0-orientation
uv run tools/frontmatter_to_youtube.py

# Undo a YouTube update from its backup
uv run tools/frontmatter_to_youtube.py --restore .youtube-sync/backups/youtube-<timestamp>.json
```

- Once signed in, `youtube_to_frontmatter.py` reads playlists through the API,
  so private and unlisted playlists work. The **DjangoCon US 2026 playlist
  (`PLFQg7E3if2as`) is private**, and yt-dlp reports it as "does not exist".
- Quota: each video update costs 50 of the default 10,000 units/day, so about
  200 updates a day.

#### Things to know

- **The sign-in expires after about 7 days.** Google limits refresh tokens for
  apps in Testing mode. When the script asks you to sign in again, repeat
  step 7. Avoiding this means publishing the app, which needs Google's
  verification for the YouTube scope. That's not worth it for a tool used a
  few times a year.
- **Scope:** `https://www.googleapis.com/auth/youtube.force-ssl`, which can
  read and edit videos on the channel.
- **Revoking access:** <https://myaccount.google.com/permissions>, remove
  "DjangoCon US YouTube Sync". Then delete
  `~/.config/djangocon-youtube-sync/token.json` (or run `--logout`).
- **New machine:** copy `client_secret.json` over (steps 6 and 7) instead of
  repeating steps 1–5. Or download it again from
  <https://console.cloud.google.com/auth/clients> in the
  `djangocon-us-youtube` project.
- **Another organizer:** add them as a test user (step 4) and give them the
  client secret file. They need to be an owner or manager of the DjangoCon US
  channel.
- **gws (Google Workspace CLI):** checked and it doesn't support YouTube (no
  `youtube` service, and the `youtube:v3` syntax is rejected). The script can
  fall back to gws's OAuth client at `~/.config/gws/client_secret.json` if no
  client secret is configured. That client usually belongs to a personal or
  work project, so the dedicated DjangoCon US project above is preferred.

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
