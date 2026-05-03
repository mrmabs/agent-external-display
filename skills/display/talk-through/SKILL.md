---
name: talk-through
description: "Use when the user says 'walk me through', 'explain step by step', or 'tell me about X'. Writes a sequenced display file within 80×20 budget (expandable to 160×40 on request), delivering each step verbally as the display advances."
version: 1.1.0
author: Marcus Berg, Cellia
license: MIT
tags: [display, output, sequential, reveal, explanation, walkthrough, org-mode, agent-pattern]
related_skills: [show-me]
---

# Talk Through

## Overview

When a user says "walk me through X" or "explain how Y works", they want **guided understanding** — not a wall of text and not a one-shot display. This skill writes a sequenced display file where each section has a step number, then delivers the steps one at a time as the conversation advances.

The `talk-through` mode is for **teaching, explaining, and reviewing**. The agent prepares all steps upfront in the display file, but uses `:VISIBLE:` properties to control which steps are shown. The agent's conversational response corresponds to the current step.

This is the structured version of "what about…?" — where the agent talks through content rather than just showing it.

## When to Use

- User says "walk me through", "explain step by step", "tell me about", "take me through", "what about"
- Content has a natural sequence (processes, timelines, analyses, reviews)
- The user benefits from paced delivery rather than seeing everything at once
- The agent wants to annotate or narrate alongside visual content

Don't use for:
- Simple lookups that need one answer (use `show-me`)
- Yes/no questions
- Content where order doesn't matter (just use `show-me` with `#+DISPLAY_MODE: show`)

## Display Budget

The display renders in an **80 characters × 20 lines** grid (default budget). If the user explicitly asks for more detail ("show me more", "expand that", "give me the full version"), you may use an **expanded budget** of 160 characters × 40 lines. Always start with the default budget. Each step must fit within the applicable budget — the user sees one step at a time, so the entire grid space is available per step.

### Estimation Rules

- Each org heading costs 2 chars overhead (`* `) plus the heading text
- `:PROPERTIES:` drawers cost 3 lines (opening, property lines, `:END:`)
- A blank line between sections costs 1 line
- A list item costs 1 line
- A paragraph of 3 sentences costs ~2–3 lines at 80 chars wide
- Per step: aim for **2–4 lines of visible content** (heading + body + spacing)
- Total steps: aim for **3–6 steps** in a talk-through

If a step exceeds the budget, summarise it. If you have too many steps, combine related ones. The talk-through should be a curated walkthrough, not a comprehensive document.

## How It Works

1. **Agent writes the entire file at once** with all steps numbered via `:STEP:` properties.
2. **Only the current step (and `:REVEAL: all` sections) have `:VISIBLE: true`.** All other steps start with `:VISIBLE: false`.
3. **Agent delivers a brief verbal response** for the current step.
4. **When the user says "next"** (or "continue", "and then?"), the agent patches the display file: set current step to `:VISIBLE: false`, set next step to `:VISIBLE: true`.
5. **Renderer shows the newly visible step.** Agent responds for that step.
6. Repeat until all steps are shown.

This means each patch changes exactly two `:VISIBLE:` values — surgical, fast, no risk of content loss.

## The Display File

### Path and Format

Same as `show-me`: the display file (`display.org` in the PWA server directory), org-mode format with `#+` directives.

The key differences from `show-me`: `#+DISPLAY_MODE: talk-through`, `:STEP:` properties on sections, and `:VISIBLE:` to control which step is shown.

### Writing Rules

**Initial write:** Use `write_file` to create the full talk-through file. All steps are present, but only the first step is `:VISIBLE: true`. All subsequent steps have `:VISIBLE: false`.

**Advancing steps:** Use `patch` to flip `:VISIBLE:` values. Set the current step to `:VISIBLE: false` and the next step to `:VISIBLE: true`. This is a minimal, surgical edit — not a rewrite.

**If the user asks to start a new topic:** Use `write_file` to overwrite with the new content.

**If the user asks to go back:** Patch the current step to `:VISIBLE: false` and the requested step to `:VISIBLE: true`.

## The `:VISIBLE:` Property for Step Control

In `talk-through` mode, `:VISIBLE:` is the primary mechanism for controlling what the renderer shows:

```org
* Introduction
  :PROPERTIES:
  :REVEAL: all
  :END:

The water cycle is the continuous movement of water.

* Evaporation
  :PROPERTIES:
  :STEP: 1
  :VISIBLE: true
  :END:

The sun heats water in oceans and lakes.

* Condensation
  :PROPERTIES:
  :STEP: 2
  :VISIBLE: false
  :END:

Water vapour rises and cools into clouds.

* Precipitation
  :PROPERTIES:
  :STEP: 3
  :VISIBLE: false
  :END:

Water falls as rain, snow, sleet, or hail.
```

When the user says "next", patch:
- Step 1: `:VISIBLE: true` → `:VISIBLE: false`
- Step 2: `:VISIBLE: false` → `:VISIBLE: true`

This is more robust than relying on the renderer to track step state — the file itself is the source of truth.

## Example: Explaining a Process

User: "walk me through the water cycle"

1. Write the display file:

