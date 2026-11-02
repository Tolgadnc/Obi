import pytest
from conftest import ROOT, video

from obi.content import ContentError, load_content
from obi.models import GROUPS, Category, Stage


def problems(write_data, data, *, strict=True) -> list[str]:
    with pytest.raises(ContentError) as caught:
        load_content(write_data(data), strict=strict)
    return caught.value.problems


def test_valid_data_loads(write_data, data):
    content = load_content(write_data(data))
    o_soto_gari = content.techniques["o-soto-gari"]
    assert content.home_belt(o_soto_gari).id == "geel"
    assert [(belt.id, stage) for belt, stage in content.appearances(o_soto_gari)] == [
        ("geel", Stage.BASIS),
        ("oranje", Stage.VERDIEPING),
    ]
    assert [video.youtube for video in o_soto_gari.approved_videos] == ["BBBBBBBBBBB"]


def test_real_data_loads():
    load_content(ROOT / "data", strict=False)


def test_real_ui_has_a_label_for_every_stage_category_and_group():
    ui = load_content(ROOT / "data", strict=False).ui
    keys = [f"stage.{stage}" for stage in Stage] + [f"stage.{stage}.hint" for stage in Stage]
    keys += [f"category.{category}" for category in Category]
    keys += [f"group.{group}" for groups in GROUPS.values() for group in groups]
    assert [key for key in keys if key not in ui] == []


def test_problems_name_the_entry(write_data, data):
    del data["techniques"][1]["translation"]["en"]
    assert problems(write_data, data) == [
        "techniques.yaml › o-soto-gari: translation.en: Field required"
    ]


def test_every_problem_is_reported_not_just_the_first(write_data, data):
    del data["techniques"][0]["translation"]["nl"]
    data["techniques"][1]["group"] = "koshi-waza-typo"
    assert len(problems(write_data, data)) == 2


def test_unknown_technique_in_syllabus(write_data, data):
    data["belts"][1]["syllabus"]["basis"].append("o-uchi-gari")
    assert problems(write_data, data) == [
        "belts.yaml › geel › basis: unknown technique 'o-uchi-gari'"
    ]


@pytest.mark.parametrize(
    ("index", "group", "expected"),
    [
        (1, None, "group must be one of"),
        (1, "osaekomi-waza", "group must be one of"),
        (0, "te-waza", "ukemi techniques have no group"),
    ],
)
def test_group_must_fit_the_category(write_data, data, index, group, expected):
    data["techniques"][index]["group"] = group
    assert expected in problems(write_data, data)[0]


def test_training_forms_are_text_only(write_data, data):
    data["techniques"][2]["videos"] = [video()]
    assert "training forms are text-only" in problems(write_data, data)[0]


def test_only_training_forms_have_a_description(write_data, data):
    data["techniques"][0]["description"] = {"nl": "x", "en": "x"}
    assert "only training forms have a description" in problems(write_data, data)[0]


def test_a_technique_is_introduced_once(write_data, data):
    data["belts"][2]["syllabus"]["basis"] = ["o-soto-gari"]
    data["belts"][2]["syllabus"]["verdieping"] = []
    assert problems(write_data, data) == [
        "belts.yaml › oranje › basis: o-soto-gari is already introduced at geel"
    ]


def test_verdieping_needs_an_earlier_basis(write_data, data):
    data["belts"][1]["syllabus"]["verdieping"] = ["ushiro-ukemi"]
    data["belts"][1]["syllabus"]["basis"] = ["o-soto-gari"]
    data["belts"][2]["syllabus"]["basis"] = ["ushiro-ukemi"]
    assert (
        "belts.yaml › geel › verdieping: ushiro-ukemi must be introduced (basis) at an earlier belt"
        in problems(write_data, data)
    )


def test_a_technique_appears_once_per_belt(write_data, data):
    data["belts"][1]["syllabus"]["verdieping"] = ["o-soto-gari"]
    assert "o-soto-gari is listed twice in this belt" in problems(write_data, data)[0]


def test_every_technique_is_used(write_data, data):
    data["belts"][1]["syllabus"]["basis"] = ["o-soto-gari"]
    assert problems(write_data, data) == ["techniques.yaml › ushiro-ukemi: not used by any belt"]


def test_strict_mode_needs_a_video_or_a_reason(write_data, data):
    data["techniques"][0]["videos"] = [video(approved=False)]
    assert problems(write_data, data) == [
        "ushiro-ukemi: needs an approved video or a no_video_reason"
    ]

    draft = load_content(write_data(data), strict=False)
    assert draft.warnings == ["ushiro-ukemi: needs an approved video or a no_video_reason"]

    data["techniques"][0]["no_video_reason"] = "no suitable public video found"
    load_content(write_data(data))


def test_a_reason_contradicts_an_approved_video(write_data, data):
    data["techniques"][0]["no_video_reason"] = "none found"
    assert "no_video_reason is set but there is an approved video" in problems(write_data, data)[0]


def test_at_most_three_approved_videos(write_data, data):
    data["techniques"][0]["videos"] = [video(f"{n}AAAAAAAAAA") for n in range(4)]
    assert "at most 3 approved videos" in problems(write_data, data)[0]


@pytest.mark.parametrize(
    "bad_video",
    [video("too-short"), video(start=30, end=10), video(start=-1)],
)
def test_bad_videos_are_rejected(write_data, data, bad_video):
    data["techniques"][0]["videos"] = [bad_video]
    assert problems(write_data, data)[0].startswith("techniques.yaml › ushiro-ukemi: videos.0")


def test_duplicate_yaml_keys_are_rejected(write_data, data):
    folder = write_data(data)
    path = folder / "techniques.yaml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "category: ukemi", "category: ukemi\n  category: kata"
        ),
        encoding="utf-8",
    )
    assert "duplicate key 'category'" in problems(lambda _: folder, data)[0]


def test_belts_are_listed_from_white_to_brown(write_data, data):
    data["belts"].reverse()
    assert (
        "list the belts from the highest kyu (white) to the lowest" in problems(write_data, data)[0]
    )


def test_a_belt_without_syllabus_needs_an_intro(write_data, data):
    del data["belts"][0]["intro"]
    assert "a belt without syllabus items needs an intro" in problems(write_data, data)[0]
