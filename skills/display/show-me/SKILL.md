---
name: show-me
description: "Use when the user says 'show me', 'display', or 'put on screen'. Writes concise content to the display file within an 80×20 character budget (expandable to 160×40 on explicit user request). Keeps the agent's text/voice response brief and presenter-voiced."
version: 1.1.0
author: Marcus Berg, Cellia
license: MIT
tags: [display, output, companion-screen, org-mode, agent-pattern]
related_skills: [talk-through]
---

# Show Me

## Overview

When a user says "show me X", they want **detail on a screen** — not a long voice response or chat dump. This skill writes structured content to a display file and keeps the agent's conversational response brief and presenter-voiced.

The pattern: **agent writes content to the display file, then gives a short reply that owns the presentation**. The display is the agent's visual aid; the conversation is the summary.

## When to Use

- User says "show me", "display", "put on screen", "can I see", "what does X look like"
- Content is too detailed for a brief voice or chat response
- You want to separate **visual detail** from **conversational summary**

Don't use for:
- Simple answers that fit in a sentence or two
- Content the user needs to edit and save back (that's a wiki/write workflow)
- Sequential walkthroughs (use the `talk-through` skill instead)

## Display Budget

The display renders in an **80 characters × 20 lines** grid. This is the **default budget**. If the user explicitly asks for more detail ("show me more", "expand that", "give me the full version"), you may use an **expanded budget** of 160 characters × 40 lines. Always start with the default budget. You must estimate your content size and stay within the applicable budget. Content that exceeds the budget forces the user to scroll, which defeats the purpose.

### Estimation Rules

- Each org heading costs 2 chars overhead (`* `) plus the heading text
- `:PROPERTIES:` drawers cost 3 lines (opening, property lines, `:END:`)
- A blank line between sections costs 1 line
- A list item costs 1 line
- A paragraph of 3 sentences costs ~2–3 lines at 80 chars wide
- Total target: **no more than 3–4 sections, each fitting in ~4 lines**

### Choosing the Right Format

Pick the display format that presents information most densely within the budget:

| Content type | Best format | Why |
|---|---|---|
| Comparison (2+ items) | `side-by-side` with `:PANE:` | Columns let the reader scan across attributes |
| Comparison (many attributes) | Org table | Tables pack the most data per screen line |
| Schedule / list of items | `show` with sections | Each item gets a heading + properties |
| Sequential process | `talk-through` with `:STEP:` | Paced reveal, one step at a time |
| Status / metrics | `card` | Compact single-section widget |

When the user asks to compare things, start with `side-by-side` or a table — not bullet lists. Bullet lists are the least dense format and the most likely to blow the budget.

Example org table:
```
| Algorithm     | Best    | Average | Worst   | Stable |
|---------------+---------+---------+---------+--------|
| Merge sort    | O(n)    | O(n lg n) | O(n lg n) | Yes  |
| Quick sort    | O(n lg n) | O(n lg n) | O(n²)   | No   |
```

### What to Do When Over Budget

When content exceeds the budget, apply these strategies **in order**:

1. **Hide** sections with `:VISIBLE: false` — data stays in the file, renderer doesn't show it. The user can ask to reveal hidden sections later. Prefer this over deleting content.
2. **Summarise** — replace a 10-line explanation with a 2-line key point
3. **Restructure** — convert lists to tables, switch to `side-by-side` mode, combine sections
4. **Cut** — as a last resort, delete content that is no longer relevant

Do NOT just write more content and hope it fits. If you're over budget, rewrite until you're not.

## The Display File

### Path

**Default**: `display.org` in the PWA server directory. The PWA server serves it at `/display.org` via HTTP.

The display file is a scratchpad: the agent can freely create, edit, overwrite, and patch it without asking. No other file gets this treatment — see File Permissions below.

### Format

Org-mode with `#+` header directives. For the complete spec (all directives, properties, display modes), use `skill_view(name='show-me', file_path='references/format.md')`.

Minimum valid file:

```
#+DISPLAY_MODE: show
#+FORMAT_VERSION: 1

* Your content here
```

### Writing Rules

**"Show me" = overwrite** the file. Use `write_file` with the display file path. Always start fresh.

**"Add" or "update" = edit** the file. Use `patch` on the display file path. Preserve existing content, BUT remove old or irrelevant content freely. The display is not archival — restructuring to stay within budget is always correct.

**Voice/chat response stays brief and presenter-voiced.** Never read the display file aloud. The screen shows the detail; the conversation is the summary.

## The `:VISIBLE:` Property

Any section can have a `:VISIBLE:` property that controls whether the renderer shows it:

```org
* Historical Context
  :PROPERTIES:
  :VISIBLE: false
  :END:

Less relevant background info here.
```

| Value | Behaviour |
|---|---|
| `true` | Shown normally (default if `:VISIBLE:` omitted) |
| `false` | Hidden — renderer skips this section entirely |

Use `:VISIBLE: false` to:
- **Shrink the display** when adding new content — hide older content instead of deleting it, so the user can ask "show the detail on X" and you can patch `:VISIBLE: true`
- **Focus attention** — hide everything except the relevant section, then reveal on request
- **Preserve data** — keep calculations or source text in the file without cluttering the view

## Example: Schedule

User: "show me today's schedule"

```
#+TITLE: Today's Schedule
#+DISPLAY_MODE: show
#+FORMAT_VERSION: 1

* Period 1 — Maths (8C)
  :PROPERTIES:
  :TIME: 09:00–09:50
  :ROOM: S4
  :END:

Focus: fractions on a number line

* Period 2 — Science (7A)
  :PROPERTIES:
  :TIME: 09:50–10:40
  :ROOM: Lab 2
  :END:

Focus: erosion experiment

* Recess
  :PROPERTIES:
  :TIME: 10:40–11:00
  :END:
```

Reply: "Here's today's schedule."

## Example: Comparison (side-by-side)

User: "show me the difference between option A and option B"

```
#+TITLE: Plan Comparison
#+DISPLAY_MODE: side-by-side
#+COLUMNS: 2
#+FORMAT_VERSION: 1

* Option A — Gradual Rollout
  :PROPERTIES:
  :PANE: 1
  :END:

Week 1: Year 7
Week 2: Year 8
Week 3: Year 9

* Option B — Full Launch
  :PROPERTIES:
  :PANE: 2
  :END:

All year levels on day one.
Staff PD in week prior.
```

Reply: "Here's the comparison between gradual rollout and full launch."

## Example: Adding Content

User: "add an erosion experiment to that"

1. Patch the display file — add the experiment under the Science section.
2. Reply: "Added the erosion experiment to the Science section."

User: "that looks good, update the lesson plan"

This is now a **save-to-wiki** action — not a display action. Read the display file, then write to the original source file with explicit user approval.

## Example: Hiding Content

User: "show me just period 2"

Patch the display file to set `:VISIBLE: false` on the other sections:

```
* Period 1 — Maths (8C)
  :PROPERTIES:
  :VISIBLE: false
  :TIME: 09:00–09:50
  :ROOM: S4
  :END:

* Period 2 — Science (7A)
  :PROPERTIES:
  :TIME: 09:50–10:40
  :ROOM: Lab 2
  :END:
```

Reply: "Here's period 2 — Science in Lab 2."

User: "show all of them again"

Patch all sections back to `:VISIBLE: true`.

## Presenter Voice

You own what you create. Speak as the presenter, not as a technician pointing at a screen:

- ✅ "Here's the comparison." / "I've laid out the steps." / "This shows the key differences."
- ❌ "Up on your display…" / "The display shows…" / "Your screen now has…"

## File Permissions

- **The display file** (`display.org` in the PWA directory) — scratchpad. The agent creates, edits, overwrites, and patches freely. No approval needed.
- **All other files** — the agent must get explicit user approval before creating, editing, overwriting, patching, or modifying. This includes wiki files, journals, pages, config files, and any path outside the display file. Ask first. Wait for confirmation. Then act.

## Common Pitfalls

1. **Writing content to the chat response instead of the display file.** If the user said "show me", the detailed content goes to the display file. The chat/voice response is a 1–2 sentence summary only.

2. **Writing to the wrong path.** The display file must be in the PWA server directory as `display.org`. Check the agent's configuration.

3. **Exceeding the display budget.** If your content exceeds 80 chars × 20 lines, rewrite it. Cut sections, summarise, use `:VISIBLE: false`, or switch to a denser format (tables, side-by-side). If the user has explicitly asked for more detail, you may expand to 160×40, but always start with the default budget.

4. **Appending on a "show me" trigger.** "Show me" always overwrites. "Add" or "update" edits in place. Getting this wrong means stale content from a previous request persists.

5. **Overwriting on a modification trigger.** If the user says "add X" or "update Y", use `patch` not `write_file`. Overwriting destroys their previous display. Exception: if the content needs restructuring to fit the budget, rewriting is fine.

6. **Reading the display file aloud.** The point is visual offload. The conversation is brief; the display is detailed. Never echo display content in the chat response.

7. **Preserving old content out of obligation.** The display is ephemeral. If old content is irrelevant, remove it. If you're not sure, hide it with `:VISIBLE: false` rather than keeping it visible.

8. **Using markdown format.** The display file is org-mode. Use `*` for headings (not `#`), `#+` for directives (not YAML frontmatter), and `:PROPERTIES:` drawers (not HTML comments). (YAML frontmatter in this SKILL.md is a Hermes skill descriptor convention — display files use `#+` directives instead.)

9. **Using `:VISIBLE:` on table rows or inline content.** The `:VISIBLE:` property only works on `*` heading sections. If you need to filter rows in a table, rewrite the table content instead. To make individual items toggleable, restructure them as separate `*` sections with their own `:PROPERTIES:` drawers.

10. **Deleting content instead of hiding it.** When adding new content that exceeds the budget, hide older sections with `:VISIBLE: false` first. The user can ask to see them again. Only cut content that is genuinely no longer relevant.

## Verification Checklist

- [ ] File path matches the PWA server's display file location
- [ ] File starts with `#+DISPLAY_MODE: show` and `#+FORMAT_VERSION: 1`
- [ ] Content fits within 80 chars × 20 lines budget
- [ ] Used `write_file` for "show me" triggers (overwrite)
- [ ] Used `patch` for "add/update" triggers (edit in place)
- [ ] Used `:VISIBLE: false` to hide non-essential content when over budget
- [ ] Conversational response is 1–2 sentences, presenter-voiced
- [ ] No display content echoed in chat
- [ ] No content written to paths other than the display file without approval
- [ ] Format is org-mode, not markdown
