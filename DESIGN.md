# Obi: design

These decisions were agreed on 2 November 2026, before any code was written. Change them
deliberately: update this file in the same commit as the change.

## Purpose and scope

- A polished public demo: an unofficial web app for Judo Vlaanderen judoka that shows what each
  belt requires, with videos.
- Read-only. No accounts, no progress tracking, no analytics.
- Kyu grades only, white to brown. Dan grades are out of scope (the model allows adding them).

## Content

- **Source**: Judo Vlaanderen's Groeimodel, *leerlijn techniek*. It is current, and at about
  50 items it is small enough to curate properly. We don't use the 2015 programme, because many
  of its items ("aanval op grond, 3 vormen") can't be shown in a single video.
- **Belts**:
  - White is the starting point and has no exam, so its page is a short intro.
  - Yellow to brown are exam belts. Each page shows what you need **to obtain** that belt.
  - No stripes, half-colour belts, minimum ages or lesson counts.
- **Belt page**: three sections in the Groeimodel's stages:
  - **Nieuw / New** (basis)
  - **Toepassen / Apply** (verdieping)
  - **Eigen maken / Make it your own** (verpersoonlijking)

  Within each section items are grouped by category: Ukemi, Nage-waza, Katame-waza, Kata,
  Oefenvormen. Kata gets its own category, although the Groeimodel files it under nage-waza.
  A toggle adds a collapsed "earlier belts" section; it arrives with the second belt.
- **Technique page**:
  - Japanese name and optional kanji.
  - Our own Dutch and English translations.
  - Category and group label: the Kodokan group for throws; hold-down, choke or armlock for
    groundwork.
  - Where the technique appears in the syllabus.
  - A primary video plus up to 2 extras.
  - No notes. Only training forms carry a one-line description, and they are shown inline
    without a page of their own.
- **URLs**: `/nl/geel/o-soto-gari/` and `/en/yellow/o-soto-gari/`. A technique's page lives under
  the belt where it is **introduced**. Belts where it comes back later link to that page.
- **Spelling**: the Groeimodel's hyphenated style (O-soto-gari). Where the Groeimodel is
  inconsistent we pick one form; every deviation is logged in `SOURCE_NOTES.md`.
- **Legal**:
  - We republish only facts (names, belt and stage) plus our own translations.
  - The footer says "unofficial, not affiliated" and links to the source.
  - We take content down if Judo Vlaanderen asks.
  - We send a courtesy email to Judo Vlaanderen before launch.

## Videos

- Public YouTube videos, preferring official bodies (the Kodokan, the IJF, federations).
- We don't use Judo Vlaanderen's own Groeimodel-app videos. They are trainer-only material,
  recorded "uitsluitend voor opleidingsdoeleinden".
- **Curation**: candidates are proposed already checked for embeddability. The maintainer approves
  them with `approved: true` in the YAML, and only approved videos are shown.
- **Privacy**:
  - Pages show a local poster.
  - YouTube (youtube-nocookie.com) loads only after a tap.
  - There is always a "watch on YouTube" link as a fallback.
  - Optional start and end times play the relevant part of a longer video.
- **Launch rule**: a strict build fails while any technique has neither an approved video nor a
  `no_video_reason`.
- A weekly GitHub Action checks every video through YouTube oEmbed and opens an issue for any
  video that is removed or no longer embeddable.

## Language and UX

- Dutch and English.
  - The bare root sends visitors to the language they picked before, or else to the first of
    their browser languages that is Dutch or English (English if neither).
  - An NL | EN switch keeps you on the same page and remembers the choice in `localStorage`.
- Mobile-first, with belt colours as accents only.
  - Text on a belt colour is black or white, whichever has more contrast.
  - Light belt colours get an outline.
  - Light and dark mode follow the system setting.
- Coming in milestone 4:
  - Search over Japanese names (ignoring hyphens, spaces and macrons) and both translations,
    using an index built by Python.
  - Offline caching of all pages, and installing the app to the home screen.
- Name: **Obi**, with an original SVG placeholder logo (milestone 4).

## Technical

- **Python at build time only** (a static site generator):
  - PyYAML → pydantic models (per-entry rules) → cross-reference checks in `content.py` →
    Jinja2 templates → `_site/`.
  - All links are relative, so the site works under any base path.
- Plain JavaScript in the browser: no framework, no npm.
- uv and `pyproject.toml`, with ruff and pytest.
- GitHub Actions lints, tests and builds strictly on every push, then deploys `main` to GitHub
  Pages.
- A public repository, with the code under MIT. The `data/` folder is excluded from that licence.

## Milestones

1. **Vertical slice**: the yellow belt end to end, with approved videos, live on GitHub Pages.
2. The remaining belts' data and translations, and the "earlier belts" toggle.
3. Video curation for every item.
4. Polish: search, offline caching and install to home screen, an accessibility pass, the logo.
5. Launch, and the courtesy email to Judo Vlaanderen.
