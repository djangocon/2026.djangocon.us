# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pytube",
# ]
# ///

# To run: uv run tools/yt_playlist.py
#
# 1. Swap PLAYLIST_ID with the playlist ID of the playlist you want to parse.
# 2. Make sure you're using git so reverting edited talk files is easy.
# 3. Run the script.
# 4. Go through the missing-talks.csv file and manually add the
#    youtube_url to the markdown files.InnerTube.__init__(client='WEB')
#    then disable the oauth usage.

# At one point things didn't work and I had to modify
# the pytube/innertube.py::

import csv
from dataclasses import dataclass
from pathlib import Path
from pytube import Playlist, YouTube

PLAYLIST_ID = "PL2NFhrDSOxgWqE_5w5CX2iUR7-P1D0ny7"
# Replace with your playlist URL
playlist_url = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
talks_directory = Path("src/_content/schedule/talks")


@dataclass
class ParsedVideo:
    title: str
    presenter1: str
    presenter2: str
    talk_prefix: str
    url: str

    @property
    def markdown_data(self):
        shortened_url = self.url.replace("https://www.youtube.com/watch?v=", "https://youtu.be/")
        return f"video_url: {shortened_url!r}"


def parse_video_title(url: str, yt_title: str) -> ParsedVideo:
    title, presenters = yt_title.rsplit(' with ', 1)
    if " and " in presenters:
        presenter1, presenter2 = presenters.rsplit(" and ", 1)
    else:
        presenter1 = presenters
        presenter2 = ""
    talk_prefix = "-".join(title.lower().split(" ")[:2])
    return ParsedVideo(
        title=title,
        presenter1=presenter1,
        presenter2=presenter2,
        talk_prefix=talk_prefix,
        url=url,
    )


def main() -> None:
    # Initialize the playlist
    playlist = Playlist(playlist_url)
    with open("missing-talks.csv", "w") as f:
        missing_talks = csv.writer(f)
        missing_talks.writerow(["title", "presenter1", "presenter2", "url"])
        for url in playlist.video_urls:
            video = YouTube(url, use_oauth=True, allow_oauth_cache=True)
            parsed = parse_video_title(url, video.title)
            matching_files = [
                f for f in talks_directory.iterdir()
                if f.is_file() and f.name.startswith(parsed.talk_prefix)
            ]
            if matching_files:
                # If we have a matching file,
                # add the video_url to the markdown data
                with open(matching_files[0], "r") as markdown_file:
                    lines = markdown_file.readlines()
                # Find the second occurrence of '---' and insert the video_url
                for i, line in enumerate(lines):
                    if i == 0:
                        continue
                    if line.strip() == "---":
                        lines.insert(i - 1, parsed.markdown_data+"\n")
                        break
                with open(matching_files[0], "w") as markdown_file:
                    markdown_file.writelines(lines)
            else:
                missing_talks.writerow([
                    parsed.title,
                    parsed.presenter1,
                    parsed.presenter2,
                    parsed.markdown_data
                ])


if __name__ == "__main__":
    main()
