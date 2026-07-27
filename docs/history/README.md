# Historical documents

These files record how the project was planned and audited earlier. They are
**superseded** and kept only for context — they do *not* describe the current
codebase and should not be used to orient new work.

For the current, accurate picture use:

- [`../../.agents/AGENTS.md`](../../.agents/AGENTS.md) — the durable operating guide.
- [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md) — verified layer-by-layer state.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — the current small-layer structure.
- The source code and tests, which are always authoritative.

## What's in here

| File | What it was | Why it's stale |
| --- | --- | --- |
| `00_initial_plan.md` | The original v1.0 project plan. | Assumes Pillow/BiDi pixel rendering and dual JPEG+PNG output, both abandoned. |
| `01_phase2_data_pipeline_plan.md` | The data-pipeline work plan. | That work is now implemented and re-architected; its "pending" checkboxes no longer reflect reality. |
| `99_folder_structure.md` | An early folder-structure map. | Lists modules that no longer exist and files described as "to be created" that now exist. |
| `REFACTOR_AUDIT.md` | A pre-refactor audit of blockers. | Its findings (no runnable product path, renderer stub, token stubs) were all resolved during the refactor. |

The architecture actually shipped is **HTML/CSS + Playwright**, saving a single
1080x1920 PNG. See `.agents/AGENTS.md` and `docs/ARCHITECTURE.md` for the real
design.
