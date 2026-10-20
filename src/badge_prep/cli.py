"""Local CLI; no uploads or network calls."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from badge_prep.images import EXTENSIONS, ensure_available, font_sample, prepare

app = typer.Typer(no_args_is_help=True, help="Prepare badge rasters for manual vectorization.")
console = Console()


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
        sources = (
            sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)
            if source.is_dir()
            else [source]
        )
        if not sources:
            raise ValueError("No supported raster images found.")
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
