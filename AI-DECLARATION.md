---
version: "0.1.2"
level: pair
processes:
  design: pair
  implementation: auto
  testing: copilot
  documentation: copilot
  review: pair
  deployment: none
components:
  pwa/index.html: auto
  pwa/server.py: auto
  skills/: copilot
  references/: copilot
---

This format is based on [AI-DECLARATION.md](https://ai-declaration.md/en/0.1.2/).

## Notes

- Mabs designed the project, defined the format spec, wrote the test
  scenarios, and made all design decisions (display budget, org-mode format,
  VISIBLE-driven step advancement, presenter voice).
- AI tools (Hermes Agent) generated draft skill text, PWA renderer
  code, and server code under that direction. All output was reviewed, tested,
  and refined by the human author.
- The `pwa/` code (renderer and server) was largely AI-generated (`auto`) with
  human direction and review.
- Skills and documentation were human-directed and AI-assisted (`copilot`) —
  the human wrote requirements, the AI drafted, the human refined.
- Design decisions (format, budget, modes, conventions) were paired — human
  and AI collaborating equally with the human understanding internals clearly.
- No AI tools were used for deployment (`none`).