```
#+TITLE: The Water Cycle
#+DISPLAY_MODE: talk-through
#+FORMAT_VERSION: 1

* Overview
  :PROPERTIES:
  :REVEAL: all
  :END:

The water cycle is the continuous movement of water through the atmosphere, land, and oceans.

* Evaporation
  :PROPERTIES:
  :STEP: 1
  :VISIBLE: true
  :END:

The sun heats water in oceans and lakes. Water molecules gain enough energy to escape the liquid surface and become water vapour.

Key points:
- Oceans provide ~86% of atmospheric moisture
- Temperature drives the rate of evaporation

* Condensation
  :PROPERTIES:
  :STEP: 2
  :VISIBLE: false
  :END:

Water vapour rises and cools. It condenses around dust particles to form tiny water droplets — visible as clouds.

* Precipitation
  :PROPERTIES:
  :STEP: 3
  :VISIBLE: false
  :END:

When water droplets in clouds combine and grow heavy enough, they fall as rain, snow, sleet, or hail.

* Collection
  :PROPERTIES:
  :STEP: 4
  :VISIBLE: false
  :END:

Water returns to Earth's surface. It collects in rivers, lakes, oceans, and groundwater.
```

2. Reply: "The first step is evaporation — the sun heats water until it becomes vapour."

3. User: "next" → Patch step 1 to `:VISIBLE: false`, step 2 to `:VISIBLE: true`. Reply: "Now condensation — the vapour cools as it rises and forms clouds."

4. Continue until all steps are delivered.

## Step Ordering

- Steps are numbered starting from 1 (ascending order)
- The renderer shows steps in order: 1, then 2, then 3, etc.
- Gaps are fine: steps 1, 2, 5 are valid — steps 3 and 4 simply don't exist
- Sections without `:STEP:` are always visible (background context, introductions, summaries)
- Use `:REVEAL: all` for sections that should be visible from the start (title, introduction, summary)

## Reveal Modes

The `:REVEAL:` property on a section controls how it appears:

| Value | Behaviour |
|---|---|
| `next` | Shown when its step is reached, hidden before. The default for `:STEP:` sections. |
| `auto` | Shown for a timed duration, then advances. Renderer determines timing. |
| `all` | Always visible, regardless of step. Use for titles, introductions, summaries. |

If `:REVEAL:` is omitted on a `:STEP:` section, it defaults to `next`.

**Note:** `:VISIBLE:` overrides `:REVEAL:` for rendering purposes. A section with `:REVEAL: all` but `:VISIBLE: false` will not be shown. This lets you hide even background sections temporarily.

## Presenter Voice

You own what you present. Speak as the presenter, not as a narrator of a screen:

- ✅ "The first step is evaporation." / "Now condensation happens." / "Let's look at how the water returns."
- ❌ "The display now shows evaporation." / "On your screen you can see…" / "The next slide shows…"

## Editing Philosophy

The display file is a scratchpad. If content needs restructuring to fit the budget, rewrite it. If a step is no longer relevant, remove it. If the user wants to skip ahead or go back, patch `:VISIBLE:` values accordingly.

## Graceful Fallback

If the renderer does not support `talk-through` mode, it falls back to `show` — displaying all content at once. The content is still valid org-mode. Steps become regular headings, and `:VISIBLE:` properties appear as readable metadata.

This means **the file is always useful even without a smart renderer**. A `cat` or `glow` of the file shows all steps in order, and the `:STEP:` and `:VISIBLE:` properties appear as structured data.

## Combining with Voice

For voice-first agents (like a classroom assistant):

1. Agent writes the full file (all steps at once, only step 1 visible)
2. Agent gives a brief voice response for the current step
3. User says "next" → agent patches `:VISIBLE:` and responds with the next step
4. Voice responses follow the same brevity rules as `show-me`

**Never read the display file content aloud.** The screen shows detail; the voice narrates the key point.

## Common Pitfalls

1. **Writing one step at a time.** Write the entire file upfront. Patch `:VISIBLE:` to reveal steps progressively. Writing step-by-step means the user can't look ahead or go back.

2. **Missing `:STEP:` properties.** Without step numbers, the renderer can't order the reveal. Every section that should appear progressively needs a `:STEP:` number.

3. **Missing `:VISIBLE:` properties.** Without `:VISIBLE:`, the renderer has to guess what to show. Be explicit: set the current step to `:VISIBLE: true` and all others to `:VISIBLE: false`.

4. **Rewriting the entire file on each step advance.** Only patch `:VISIBLE:` values. The file structure stays intact. Rewriting risks losing content and is slower.

5. **Forgetting `:REVEAL: all` on introductory sections.** The overview or introduction should be visible from the start. Without `:REVEAL: all`, the introduction won't appear until its step number.

6. **Echoing display content in the chat response.** The display shows the detail. The conversation is the narration. One key point per step, 1–2 sentences.

7. **Not providing a mental map before starting.** Begin with a brief overview of what the walkthrough covers, then advance. Don't jump into step 1 without context.

8. **Exceeding the display budget per step.** Each step must fit in 80×20 chars (or 160×40 if expanded). If a step is too detailed, summarise it. The talk-through is a curated walkthrough, not a textbook chapter.

9. **Numbering steps out of order.** `:STEP:` values must be in ascending order for the sections you want revealed. The renderer shows them 1 → 2 → 3.

## Verification Checklist

- [ ] File path matches the PWA server's display file location
- [ ] `#+DISPLAY_MODE: talk-through` is set
- [ ] `#+FORMAT_VERSION: 1` is set
- [ ] Each progressive section has a `:STEP:` property with ascending number
- [ ] Current step has `:VISIBLE: true`, all others have `:VISIBLE: false`
- [ ] Introductory or always-visible sections have `:REVEAL: all`
- [ ] Each step fits within 80 chars × 20 lines budget
- [ ] Total steps are 3–6 (combine if more)
- [ ] File was written once with `write_file`, then patched for advances
- [ ] Conversational response is brief — one key point per step, presenter-voiced
- [ ] No display content echoed in the chat/voice response
