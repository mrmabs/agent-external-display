# Preamble (non-AI)

The majority of this repo was AI generated, and this project has been shared to allow others to look at it and build on what I have. I am also working to build supporting infrastructure on this to support voice interactivity, and making the "chat" session essentially a hidden debug stream.

The inspiration for the larger project combines my own thoughts on creating an interactive user interface like in the [Apple Knowledge Navigator](https://www.youtube.com/watch?v=umJsITGzXd0) demo, and a "software defined interface" as [described by Michael Okuda in conversation with Adam Savage](https://youtu.be/D24tYFIVyv0?t=228) about LCARS in Star Trek: The Next Generation.

I won't be actively reviewing PRs, but you are welcome to fork and enjoy.

Below here, I have minimal input; which is mostly intertwined with AI-generated content.

-----

# Display Skills

Agent skills for writing structured content to a display file that a companion renderer presents on a screen. The agent handles detail; the conversation stays brief.

## Problem

When an AI agent has detailed content to share — schedules, comparisons, walkthroughs, code reviews — dumping it all into a chat or voice response is the wrong approach. The user wants **visual detail on a screen** and a **brief summary in conversation**.

These skills define how an agent writes that content: what file, what format, what semantics.

## Approach

### Two channels

- **Display file** (`display.org` in the PWA directory) — detailed, structured, formatted for a screen. The agent writes to this file; a renderer displays it.
- **Conversational response** — brief, 1–2 sentences. No echoing of display content.

### Org-mode format

The display file uses a subset of Emacs Org-mode. `#+` directives configure the renderer (mode, columns, refresh). `:PROPERTIES:` drawers attach metadata to sections (step order, pane assignment, timestamps). This is unambiguous, extensible, and readable without a renderer.

See [why-orgmode.md](why-orgmode.md) for the full rationale, or [skills/display/references/format.md](skills/display/references/format.md) for the format specification.

## Skills

### show-me

**Trigger:** "show me", "display", "put on screen", "can I see"

The core display skill. Write detailed content to the display file, keep the conversation brief. Overwrite on "show me", patch on "add/update".

```org
#+TITLE: Today's Schedule
#+DISPLAY_MODE: show
#+FORMAT_VERSION: 1

* Period 1 — Maths (8C)
  :PROPERTIES:
  :TIME: 09:00–09:50
  :ROOM: S4
  :END:

Focus: fractions on a number line
```

Supports `side-by-side` mode for comparisons:

```org
#+DISPLAY_MODE: side-by-side
#+COLUMNS: 2

* Option A
  :PROPERTIES:
  :PANE: 1
  :END:

* Option B
  :PROPERTIES:
  :PANE: 2
  :END:
```

→ [skills/display/show-me/SKILL.md](skills/display/show-me/SKILL.md)

### talk-through

**Trigger:** "walk me through", "explain step by step", "tell me about", "take me through"

Sequential reveal. The agent writes the entire file upfront with `:STEP:` properties on each section. The renderer shows one step at a time. The agent narrates the current step conversationally — one key point per step, then advances.

```org
#+TITLE: The Water Cycle
#+DISPLAY_MODE: talk-through
#+FORMAT_VERSION: 1

* Introduction
  :PROPERTIES:
  :REVEAL: all
  :END:

The water cycle is the continuous movement of water.

* Evaporation
  :PROPERTIES:
  :STEP: 1
  :END:

The sun heats water in oceans and lakes.

* Condensation
  :PROPERTIES:
  :STEP: 2
  :END:

Water vapour rises and cools into clouds.
```

→ [skills/display/talk-through/SKILL.md](skills/display/talk-through/SKILL.md)

## Format Specification

The shared org-mode format spec lives in [skills/display/references/format.md](skills/display/references/format.md). It defines:

- `#+` directives (configuring renderer mode, columns, refresh, styling)
- `:PROPERTIES:` drawers (per-section metadata: step, pane, time, notes)
- Six display modes: `show`, `talk-through`, `side-by-side`, `slides`, `dashboard`, `card`
- Content formatting (bold, italic, code, links, lists, tables, source blocks, images)
- Graceful fallback (always readable as plain text)

Both skills reference this spec. New skills (slides, dashboard, card) would use the same format.

## Project Structure

```
agent-external-display/
├── README.md                          ← you are here
├── AI-DECLARATION.md                  ← AI involvement declaration
├── LICENCE                            ← MIT licence
├── why-orgmode.md                     ← format rationale
├── references/
│   └── display-format.md              ← org-mode spec for display files
├── skills/
│   ├── show-me/
│   │   └── SKILL.md                   ← core display output skill
│   └── talk-through/
│       └── SKILL.md                   ← sequential reveal skill
└── pwa/
    ├── server.py                      ← stdlib Python HTTP server
    ├── index.html                     ← self-contained PWA renderer
    ├── manifest.json                  ← PWA manifest
    ├── sw.js                          ← service worker
    └── display.org                    ← display file (auto-created on start)
```

## Quick Start

1. Start the PWA server:
   ```bash
   cd agent-external-display/pwa && python3 server.py
   ```
2. Open `http://localhost:8907` in a browser
3. Write display content to `agent-external-display/pwa/display.org` (by hand, or from an agent using the `show-me` / `talk-through` skills)
4. The PWA auto-refreshes when the file changes

## Renderers

The format is renderer-agnostic. Any program that watches the display file and renders org-mode content works:

- **PWA** (included): `cd pwa && python3 server.py` — serves the display file and a full renderer at `http://localhost:8907`
- **Terminal**: `cat display.org` or `glow display.org` (basic, no mode support)
- **`entr` watcher**: `ls display.org | entr -c glow display.org` (auto-refresh on file change)
- **Custom**: Parse `#+` directives and `:PROPERTIES:` drawers, render according to mode. The spec is small enough to implement in an afternoon.

Since the agent can also modify the renderer, new display modes can be defined as needed. Define `#+DISPLAY_MODE: timeline`, write the renderer to support it, and the format has grown without a spec change.

## Extending

The format is designed for co-evolution. To add a new capability:

1. Define new `#+` directives or `:PROPERTIES:` keys in your skill
2. Update your renderer to handle them
3. Publish the skill — renderers that don't understand the new directives ignore them

Future skill ideas:
- **slides** — presentation mode (top-level headings = slides, `:NOTES:` = speaker notes)
- **dashboard** — live-updating views with `#+REFRESH:` intervals
- **card** — single compact status card (progress, stats, alerts)
- **images** — embedding generated or linked images in display content

## AI Declaration

[![AI-DECLARATION: pair](https://img.shields.io/badge/䷼%20AI--DECLARATION-pair-ffedd5?labelColor=ffedd5)](https://ai-declaration.md)

This project uses [AI-DECLARATION.md](https://ai-declaration.md/en/0.1.2/) to declare AI involvement. See [AI-DECLARATION.md](AI-DECLARATION.md) for the full breakdown by process and component.

**Copyright and licensing status may vary by jurisdiction.** Some jurisdictions do not recognise copyright of AI-generated output, or apply different rules to works produced with AI assistance. Where local law holds that this content is not copyrightable or is subject to different rules, those laws take precedence over the MIT licence below. In jurisdictions where the content is copyrightable, it is licensed under the MIT licence as stated.

Personal issues with AI-generated content aside, this decision was taken as PD/CC0 may be complicated by the copyrights of contributions to the model used to create the code; and GPL variants may also be completely incompatible with those. I have no plans to defend the licence of any AI generated code, MIT is literally a best fit placeholder.

## Licence

This project is licensed under the [MIT Licence](LICENCE).
