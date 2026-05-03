# Display Skills for AI Agents

This project provides skills for AI agents that write structured content to a companion display (browser PWA). The agent handles content generation; the PWA handles rendering.

## Quick Start

1. **Start the PWA server:**
   ```bash
   cd pwa && python3 server.py
   ```
   Opens on `http://localhost:8907`. Set `PORT` and `HOST` env vars to customise.

2. **Point your agent at the display file:**
   The PWA server reads `pwa/display.org` by default. Set `DISPLAY_FILE` env var to override.

   For Hermes Agent, add these skills to your profile's `skills/` directory:
   ```bash
   # From your profile directory (e.g. ~/.hermes/profiles/my-profile/)
   cp -r skills/display/ ~/.hermes/profiles/my-profile/skills/display/
   ```

3. **Try it:**
   - "show me a comparison of sorting algorithms" → triggers `show-me`
   - "walk me through how DNS resolution works" → triggers `talk-through`

## Structure

```
.
├── AGENTS.md              ← You are here. Project overview + deployment guide.
├── README.md              ← Human-readable introduction
├── why-orgmode.md         ← Rationale for choosing org-mode over markdown
├── pwa/
│   ├── server.py          ← Python stdlib HTTP server (no dependencies)
│   ├── index.html         ← Self-contained PWA renderer
│   ├── display.org        ← The display file (auto-created, gitignored)
│   ├── manifest.json      ← PWA manifest
│   └── sw.js              ← Service worker for offline
└── skills/display/
    ├── references/
    │   └── format.md      ← Full org-mode display format specification
    ├── show-me/
    │   └── SKILL.md        ← "Show me X" — write content to display
    └── talk-through/
        └── SKILL.md        ← "Walk me through X" — sequential reveal
```

## Skills

### show-me
Trigger: "show me", "display", "put on screen"

Writes detailed content to the display file. "Show me" overwrites; "add/update" patches in place. Keeps chat responses brief (1–2 sentences).

### talk-through
Trigger: "walk me through", "explain step by step", "tell me about"

Writes all steps upfront with `:STEP:` and `:VISIBLE:` properties. Patches visibility to advance between steps. Each step fits in the display budget (80×20 chars, expandable to 160×40 on request).

### Format Reference
The complete display format spec is available as a skill reference file:
```
skill_view(name='show-me', file_path='references/format.md')
```
This is loaded on demand, not in every prompt.

## Display File Conventions

- **Path:** `pwa/display.org` (relative to project root, configurable via `DISPLAY_FILE` env var)
- **Format:** Org-mode with `#+` directives and `:PROPERTIES:` drawers
- **Budget:** 80 characters × 20 lines (default). Expandable to 160×40 when the user explicitly requests more detail. Agents must estimate content size and stay within the applicable budget.
- **Ephemeral:** The display file is a scratchpad. Agents freely overwrite, patch, shrink, and cut content.

## Deploying with an Agent Profile

### Option A: Run from this directory (simplest)

Set your agent's working directory to this project root. The display file is at `pwa/display.org` relative to cwd.

For Hermes Agent, set in your profile's `config.yaml`:
```yaml
terminal:
  cwd: /path/to/display-skills
```

Add to your SOUL.md:
```
Display file: pwa/display.org (relative to workdir)
PWA server: cd pwa && python3 server.py
```

### Option B: Copy into an existing profile

Copy the `skills/display/` directory into your profile's skills:
```bash
cp -r skills/display/ ~/.hermes/profiles/my-profile/skills/display/
```

Then set the absolute display file path in your SOUL.md:
```
Display file: /absolute/path/to/display-skills/pwa/display.org
```

Start the PWA server from the project root:
```bash
cd /path/to/display-skills/pwa && python3 server.py
```

## SOUL.md Template

Add these directives to your agent's SOUL.md. Adjust paths for your setup:

```markdown
## Display File

- Path: {relative or absolute path to pwa/display.org}
- Always use org-mode format with `#+` directives
- "Show me" = overwrite (`write_file`)
- "Add/update" = edit in place (`patch`)
- Never read display content aloud in chat

## Display Budget

The display is 80 characters wide by 20 lines tall. This is the **default budget**. If the user explicitly asks for more detail ("show me more", "expand that", "give me the full version"), the agent may use an expanded budget of 160 characters × 40 lines. Always start with the default budget.

- Each org heading costs 2 chars overhead (`* `) plus text
- `:PROPERTIES:` drawers cost 3 lines
- A blank line between sections costs 1 line
- A list item costs 1 line
- A paragraph of 3 sentences costs ~2–3 lines at 80 chars wide
- Target: 3–4 sections, each fitting in ~4 lines

If content exceeds the budget, cut or summarise. Remove old or irrelevant content freely.

## Presenter Voice

You own what you create. Speak as the presenter:
- ✅ "Here's the comparison." / "I've laid out the steps."
- ❌ "Up on your display…" / "The display shows…"

## Editing Philosophy

The display file is a scratchpad. Rewrite, shrink, restructure, or cut content whenever it helps the user. Do not preserve old content out of obligation.
```

## PWA Server

```bash
cd pwa && python3 server.py
```

Environment variables:
- `DISPLAY_FILE` — path to display.org (default: `pwa/display.org` in the script's directory)
- `PORT` — HTTP port (default: 8907)
- `HOST` — bind address (default: 0.0.0.0)

The PWA server:
- Serves static files from `pwa/`
- Serves `display.org` with no-cache headers
- Pushes updates to browsers via SSE (`/api/events`)
- Auto-creates `display.org` if missing

## Extending

### New Display Modes

Define a `#+DISPLAY_MODE:` value and write the renderer code in `pwa/index.html`. The format spec is open-ended — `#+` directives and `:PROPERTIES:` keys that a renderer doesn't understand are ignored. No spec change needed.

### New Skills

Create a new skill directory under `skills/display/`:
```
skills/display/my-skill/SKILL.md
skills/display/my-skill/references/...   ← optional
```

Set `related_skills` in the YAML frontmatter to link it to existing skills.

### New Properties

Add any `:PROPERTIES:` key to your org sections. Unknown properties are ignored by renderers that don't support them. This is how the format grows without version bumps.