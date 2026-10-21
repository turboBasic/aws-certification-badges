"""Local CLI; no uploads or network calls."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from badge_prep.images import EXTENSIONS, ensure_available, font_sample, prepare

app = typer.Typer(no_args_is_help=True, help="Prepare badge rasters for manual vectorization.")
console = Console()


def discover_sources(source: Path, output: Path) -> list[Path]:
    if source.is_symlink():
        raise ValueError(f"Input path must not be a symlink: {source}")
    if not source.exists():
        raise ValueError(f"Input path does not exist: {source}")

    if source.is_dir():
        resolved_source = source.resolve()
        resolved_output = output.resolve()
        if resolved_output == resolved_source or resolved_source in resolved_output.parents:
            raise ValueError("Output directory must not be inside the batch input directory.")
        candidates = sorted(source.iterdir())
        symlinks = [
            path for path in candidates if path.is_symlink() and path.suffix.lower() in EXTENSIONS
        ]
        if symlinks:
            raise ValueError(f"Input path must not be a symlink: {symlinks[0]}")
        sources = [
            path for path in candidates if path.is_file() and path.suffix.lower() in EXTENSIONS
        ]
        if not sources:
            raise ValueError(f"No supported raster images found in: {source}")
        return sources

    if not source.is_file() or source.suffix.lower() not in EXTENSIONS:
        raise ValueError(f"Unsupported raster image: {source}")
    return [source]


@app.command("prepare")
def prepare_command(
    source: Annotated[Path, typer.Argument(exists=True, readable=True)],
    output: Annotated[Path, typer.Option(help="Separate directory for generated files.")] = Path(
        "output"
    ),
    size: Annotated[int, typer.Option(min=1, max=8192)] = 1024,
    padding: Annotated[int, typer.Option(min=0)] = 32,
    colors: Annotated[int, typer.Option(min=1, max=256)] = 8,
) -> None:
    """Crop alpha margins, normalize size, and export PNG + palette JSON."""
    try:
        sources = discover_sources(source, output)
        if padding * 2 >= size:
            raise ValueError("Padding must be less than half the canvas size.")
        targets = [
            output / f"{path.stem}{suffix}"
            for path in sources
            for suffix in (".png", ".palette.json")
        ]
        if {p.resolve() for p in sources}.intersection(p.resolve() for p in targets):
            raise ValueError("Output would replace a source image; choose a separate directory.")
        ensure_available(targets)
        for path in sources:
            prepare(path, output, size, padding, colors)
            console.print(f"Prepared {path.name}", markup=False)
    except (OSError, ValueError) as error:
        console.print(f"Error: {error}", style="red", markup=False)
        raise typer.Exit(1) from error


@app.command("font-sample")
def font_sample_command(
    source: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    box: Annotated[str, typer.Option(help="Original pixels: left,top,right,bottom (exclusive).")],
    output: Annotated[Path, typer.Option()] = Path("output/font-sample.png"),
    scale: Annotated[int, typer.Option(min=1, max=8)] = 3,
    background: Annotated[
        str, typer.Option(help="Solid color behind transparent pixels.")
    ] = "white",
) -> None:
    """Export a text region for manual font matching; does not identify fonts."""
    try:
        coordinates = tuple(int(value.strip()) for value in box.split(","))
        if len(coordinates) != 4:
            raise ValueError("Box requires four integers: left,top,right,bottom.")
        left, top, right, bottom = coordinates
        font_sample(source, output, (left, top, right, bottom), scale, background)
    except (OSError, ValueError) as error:
        console.print(f"Error: {error}", style="red", markup=False)
        raise typer.Exit(1) from error
    console.print(
        f"Saved {output}. Upload manually and compare candidate letter shapes.", markup=False
    )
    console.print("https://www.myfonts.com/pages/whatthefont")
    console.print("https://www.fontsquirrel.com/matcherator")
