# Display Format Specification

**Version:** 1
**Status:** Draft

This document defines the org-mode display format — a structured file format for AI agents to write content that a companion renderer displays on a screen. The format is a subset of Emacs Org-mode, designed for unambiguous agent-to-renderer communication.

The format supports multiple display modes (immediate show, sequential reveal, side-by-side panes, slides, dashboards, cards) through `#+` directives and `:PROPERTIES:` drawers. A renderer that doesn't understand a mode falls back to showing everything — the file is always legible as plain text.

For the rationale behind choosing org-mode over markdown, JSON, YAML, or HTML, see [why-orgmode.md](why-orgmode.md).

## File Location

Default path: `display.org` in the PWA server directory.

The server serves this file at `/display.org`. Agents write to the file on disk; the PWA fetches it via HTTP.

The path is configurable via the `DISPLAY_FILE` environment variable when starting the server. Agents should be configured with the matching absolute path.

## Format Overview

The display format is org-mode with two extensions that serve as the agent-renderer API:

1. **`#+` directives** at the top of the file — configure the renderer (mode, columns, refresh interval)
2. **`:PROPERTIES:` drawers** on headings — attach metadata to sections (step order, pane assignment, timestamps)

Everything else is standard org-mode: headings, body text, lists, tables, source blocks, links.

## Minimal Valid File

```org
#+DISPLAY_MODE: show
#+FORMAT_VERSION: 1

* Content goes here
```

`#+DISPLAY_MODE:` and `#+FORMAT_VERSION:` are the only required directives. Everything else is optional.

## Display Budget

Agents should target an **80 characters × 20 lines** display grid (default budget). If the user explicitly asks for more detail ("show me more", "expand that", "give me the full version"), the agent may use an expanded budget of 160 characters × 40 lines. Always start with the default budget. Content that exceeds the budget forces the user to scroll, which defeats the purpose of a companion display.

Estimation rules:
- Each org heading costs 2 chars overhead (`* `) plus the heading text
- `:PROPERTIES:` drawers cost 3 lines (opening, properties, `:END:`)
- A blank line between sections costs 1 line
- A list item costs 1 line
- A paragraph of 3 sentences costs ~2–3 lines at 80 chars wide

When over budget, apply these strategies **in order**: (1) **hide** sections with `:VISIBLE: false` — data stays in the file and can be revealed later; (2) **summarise** verbose sections; (3) **restructure** (use tables, side-by-side, etc.); (4) **cut** content that is genuinely no longer relevant. The display is ephemeral — removing old content is acceptable, but hiding is preferred over deleting.

For `talk-through` mode, each step gets the full grid to itself. Aim for 2–4 lines of visible content per step, 3–6 steps total.

## Versioning

`#+FORMAT_VERSION: 1`

Increment when breaking changes occur. Renderers should check this value and reject or warn on unknown versions. Agents write the version they target. New agents can fall back to older versions by omitting newer directives.

## Top-level `#+` Directives

These appear before the first heading. They configure the renderer.

```
#+TITLE: Today's Schedule
#+DISPLAY_MODE: show
#+FORMAT_VERSION: 1
#+COLUMNS: 1
#+REFRESH: 0
#+ATTR_STYLE: background:#1a1a2e;color:#eee
#+ATTR_IMAGE: ./hero.png
```

| Directive | Values | Default | Purpose |
|---|---|---|---|
| `#+TITLE:` | plain text | *(none)* | Display title. Rendered as document heading. |
| `#+DISPLAY_MODE:` | `show`, `talk-through`, `side-by-side`, `slides`, `dashboard`, `card` | `show` | How the renderer presents the content |
| `#+FORMAT_VERSION:` | integer | `1` | Format contract version |
| `#+COLUMNS:` | integer 1–6 | `1` | Number of panes (used by `side-by-side` mode) |
| `#+REFRESH:` | seconds, `0` = never | `0` | Auto-refresh interval. For `dashboard` mode. |
| `#+ATTR_STYLE:` | CSS-like `key:value` pairs, semicolon-separated | *(none)* | Renderer styling hints |
| `#+ATTR_IMAGE:` | file path or URL | *(none)* | Hero image rendered after the title |
| `#+DISPLAY_FILE:` | absolute file path | *(server default)* | Override the display file location in the org content itself. Rarely needed — usually set via server config. |

## Display Modes

### `show` (default)

Immediate full display. All content visible at once. Content is static — the file is written once per request.

### `talk-through`

Sequential reveal. Sections have `:STEP:` properties. The renderer shows one step at a time, advancing on user action or automatically. The agent writes the entire file upfront; the renderer controls visibility.

See the [talk-through skill](skills/talk-through/SKILL.md) for usage.

### `side-by-side`

