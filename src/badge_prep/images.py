"""Small image operations independent of the CLI."""

import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageOps

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def load_rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGBA")


def normalize(image: Image.Image, size: int, padding: int) -> Image.Image:
    if size < 1 or padding < 0 or 2 * padding >= size:
        raise ValueError("Size must be positive; padding must leave room for the image.")
    image = image.convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("Image is fully transparent.")
    cropped = image.crop(bounds)
    edge = size - 2 * padding
    fitted = ImageOps.contain(cropped, (edge, edge), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size))
    canvas.alpha_composite(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
    return canvas


def palette(image: Image.Image, colors: int) -> list[str]:
    if not 1 <= colors <= 256:
        raise ValueError("Colors must be between 1 and 256.")
    rgba = image.convert("RGBA")
    # Quantize only visible pixels without copying the full image into RGB bytes.
    pixels = bytearray()
    for y in range(rgba.height):
        for x in range(rgba.width):
            pixel = rgba.getpixel((x, y))
            if isinstance(pixel, tuple) and pixel[3]:
                pixels.extend(pixel[:3])
    if not pixels:
        raise ValueError("Image is fully transparent.")
    strip = Image.frombytes("RGB", (len(pixels) // 3, 1), pixels)
    quantized = strip.quantize(colors=colors, dither=Image.Dither.NONE)
    entries: Counter[int] = Counter()
    for x in range(quantized.width):
        index = quantized.getpixel((x, 0))
        if isinstance(index, int):
            entries[index] += 1
    table = quantized.getpalette()
    if table is None:
        raise ValueError("Could not extract palette.")
    colors_by_frequency = [
        (
            "#{:02x}{:02x}{:02x}".format(*table[index * 3 : index * 3 + 3]),
            count,
        )
        for index, count in entries.items()
    ]
    return [color for color, _ in sorted(colors_by_frequency, key=lambda item: (-item[1], item[0]))]


def prepare(source: Path, output: Path, size: int, padding: int, colors: int) -> None:
    image = load_rgba(source)
    normalized = normalize(image, size, padding)
    swatches = palette(image, colors)
    # Both outputs are checked before either file is created.
    targets = [output / f"{source.stem}.png", output / f"{source.stem}.palette.json"]
    ensure_available(targets)
    output.mkdir(parents=True, exist_ok=True)
    with targets[0].open("xb") as handle:
        normalized.save(handle, format="PNG")
    with targets[1].open("x") as handle:
        json.dump({"source": source.name, "colors": swatches}, handle, indent=2)
        handle.write("\n")


def ensure_available(paths: list[Path]) -> None:
    resolved = [path.resolve() for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("Input filenames produce duplicate output names.")
    for path in paths:
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"Refusing to overwrite: {path}")


def font_sample(
    source: Path,
    output: Path,
    box: tuple[int, int, int, int],
    scale: int,
    background: str,
) -> None:
    image = load_rgba(source)
    left, top, right, bottom = box
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ValueError("Box must be inside the original image: left,top,right,bottom.")
    if not 1 <= scale <= 8:
        raise ValueError("Scale must be between 1 and 8.")
    crop = image.crop(box)
    canvas = Image.new("RGBA", crop.size, background)
    canvas.alpha_composite(crop)
    result = ImageOps.contain(
        canvas.convert("RGB"),
        (crop.width * scale, crop.height * scale),
        Image.Resampling.LANCZOS,
    )
    ensure_available([output])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        result.save(handle, format="PNG")
