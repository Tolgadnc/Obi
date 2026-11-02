"""Load the YAML data files and check that they fit together."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import BaseModel, TypeAdapter, ValidationError

from .models import LANGS, Belt, Stage, Technique, Text


class ContentError(Exception):
    """The data has problems; `problems` lists every one of them, not just the first."""

    def __init__(self, problems: list[str]):
        super().__init__(f"{len(problems)} problem(s) in the data")
        self.problems = problems


@dataclass
class Content:
    belts: list[Belt]  # from 6th kyu (white) to 1st kyu (brown)
    techniques: dict[str, Technique]
    ui: dict[str, Text]
    warnings: list[str] = field(default_factory=list)
    _home: dict[str, Belt] = field(default_factory=dict, repr=False)
    _appearances: dict[str, list[tuple[Belt, Stage]]] = field(default_factory=dict, repr=False)

    def home_belt(self, technique: Technique) -> Belt:
        """The belt where the technique is introduced. Its page lives under that belt's URL."""
        return self._home[technique.id]

    def appearances(self, technique: Technique) -> list[tuple[Belt, Stage]]:
        return self._appearances[technique.id]

    def neighbours(self, belt: Belt) -> tuple[Belt | None, Belt | None]:
        index = self.belts.index(belt)
        previous = self.belts[index - 1] if index > 0 else None
        following = self.belts[index + 1] if index + 1 < len(self.belts) else None
        return previous, following


def load_content(data_dir: Path, *, strict: bool = True) -> Content:
    """Read and check belts.yaml, techniques.yaml and ui.yaml.

    In strict mode every technique with a page needs an approved video or a
    no_video_reason; otherwise a missing video is only a warning (for drafts).
    """
    problems: list[str] = []
    belts = _parse_list(Belt, _read(data_dir / "belts.yaml", problems), "belts.yaml", problems)
    techniques = _parse_list(
        Technique, _read(data_dir / "techniques.yaml", problems), "techniques.yaml", problems
    )
    ui = _parse_ui(_read(data_dir / "ui.yaml", problems), problems)
    if problems:
        raise ContentError(problems)

    content = Content(belts=belts, techniques={t.id: t for t in techniques}, ui=ui)
    problems += _duplicates("technique id", [t.id for t in techniques])
    problems += _duplicates("belt id", [b.id for b in belts])
    for lang in LANGS:
        problems += _duplicates(f"belt slug ({lang})", [b.slug[lang] for b in belts])
    if [b.kyu for b in belts] != sorted((b.kyu for b in belts), reverse=True):
        problems.append("belts.yaml: list the belts from the highest kyu (white) to the lowest")
    if problems:
        raise ContentError(problems)

    problems += _link_syllabus(content)
    for technique in techniques:
        if technique.has_page and not technique.approved_videos and not technique.no_video_reason:
            message = f"{technique.id}: needs an approved video or a no_video_reason"
            if strict:
                problems.append(message)
            else:
                content.warnings.append(message)
    if problems:
        raise ContentError(problems)
    return content


def _link_syllabus(content: Content) -> list[str]:
    """Check every syllabus reference and record where each technique appears."""
    problems = []
    for belt in content.belts:
        seen_in_belt = set()
        for stage in Stage:
            for technique_id in belt.syllabus.get(stage, []):
                where = f"belts.yaml › {belt.id} › {stage}"
                if technique_id not in content.techniques:
                    problems.append(f"{where}: unknown technique {technique_id!r}")
                    continue
                if technique_id in seen_in_belt:
                    problems.append(f"{where}: {technique_id} is listed twice in this belt")
                    continue
                seen_in_belt.add(technique_id)
                if stage is Stage.BASIS:
                    if technique_id in content._home:
                        first = content._home[technique_id].id
                        problems.append(f"{where}: {technique_id} is already introduced at {first}")
                        continue
                    content._home[technique_id] = belt
                elif stage is Stage.VERDIEPING and technique_id not in content._home:
                    problems.append(
                        f"{where}: {technique_id} must be introduced (basis) at an earlier belt"
                    )
                content._appearances.setdefault(technique_id, []).append((belt, stage))

    for technique in content.techniques.values():
        if technique.id not in content._appearances:
            problems.append(f"techniques.yaml › {technique.id}: not used by any belt")
        elif technique.has_page and technique.id not in content._home:
            problems.append(f"techniques.yaml › {technique.id}: never introduced (basis) at a belt")
    return problems


def _duplicates(what: str, values: list[str]) -> list[str]:
    seen, problems = set(), []
    for value in values:
        if value in seen:
            problems.append(f"duplicate {what}: {value!r}")
        seen.add(value)
    return problems


def _parse_list[M: BaseModel](model: type[M], raw, filename: str, problems: list[str]) -> list[M]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        problems.append(f"{filename}: expected a list of entries")
        return []
    entries = []
    for index, item in enumerate(raw, start=1):
        label = item.get("id", f"entry {index}") if isinstance(item, dict) else f"entry {index}"
        try:
            entries.append(model.model_validate(item))
        except ValidationError as error:
            problems += _describe(error, f"{filename} › {label}")
    return entries


def _parse_ui(raw, problems: list[str]) -> dict[str, Text]:
    try:
        return TypeAdapter(dict[str, Text]).validate_python(raw)
    except ValidationError as error:
        problems += _describe(error, "ui.yaml")
        return {}


def _describe(error: ValidationError, where: str) -> list[str]:
    lines = []
    for detail in error.errors():
        location = ".".join(str(part) for part in detail["loc"])
        lines.append(f"{where}: {location + ': ' if location else ''}{detail['msg']}")
    return lines


def _read(path: Path, problems: list[str]):
    try:
        with path.open(encoding="utf-8") as file:
            return yaml.load(file, Loader=_UniqueKeyLoader)  # a SafeLoader subclass, so safe
    except FileNotFoundError:
        problems.append(f"{path.name}: file not found in {path.parent}")
    except yaml.YAMLError as error:
        problems.append(f"{path.name}: {error}")
    return None


class _UniqueKeyLoader(yaml.SafeLoader):
    """PyYAML silently keeps the last of two identical keys; we'd rather hear about it."""


def _construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False):
    keys = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in keys:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        keys.add(key)
    return loader.construct_mapping(node, deep=deep)


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)
