"""Render the content to a static site: one page per language, belt and technique.

All links are relative, so the site works at any address (GitHub Pages serves it under /obi/).
"""

import posixpath
import shutil
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape

from .content import Content
from .models import LANGS, Belt, Category, Stage, Technique

STATIC_DIR = Path(__file__).parent / "static"
SOURCE_URL = "https://judovlaanderengroeimodel.be/leerlijn-techniek/"


@dataclass
class Group:
    category: Category
    techniques: list[Technique]


@dataclass
class Section:
    stage: Stage
    groups: list[Group]


def build(content: Content, out: Path, *, draft: bool = False) -> int:
    """Write the whole site to `out`, replacing what was there. Returns the number of pages."""
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC_DIR, out / "static")
    renderer = _Renderer(content, out, draft)
    renderer.write_root()
    for lang in LANGS:
        renderer.write(
            "home.html", lang, {code: home_path(code) for code in LANGS}, belts=content.belts
        )
        for belt in content.belts:
            previous, following = content.neighbours(belt)
            renderer.write(
                "belt.html",
                lang,
                {code: belt_path(code, belt) for code in LANGS},
                belt=belt,
                sections=belt_sections(content, belt),
                previous=previous,
                following=following,
            )
        for technique in content.techniques.values():
            if technique.has_page:
                renderer.write(
                    "technique.html",
                    lang,
                    {code: technique_path(code, content, technique) for code in LANGS},
                    technique=technique,
                    home_belt=content.home_belt(technique),
                    appearances=content.appearances(technique),
                )
    return renderer.pages


def home_path(lang: str) -> str:
    return f"{lang}/"


def belt_path(lang: str, belt: Belt) -> str:
    return f"{lang}/{belt.slug[lang]}/"


def technique_path(lang: str, content: Content, technique: Technique) -> str:
    return f"{belt_path(lang, content.home_belt(technique))}{technique.id}/"


def belt_sections(content: Content, belt: Belt) -> list[Section]:
    """The belt's syllabus by stage, and within each stage by category; empty ones left out."""
    sections = []
    for stage in Stage:
        techniques = [content.techniques[id_] for id_ in belt.syllabus.get(stage, [])]
        groups = [Group(c, [t for t in techniques if t.category is c]) for c in Category]
        if techniques:
            sections.append(Section(stage, [group for group in groups if group.techniques]))
    return sections


def relative_url(from_dir: str, to: str) -> str:
    """Link from a page in directory `from_dir` to `to`: a directory ending in "/" or a file."""
    rel = posixpath.relpath(to or ".", from_dir or ".")
    if to and not to.endswith("/"):
        return rel
    return "./" if rel == "." else f"{rel}/"


def ordinal(number: int, lang: str) -> str:
    if lang == "nl":
        return f"{number}{'ste' if number in (1, 8) or number >= 20 else 'de'}"
    if 10 <= number % 100 <= 20:
        return f"{number}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def text_colour_on(background: str) -> str:
    """Black or white, whichever has the higher WCAG contrast against `background` (#rrggbb)."""

    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(int(background[i : i + 2], 16) / 255) for i in (1, 3, 5))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "#000000" if (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05) else "#ffffff"


class _Renderer:
    def __init__(self, content: Content, out: Path, draft: bool):
        self.content = content
        self.out = out
        self.draft = draft
        self.pages = 0
        self.env = Environment(
            loader=PackageLoader("obi", "templates"),
            autoescape=select_autoescape(),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )
        self.env.filters["on_colour"] = text_colour_on

    def write_root(self) -> None:
        html = self.env.get_template("root.html").render(url=lambda to: relative_url("", to))
        self._save("", html)

    def write(self, template: str, lang: str, paths: dict[str, str], **context) -> None:
        """Render `template` for `lang` at paths[lang]; `paths` gives the same page per language."""
        here = paths[lang]
        content = self.content

        def url(to: str) -> str:
            return relative_url(here, to)

        def t(key: str) -> str:
            return content.ui[key][lang]  # a KeyError fails the build: no silently missing text

        html = self.env.get_template(template).render(
            lang=lang,
            langs=LANGS,
            lang_urls={code: url(path) for code, path in paths.items()},
            url=url,
            t=t,
            home_url=url(home_path(lang)),
            belt_url=lambda belt: url(belt_path(lang, belt)),
            technique_url=lambda technique: url(technique_path(lang, content, technique)),
            kyu=lambda number: f"{ordinal(number, lang)} kyu",
            source_url=SOURCE_URL,
            draft=self.draft,
            **context,
        )
        self._save(here, html)

    def _save(self, directory: str, html: str) -> None:
        path = self.out / directory / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        self.pages += 1
