# Project instructions

Small local CLI for preparing AWS and Anthropic badge rasters for manual vectorization.
Use uv, hatchling, Typer, Rich, Pillow, strict Pyright, Ruff, and pytest.
Pillow is the image-processing dependency; add other runtime libraries only when needed.

## Scope

Prepare one image or a flat directory: crop transparent margins, resize proportionally
onto a transparent square, export a palette. Export manually selected text regions
for manual upload to font-matching services. No tracing engine, OCR, background removal,
external API, automatic upload, or web UI in this version. Raster font matches are
candidates requiring visual comparison, not guaranteed identifications.

## Structure

```text
.cspell/                 Project spelling dictionary
.vscode/                 Shared editor settings and recommendations
assets/                  Original references and editable SVGs; preserve these
docs/                    Project instructions
src/badge_prep/          CLI and image operations
tests/                   Focused pytest tests
.github/workflows/       CI
output/                  Ignored generated results
```

## Working rules

Follow .editorconfig. Keep the src layout and current Python typing syntax.
Use just ci, just lint, just fmt, just typecheck, just test, and just build.
Linters and formatters run through prek. Human-facing tasks belong in justfile;
mise owns tool pins and the environment. Python tools are dev dependencies in
pyproject.toml, resolved in uv.lock. Run uv lock after dependency edits and include
the lockfile in the same change. Python 3.14 runs both the CLI and tests.
Use just setup to install tools, locked dependencies, and both git hook types.
Keep Pyright strict and test signatures typed. Conventional Commits are enforced
by the commit-msg hook. Spelling rules own exclusions in .cspell.config.yaml;
project words belong in .cspell/project.txt. Never add machine-specific dictionary
imports. GitHub CI calls the shared `project-ci` workflow, which runs the hidden
mise task API for lint, build, type-check, and tests; `just ci` runs the same
gates locally.
Never overwrite existing outputs or modify source assets. Preflight batch name
collisions before writing. Preserve aspect ratio and transparency; ignore fully
transparent pixels when extracting colors. Test image behavior and CLI failures.
Keep user documentation in README.md and these instructions here.
