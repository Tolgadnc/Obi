"""The shape of one entry in each data file, validated with pydantic.

Rules that span several entries (references between belts and techniques, uniqueness)
live in content.py, because a single entry can't see the others.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

LANGS = ("nl", "en")
MAX_APPROVED_VIDEOS = 3  # one primary video plus at most two extras

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
YouTubeId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{11}$")]
Colour = Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")]


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Text(Entry):
    """A piece of text in every interface language."""

    nl: NonEmpty
    en: NonEmpty

    def __getitem__(self, lang: str) -> str:
        return getattr(self, lang)


class Slugs(Entry):
    """A URL segment in every interface language."""

    nl: Slug
    en: Slug

    def __getitem__(self, lang: str) -> str:
        return getattr(self, lang)


class Category(StrEnum):
    """Belt pages list the categories in this order."""

    UKEMI = "ukemi"
    NAGE_WAZA = "nage-waza"
    KATAME_WAZA = "katame-waza"
    KATA = "kata"
    OEFENVORMEN = "oefenvormen"


# The label a technique carries within its category: the Kodokan group for throws,
# hold / choke / armlock for groundwork. Other categories have no label.
GROUPS = {
    Category.NAGE_WAZA: {
        "te-waza",
        "koshi-waza",
        "ashi-waza",
        "ma-sutemi-waza",
        "yoko-sutemi-waza",
    },
    Category.KATAME_WAZA: {"osaekomi-waza", "shime-waza", "kansetsu-waza"},
}


class Stage(StrEnum):
    """The Groeimodel's three stages, in the order belt pages show them."""

    BASIS = "basis"  # learn the technique
    VERDIEPING = "verdieping"  # apply it: combinations, counters, transitions
    VERPERSOONLIJKING = "verpersoonlijking"  # make it your own


class Video(Entry):
    youtube: YouTubeId
    title: NonEmpty
    channel: NonEmpty
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, gt=0)
    approved: bool = False

    @model_validator(mode="after")
    def _end_after_start(self):
        if self.end is not None and self.end <= (self.start or 0):
            raise ValueError("end must be later than start")
        return self

    @property
    def watch_url(self) -> str:
        url = f"https://www.youtube.com/watch?v={self.youtube}"
        return f"{url}&t={self.start}s" if self.start else url


class Technique(Entry):
    id: Slug
    name: NonEmpty
    kanji: NonEmpty | None = None
    category: Category
    group: str | None = None
    translation: Text
    description: Text | None = None
    videos: list[Video] = []
    no_video_reason: NonEmpty | None = None

    @model_validator(mode="after")
    def _fits_its_category(self):
        allowed = GROUPS.get(self.category)
        if allowed is None and self.group is not None:
            raise ValueError(f"{self.category} techniques have no group")
        if allowed is not None and self.group not in allowed:
            raise ValueError(f"group must be one of: {', '.join(sorted(allowed))}")

        if self.category is Category.OEFENVORMEN:
            if self.description is None:
                raise ValueError("training forms need a description")
            if self.videos or self.no_video_reason:
                raise ValueError("training forms are text-only: no videos, no no_video_reason")
        elif self.description is not None:
            raise ValueError("only training forms have a description")

        approved = self.approved_videos
        if len(approved) > MAX_APPROVED_VIDEOS:
            raise ValueError(f"at most {MAX_APPROVED_VIDEOS} approved videos")
        if approved and self.no_video_reason:
            raise ValueError("no_video_reason is set but there is an approved video")
        return self

    @property
    def approved_videos(self) -> list[Video]:
        return [video for video in self.videos if video.approved]

    @property
    def has_page(self) -> bool:
        """Training forms are explained inline on the belt page; everything else gets a page."""
        return self.category is not Category.OEFENVORMEN


class Belt(Entry):
    id: Slug
    kyu: int = Field(ge=1, le=6)
    colour: Colour
    name: Text
    slug: Slugs
    intro: Text | None = None
    syllabus: dict[Stage, list[Slug]] = {}

    @model_validator(mode="after")
    def _has_content(self):
        if not self.has_exam and self.intro is None:
            raise ValueError("a belt without syllabus items needs an intro")
        return self

    @property
    def has_exam(self) -> bool:
        return any(self.syllabus.values())
