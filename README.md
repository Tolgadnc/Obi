# Obi

An unofficial, bilingual (Dutch/English) web app that shows, for each judo belt, what the
Judo Vlaanderen kyu syllabus requires, with a video for every technique.

**Not affiliated with Judo Vlaanderen.** The belt syllabus is based on the Judo Vlaanderen
[Groeimodel](https://judovlaanderengroeimodel.be/leerlijn-techniek/). Videos are embedded from
YouTube and belong to their creators.

The design decisions are in [DESIGN.md](DESIGN.md). Deviations from the source syllabus are in
[SOURCE_NOTES.md](SOURCE_NOTES.md).

## How it works

A Python script reads the YAML files in `data/`, validates them, and renders a static site
(Jinja2 templates, a little plain JavaScript, no framework). GitHub Actions builds the site on
every push to `main` and publishes it on GitHub Pages. There is no server and no database.

```
data/*.yaml  ->  pydantic validation  ->  Jinja2 templates  ->  _site/  ->  GitHub Pages
```

## Commands

You need [uv](https://docs.astral.sh/uv/). It installs the right Python version itself.

```sh
uv run obi serve          # preview at http://127.0.0.1:8000, rebuilds when you save
uv run obi build          # check the data and write the site to _site/ (strict, like CI)
uv run obi build --draft  # same, but allow techniques without an approved video
uv run obi check-videos   # ask YouTube whether every video still exists and can be embedded
uv run pytest             # tests
uv run ruff check . && uv run ruff format .
```

`obi serve` runs in draft mode unless you pass `--strict`.

## Editing the content

Everything lives in three files, and each one explains its fields at the top:

- `data/belts.yaml`: the belts and which techniques each requires, per stage
- `data/techniques.yaml`: every technique, with translations and videos
- `data/ui.yaml`: interface text in Dutch and English

To **add a video**, add an entry under the technique's `videos`. It is not shown until you set
`approved: true`:

```yaml
  videos:
    - youtube: "abcDEF12345" # the part after watch?v=, in quotes
      title: O-soto-gari demonstration
      channel: Some Judo Channel
      start: 12              # optional, seconds
      end: 40                # optional, seconds
      approved: true
```

The first approved video is the main one; up to two more are shown as extras. If there is no
suitable video, set `no_video_reason` instead. The build (and CI) refuses to publish while any
technique has neither.

A scheduled workflow checks every video once a week and opens an issue if one has been
removed or no longer allows embedding.

## Licence

The code is MIT licensed (see [LICENSE](LICENSE)). The `data/` folder is not covered by that
licence: the syllabus structure comes from Judo Vlaanderen, and the videos belong to their
creators.
