# Why Org-mode

When building a display output system for AI agents, the format choice matters more than it seems. The display file is a contract between two things the agent controls: the **writer** (the skill that generates content) and the **renderer** (the program that displays it). Both need to understand the format unambiguously.

We chose a subset of Emacs Org-mode. Here's why.

## The Alternatives

### Markdown

Markdown is the obvious first choice — it's everywhere, every renderer handles it, and every LLM emits it by default. But markdown has real problems as an agent-to-renderer contract:

- **No standard metadata.** YAML frontmatter (the `---` block at the top) is a GitHub convention, not part of any markdown spec. Renderers parse it inconsistently or not at all.
- **No section-level properties.** There's no standard way to attach metadata like "this section is step 3" or "this section goes in pane 2" to a heading. Hacky workarounds exist (HTML comments, `<details>` tags), but they're brittle and renderer-specific.
- **Ambiguous nesting.** Nested lists, code blocks inside lists, and links inside other constructs all create parser edge cases. Every markdown renderer handles these differently.
- **No extensibility point.** You can't define new directives. Want to tell the renderer "this is a talk-through, reveal one step at a time"? You'd need a separate config file or a custom markdown extension — and now you have two formats to maintain.

For simple static documents, markdown is fine. For a programmatic contract between an agent and a renderer that need to agree on layout, mode, and metadata, it's the wrong tool.

### JSON

JSON is unambiguous and machine-parseable, but it's hostile to human readability. A display file should be legible in a terminal (`cat` or `glow`). JSON doesn't render headings, lists, or emphasis — it renders as a data blob. The agent is writing content for humans to read, not just data for a renderer to parse.

### YAML

YAML is human-readable and supports nested structures, but its parsing rules are notoriously complex. Multi-line strings in YAML are painful. Indentation errors cause silent failures. And like JSON, it's data-first — you'd need a separate field for the "rendered content" portion, creating a split between structure and prose.

### HTML

HTML with `data-` attributes could do everything we need — metadata, layout, styling. But it's verbose, error-prone for agents to generate correctly, and unreadable as raw text. An agent writing HTML has to juggle closing tags, attribute quoting, and nested elements. A `cat` of an HTML file is not pleasant reading.

## What Org-mode Gets Right

Org-mode is a 20-year-old plain text format from the Emacs ecosystem. It's been through the standardisation process. Multiple independent parsers exist. It solves the specific problems we have:

### `#+` directives for top-level config

```
#+TITLE: Today's Schedule
#+DISPLAY_MODE: talk-through
#+COLUMNS: 2
#+FORMAT_VERSION: 1
```

These are unambiguous key-value pairs at the top of the file. Any parser can read them. They serve the same role as YAML frontmatter, but they're **part of the org-mode spec** — not a convention bolted on.

This is our API surface: the renderer reads `#+DISPLAY_MODE:` and switches layout. The agent writes it. New modes are just new `#+` keywords — no spec change needed, no new file format.

### `:PROPERTIES:` drawers for section metadata

```
* Evaporation
  :PROPERTIES:
  :STEP: 1
  :REVEAL: next
  :TIME: 09:00
  :END:

Content here.
```

Properties attach structured metadata to any heading. This is where we put step numbers, pane assignments, timestamps, and display hints. It's built into the format — no HTML comments, no frontmatter hacks, no sidecar JSON.

### Content is first-class

The body of a section is just text with org-mode markup (`*bold*`, `/italic/`, `=code=`, `[[link][description]]`, lists, tables). It renders well in terminals, in `glow`, and in org-mode viewers. You can `cat` the file and read it. The metadata doesn't pollute the content.

### Extensibility without forking

`#+` keywords and `:PROPERTIES:` keys are open-ended. If we need `#+ATTR_STYLE:` tomorrow, we add it. If we need `:COLLAPSED: true`, we add it. Renderers that don't understand a directive ignore it. The format grows organically without breaking existing files.

This is critical because **the agent can modify the renderer**. If the agent writes a PWA renderer (or a terminal watcher, or an Unreal Engine integration), it can define new directives and implement them in the same pass. The format and renderer co-evolve.

### The escape hatch

Every org-mode file is readable as plain text. If a renderer doesn't understand `#+DISPLAY_MODE: talk-through`, it shows everything — headings, property drawers, body text. The content is never locked behind a parser. `:PROPERTIES:` drawers are visible and human-readable even without rendering.

This is the design goal: **the file must be legible even without a renderer**.

## What We're Not Using

This is a subset of org-mode. We don't use:

- `#+SETUPFILE`, `#+INCLUDE`, `#+MACRO` — these are Emacs-specific features that add complexity without benefit for our use case
- Clocking, logging, TODO state machines — these are for task management, not display
- Inline source block evaluation (`<<elisp>>`) — we're not executing code in the display file
- LaTeX fragments — if needed, they'd be rendered by the viewer, not the format

We use: `#+` keywords, `:PROPERTIES:` drawers, headings, body text with basic markup, tables, source blocks, and links. That's enough to express display modes, layout, sequencing, and rich content — without pulling in the weight of full Emacs org-mode.

## Summary

| Requirement | Markdown | JSON | YAML | HTML | Org-mode |
|---|---|---|---|---|---|
| Human-readable raw text | ✅ | ❌ | ✅ | ❌ | ✅ |
| Standard top-level metadata | ❌ (convention) | ✅ | ✅ | ✅ (data-) | ✅ (#+) |
| Section-level properties | ❌ | ✅ | ✅ | ✅ (data-) | ✅ (drawers) |
| Extensible without forking | ❌ | ✅ | ✅ | ✅ | ✅ |
| Simple parser | ❌ (edge cases) | ✅ | ❌ (complex) | ❌ (tag soup) | ✅ |
| Content and config in one file | ✅ (messy) | ❌ | ❌ | ✅ (ugly) | ✅ |
| `cat`-readable without renderer | ✅ | ❌ | ✅ | ❌ | ✅ |
| Agent-friendly to generate | ✅ | ✅ | ❌ | ❌ | ✅ |

Org-mode hits every requirement. The others miss at least one critical need. For an agent-to-renderer contract where both sides are programmable and the format needs to grow over time, org-mode with `#+` directives and `:PROPERTIES:` drawers is the right tool.