Multi-pane layout. Sections have `:PANE:` properties (1-indexed). `#+COLUMNS:` defines the number of panes. Sections without `:PANE:` default to pane 1.

```
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

### `slides`

Presentation mode. Each top-level heading becomes a slide. Speaker notes in `:NOTES:` properties.

```
#+DISPLAY_MODE: slides

* Introduction
  :PROPERTIES:
  :NOTES: Welcome everyone. Two minutes on this.
  :END:

* Key Finding
  ...
```

### `dashboard`

Live-updating view. The renderer re-reads the file at `#+REFRESH:` second intervals. Sections can have per-section `:REFRESH:` overrides. The agent (or a cron job) overwrites the file at the refresh interval.

```
#+DISPLAY_MODE: dashboard
#+REFRESH: 30

* System Status
  :PROPERTIES:
  :REFRESH: 10
  :END:

CPU: 34% | Memory: 6.2 GB / 16 GB | Disk: 45%

* Recent Events
  :PROPERTIES:
  :REFRESH: 60
  :END:

- 14:03 Deploy completed
- 13:58 Health check passed
```

### `card`

Single compact status card. One section, styled as a widget. For progress bars, stats, alerts.

```
#+DISPLAY_MODE: card
#+FORMAT_VERSION: 1

* Build Status
  :PROPERTIES:
  :ICON: 🔨
  :END:

3/5 tasks complete ▓▓▓▓░░░░
```

## Per-section `:PROPERTIES:` Keys

Properties attach to headings using org-mode drawer syntax:

```org
* Period 1 — Maths (8C)
  :PROPERTIES:
  :TIME: 09:00–09:50
  :ROOM: S4
  :STEP: 1
  :END:
```

| Property | Values | Used by | Purpose |
|---|---|---|---|
|| `:STEP:` | positive integer | `talk-through` | Reveal order. Sections shown in ascending order. |
| `:REVEAL:` | `next`, `auto`, `all` | `talk-through` | `next` = user advances. `auto` = timed. `all` = visible from start. |
|| `:VISIBLE:` | `true`, `false` | all modes | Whether the renderer shows this section. `false` = hidden (data stays in file). Default: `true`. **Only works on `*` heading sections** — cannot hide individual table rows, list items, or inline content. To make items toggleable, restructure them as separate `*` sections with their own `:PROPERTIES:` drawers. |
| `:PANE:` | positive integer (1-indexed) | `side-by-side` | Which column this section belongs to. |
| `:TIME:` | free text | `show`, `dashboard` | Timestamp or range for display |
| `:ROOM:` | free text | `show` | Room, location, or place identifier |
| `:NOTES:` | plain text | `slides` | Speaker notes, not shown on main display |
| `:REFRESH:` | seconds | `dashboard` | Per-section refresh override |
| `:COLLAPSED:` | `true`, `false` | all modes | Whether section body starts collapsed |
| `:ICON:` | emoji or icon name | all modes | Icon to display beside the heading |

Properties are free-form. Renderers should ignore properties they don't understand. Agents can add custom properties for custom renderers. This is how the format extends without version bumps.

## Content Formatting

Standard org-mode markup within section bodies:

- **Bold**: `*bold*`
- **Italic**: `/italic/`
- **Code**: `=verbatim=`
- **Links**: `[[https://example.com][Example]]` or `[[file:path][Local file]]`
- **Unordered lists**: `- item`
- **Ordered lists**: `1. item`
- **Tables**:

```org
| Name  | Score |
|-------+-------|
| Alice | 95    |
| Bob   | 87    |
```

- **Source blocks**:

```org
#+BEGIN_SRC python
print("hello")
#+END_SRC
```

- **Images**: `[[./image.png]]` or `[[https://example.com/img.png]]`

Renderers should handle at minimum: bold, italic, code, links, lists, and tables. Source blocks and images are optional quality-of-life features.

## Graceful Fallback

Every display file is valid org-mode. Even without a smart renderer:

- `cat display.org` — shows headings, properties, and body text
- `glow display.org` — renders with syntax highlighting (if org-mode is supported)
- Any org-mode viewer — full rendering

`#+` directives appear as human-readable headers. `:PROPERTIES:` drawers appear as structured metadata. A viewer that understands nothing still shows the headings and body text.

This is a design goal: **the file must be legible even without a renderer**.

## Extending the Format

Since `#+` keywords and `:PROPERTIES:` keys are open-ended:

1. **Agents can define new directives** — a renderer that doesn't understand them ignores them
2. **Agents can modify the renderer** — define `#+DISPLAY_MODE: timeline` and write the renderer code for it
3. **No spec change is needed** — new properties are just new keys that happen to be meaningful to an updated renderer

This co-evolution model is the key advantage: the format and the renderer grow together, and old files never break.
