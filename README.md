# AWS Certification Badges

<!-- markdownlint-disable MD033 MD005 -->

A collection of badge assets for AWS certifications — vector templates for editing and raster examples for reference.

## Raster preparation CLI

A small Python starter for AWS and Anthropic badges. It automates preparation;
tracing and final typography stay in Inkscape. Existing assets remain untouched.

Install [mise](https://mise.jdx.dev/), then run:

```console
mise trust
mise install
just setup
uv run badge-prep --help
```

If mise is not activated in your shell, run `mise exec -- just setup` and prefix
subsequent commands with `mise exec --` too.

Prepare a single image or every supported image directly inside a directory:

```console
uv run badge-prep prepare "assets/raster examples" --output output/aws --size 1024 --padding 32 --colors 8
```

Each input produces `<stem>.png` and `<stem>.palette.json`. Preparation crops only
transparent margins, preserves aspect ratio, and centers the result on a transparent
square. Opaque backgrounds stay intact. Palette JSON lists approximate RGB colors
from the original visible pixels, most frequent first; partially transparent pixels
count once using their underlying RGB values. Gradients and antialiasing affect matches.
The PNG retains the original colors rather than applying the palette.

The palette JSON schema has a `source` filename string and a `colors` array of
six-digit hexadecimal RGB strings. It describes approximated colors found in the
source image; it does not include transparent pixels or change the prepared PNG.

Supported formats: PNG, JPEG, WebP, TIFF, and BMP; only the first frame is used.
Directory traversal is nonrecursive. Existing outputs and duplicate stems are rejected
before batch writing. Each PNG and palette pair is staged in the destination directory and
published with hard links; reported publish errors trigger rollback attempts. The destination
filesystem must support hard links. Two output files cannot be made visible as one transaction,
so abrupt process termination between publishes can leave one file. A corrupt image stops
processing; earlier successful outputs remain. Choose a new output directory for another run.

## Font matching helper

Choose a text rectangle in the original image using an image editor, then export it:

```console
uv run badge-prep font-sample "assets/raster examples/aws-certified-cloud-practitioner-logo-600px.png" --box 100,250,500,350 --output output/text-sample.png --scale 3 --background white
```

Those coordinates illustrate the syntax; choose the bounds around your target text.
Coordinates are `left,top,right,bottom` in pixels after EXIF orientation, with right
and bottom excluded. Export one text style at a time and retain distinctive letters.
Choose a background that contrasts with the text; the option fills transparent pixels
and does not remove an existing background. Enlargement adds no missing image detail.

The helper saves an RGB PNG and prints links to
[WhatTheFont](https://www.myfonts.com/pages/whatthefont) and
[Font Squirrel Matcherator](https://www.fontsquirrel.com/matcherator).
Upload the crop manually, compare candidate letter shapes, then confirm the font
visually in your SVG. These services provide candidates, not guaranteed matches;
custom logo lettering may have no equivalent font. Font selection, acquisition,
and licensing remain manual. The CLI makes no network calls or automatic uploads.

## Development

```console
just fmt
just lint
just typecheck
just test
just build
```

Python 3.14 runs the CLI and tests. `just setup` installs the pinned tools, syncs
locked dependencies, and installs pre-commit and commit-message hooks.

uv locks dependencies; hatchling builds the package. Typer/Rich provide the CLI,
Pillow handles images, Ruff runs through prek, Pyright uses strict mode, and pytest
checks image behavior and output protection. External tool versions and the
virtual environment live in `mise.toml`; Python tools are declared in `pyproject.toml` and resolved in `uv.lock`. Run `uv lock`
after changing dependencies and include the updated lockfile in the same change.
Run `just` to list commands. Generated files belong under ignored `output/`.
Project authoring rules live in [docs/ai-instructions.md](docs/ai-instructions.md).
All linters and formatters run through prek. Hooks cover Python linting and
formatting, strict types, Markdown, TOML, YAML, spelling, file integrity, and
Conventional Commit messages. `just lint` skips Pyright because `just typecheck`
owns that check; commits still run its hook. `just fmt` formats Python and TOML.
GitHub workflow validation is outside these local checks. Source assets remain
untouched; the large-file guard allows files up to 5 MiB.

Spelling rules and exclusions live in `.cspell.config.yaml`; project words live in
`.cspell/project.txt`. Shared VS Code settings select the project interpreter,
pytest, Ruff, and that dictionary; extension recommendations are included.

## Assets

| Preview | Certification | Format | File |
| :---: | :--- | :---: | :--- |
| <a href="assets/vector%20templates/aws-certified-template.svg"><img src="assets/vector%20templates/aws-certified-template.svg" style="max-height: 100px; height: auto; width: auto;" alt="AWS Certified Template"/></a> | AWS Certified (Generic Template) | SVG | [aws-certified-template.svg](assets/vector%20templates/aws-certified-template.svg) |
| <a href="assets/vector%20rendered/aws-certified-ai-practitioner.svg"><img src="assets/vector%20rendered/aws-certified-ai-practitioner.svg" style="max-height: 100px; height: auto; width: auto;" alt="AWS Certified AI Practitioner"/></a> | AWS Certified AI Practitioner | SVG | [aws-certified-ai-practitioner.svg](assets/vector%20rendered/aws-certified-ai-practitioner.svg) |
| <a href="assets/vector%20rendered/aws-certified-cloud-practitioner.svg"><img src="assets/vector%20rendered/aws-certified-cloud-practitioner.svg" style="max-height: 100px; height: auto; width: auto;" alt="AWS Certified Cloud Practitioner"/></a> | AWS Certified Cloud Practitioner | SVG | [aws-certified-cloud-practitioner.svg](assets/vector%20rendered/aws-certified-cloud-practitioner.svg) |
| <a href="assets/vector%20rendered/aws-certified-solutions-architect-associate.svg"><img src="assets/vector%20rendered/aws-certified-solutions-architect-associate.svg" style="max-height: 100px; height: auto; width: auto;" alt="AWS Certified Solutions Architect Associate"/></a> | AWS Certified Solutions Architect Associate | SVG | [aws-certified-solutions-architect-associate.svg](assets/vector%20rendered/aws-certified-solutions-architect-associate.svg) |
| <a href="assets/vector%20rendered/aws-certified-solutions-architect-professional.svg"><img src="assets/vector%20rendered/aws-certified-solutions-architect-professional.svg" style="max-height: 100px; height: auto; width: auto;" alt="AWS Certified Solutions Architect Professional"/></a> | AWS Certified Solutions Architect Professional | SVG | [aws-certified-solutions-architect-professional.svg](assets/vector%20rendered/aws-certified-solutions-architect-professional.svg) |

## Structure

```plaintext
assets/
├── vector templates/
│   └── aws-certified-template.svg                          # Editable SVG base template
├── vector rendered/
│   ├── aws-certified-ai-practitioner.svg
│   ├── aws-certified-cloud-practitioner.svg
│   ├── aws-certified-solutions-architect-associate.svg
│   └── aws-certified-solutions-architect-professional.svg
└── raster examples/
    ├── aws-certified-ai-practitioner-logo-600px.png
    ├── aws-certified-cloud-practitioner-logo-600px.png
    ├── aws-certified-solutions-architect-associate-logo-600px.png
    └── aws-certified-solutions-architect-professional-logo-600px.png
```
