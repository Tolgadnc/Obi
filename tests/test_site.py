import re
from pathlib import Path

import pytest

from obi.content import load_content
from obi.site import build, ordinal, relative_url, text_colour_on


@pytest.fixture
def site(tmp_path, write_data, data) -> Path:
    out = tmp_path / "_site"
    build(load_content(write_data(data)), out)
    return out


def page(site: Path, path: str) -> str:
    return (site / path / "index.html").read_text(encoding="utf-8")


def test_every_page_exists_in_both_languages(site):
    for path in [
        "",
        "nl",
        "en",
        "nl/wit",
        "en/white",
        "nl/geel",
        "en/yellow",
        "nl/oranje",
        "en/orange",
        "nl/geel/o-soto-gari",
        "en/yellow/o-soto-gari",
        "nl/geel/ushiro-ukemi",
    ]:
        assert (site / path / "index.html").is_file(), path
    assert not (site / "nl" / "oranje" / "tokui-waza").exists()  # training forms have no page


def test_every_local_link_resolves(site):
    for html_file in site.rglob("*.html"):
        for target in re.findall(r'(?:href|src)="([^"]+)"', html_file.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (html_file.parent / target).resolve()
            if target.endswith("/"):
                resolved = resolved / "index.html"
            assert resolved.is_file(), f"{html_file.relative_to(site)} links to missing {target}"


def test_language_switch_points_to_the_same_page(site):
    html = page(site, "nl/geel/o-soto-gari")
    assert 'href="../../../en/yellow/o-soto-gari/" hreflang="en"' in html
    assert 'href="./" hreflang="nl"' in html


def test_videos_load_only_on_click(site):
    html = page(site, "nl/geel/o-soto-gari")
    assert 'data-youtube="BBBBBBBBBBB" data-start="12" data-end="40"' in html
    assert "https://www.youtube.com/watch?v=BBBBBBBBBBB&amp;t=12s" in html
    assert "<iframe" not in html
    assert "CCCCCCCCCCC" not in html  # not approved


def test_belt_page_groups_by_stage(site):
    html = page(site, "en/orange")
    assert html.index("<h2>Apply</h2>") < html.index("<h2>Make it your own</h2>")
    assert "Choose your own throw." in html


def test_draft_placeholder_only_in_draft_builds(tmp_path, write_data, data):
    data["techniques"][0]["videos"] = []
    out = tmp_path / "draft"
    build(load_content(write_data(data), strict=False), out, draft=True)
    assert "no approved video yet" in page(out, "en/yellow/ushiro-ukemi")


def test_footer_carries_the_disclaimer_and_source(site):
    html = page(site, "nl")
    assert "niet verbonden met Judo Vlaanderen" in html
    assert 'href="https://judovlaanderengroeimodel.be/leerlijn-techniek/"' in html


@pytest.mark.parametrize(
    ("from_dir", "to", "expected"),
    [
        ("nl/geel/", "nl/geel/o-soto-gari/", "o-soto-gari/"),
        ("nl/geel/o-soto-gari/", "static/style.css", "../../../static/style.css"),
        ("nl/", "nl/", "./"),
        ("", "nl/", "nl/"),
        ("nl/", "", "../"),
    ],
)
def test_relative_url(from_dir, to, expected):
    assert relative_url(from_dir, to) == expected


@pytest.mark.parametrize(
    ("number", "nl", "en"),
    [
        (1, "1ste", "1st"),
        (2, "2de", "2nd"),
        (3, "3de", "3rd"),
        (5, "5de", "5th"),
        (8, "8ste", "8th"),
    ],
)
def test_ordinal(number, nl, en):
    assert (ordinal(number, "nl"), ordinal(number, "en")) == (nl, en)


@pytest.mark.parametrize(
    ("colour", "text"),
    [
        ("#ffffff", "#000000"),
        ("#f6c90e", "#000000"),
        ("#1f5fbf", "#ffffff"),
        ("#6b4226", "#ffffff"),
    ],
)
def test_text_colour_on_belt_colours(colour, text):
    assert text_colour_on(colour) == text
