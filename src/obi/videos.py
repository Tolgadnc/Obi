"""Check that linked videos still exist and still allow embedding.

Uses YouTube's oEmbed endpoint, which needs no API key: 200 means embeddable,
401/403 means the uploader disabled embedding, 400/404 means removed or private.
"""

import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from .content import Content
from .models import Technique, Video

OEMBED_URL = "https://www.youtube.com/oembed"


class Status(StrEnum):
    OK = "ok"
    NOT_EMBEDDABLE = "embedding disabled"
    UNAVAILABLE = "removed or private"
    UNKNOWN = "could not check"


@dataclass
class Result:
    technique: Technique
    video: Video
    status: Status

    @property
    def broken(self) -> bool:
        return self.status in (Status.NOT_EMBEDDABLE, Status.UNAVAILABLE)


def check_video(youtube_id: str, opener: Callable = urllib.request.urlopen) -> Status:
    query = urllib.parse.urlencode(
        {"url": f"https://www.youtube.com/watch?v={youtube_id}", "format": "json"}
    )
    try:
        with opener(f"{OEMBED_URL}?{query}", timeout=15) as response:
            return Status.OK if response.status == 200 else Status.UNKNOWN
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            return Status.NOT_EMBEDDABLE
        if error.code in (400, 404):
            return Status.UNAVAILABLE
        return Status.UNKNOWN
    except urllib.error.URLError, TimeoutError:
        return Status.UNKNOWN


def check_all(content: Content, check: Callable[[str], Status] = check_video) -> list[Result]:
    return [
        Result(technique, video, check(video.youtube))
        for technique in content.techniques.values()
        for video in technique.videos
    ]


def report(results: list[Result]) -> str:
    """A Markdown report of every video that isn't fine, for the terminal or a GitHub issue."""
    problems = [result for result in results if result.status is not Status.OK]
    if not problems:
        return f"All {len(results)} videos are available and embeddable.\n"
    lines = [
        f"{len(problems)} of {len(results)} videos have a problem.",
        "",
        "| Technique | Video | Approved | Status |",
        "|---|---|---|---|",
    ]
    for result in problems:
        video = result.video
        title = video.title.replace("|", "\\|")
        lines.append(
            f"| {result.technique.id} | [{title}]({video.watch_url}) "
            f"| {'yes' if video.approved else 'no'} | {result.status} |"
        )
    return "\n".join(lines) + "\n"
