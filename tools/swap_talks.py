"""Swap two talks in the schedule"""

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


@app.command()
def swap(
    talk1: str,
    talk2: str,
):
    """Switch two talks in the program"""
    talk_1_text = Path(talk1).read_text()
    talk_2_text = Path(talk2).read_text()
    output_folder = Path(talk1).parent
    talk_1_data = frontmatter.loads(talk_1_text)
    talk_2_data = frontmatter.loads(talk_2_text)
    talk_1_schedule = models.Schedule(**talk_1_data.metadata)
    talk_2_schedule = models.Schedule(**talk_2_data.metadata)
    t1_room = talk_1_schedule.room
    t1_start = talk_1_schedule.start_datetime
    t1_end = talk_1_schedule.end_datetime
    t1_track = talk_1_schedule.track
    t1_duration = t1_end - t1_start
    t2_duration = talk_2_schedule.end_datetime - talk_2_schedule.start_datetime
    assert t2_duration == t1_duration, "Talks are not the same length!"
    talk_1_schedule.room = talk_2_schedule.room
    talk_1_schedule.start_datetime = talk_2_schedule.start_datetime
    talk_1_schedule.end_datetime = talk_2_schedule.end_datetime
    talk_1_schedule.track = talk_2_schedule.track
    talk_2_schedule.start_datetime = t1_start
    talk_2_schedule.end_datetime = t1_end
    talk_2_schedule.room = t1_room
    talk_2_schedule.track = t1_track
    Path(talk1).unlink()
    Path(talk2).unlink()
    output_path: Path = (
            output_folder
            # TODO please make this less ugly
            / f"{talk_1_schedule.start_datetime.year}-{talk_1_schedule.start_datetime.month:0>2}"
            f"-{talk_1_schedule.start_datetime.day:0>2}-{talk_1_schedule.start_datetime.hour:0>2}"
            f"-{talk_1_schedule.start_datetime.minute:0>2}-{talk_1_schedule.track}-{slugify(talk_1_schedule.title)}.md"
        )
    talk_1_data.metadata.update(talk_1_schedule.model_dump(exclude_unset=True))
    output_path.write_text(frontmatter.dumps(talk_1_data))
    output_path: Path = (
            output_folder
            # TODO please make this less ugly
            / f"{talk_2_schedule.start_datetime.year}-{talk_2_schedule.start_datetime.month:0>2}"
            f"-{talk_2_schedule.start_datetime.day:0>2}-{talk_2_schedule.start_datetime.hour:0>2}"
            f"-{talk_2_schedule.start_datetime.minute:0>2}-{talk_2_schedule.track}-{slugify(talk_2_schedule.title)}.md"
        )
    talk_2_data.metadata.update(talk_2_schedule.model_dump(exclude_unset=True))
    output_path.write_text(frontmatter.dumps(talk_2_data))

if __name__ == "__main__":
    app()
