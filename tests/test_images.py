import json
from pathlib import Path

import pytest
from PIL import Image
from typer.testing import CliRunner

from badge_prep.cli import app
from badge_prep.images import font_sample, load_rgba, normalize, palette

runner = CliRunner()


def test_normalize_crops_alpha_and_preserves_proportions() -> None:
    image = Image.new("RGBA", (100, 100))
    image.paste((255, 0, 0, 255), (20, 30, 80, 60))
    result = normalize(image, 80, 10)
    assert result.size == (80, 80)
    assert result.getchannel("A").getbbox() == (10, 25, 70, 55)


def test_normalize_keeps_partially_transparent_edge_pixels() -> None:
    image = Image.new("RGBA", (9, 7))
    image.paste((255, 0, 0, 1), (3, 2, 4, 3))
    image.paste((0, 0, 255, 255), (5, 4, 6, 5))

    result = normalize(image, 9, 0)

    assert result.getchannel("A").getbbox() == (0, 0, 9, 9)
    pixel = result.getpixel((0, 0))
    assert isinstance(pixel, tuple)
    assert pixel[3] > 0


def test_normalize_centers_odd_sized_result_and_preserves_ratio() -> None:
    image = Image.new("RGBA", (5, 3), "red")

    result = normalize(image, 9, 1)

    assert result.getchannel("A").getbbox() == (1, 2, 8, 6)
    assert result.getpixel((4, 4)) == (255, 0, 0, 255)


def test_load_rgba_applies_exif_orientation(tmp_path: Path) -> None:
    source = tmp_path / "rotated.png"
    image = Image.new("RGB", (3, 2))
    image.paste((255, 0, 0), (0, 0, 1, 1))
    exif = Image.Exif()
    exif[274] = 6
    image.save(source, exif=exif)

    result = load_rgba(source)

    assert result.size == (2, 3)
    pixel = result.getpixel((1, 0))
    assert isinstance(pixel, tuple)
    assert pixel[:3] == (255, 0, 0)


def test_palette_excludes_hidden_colors_and_orders_by_frequency() -> None:
    image = Image.new("RGBA", (20, 1), (0, 255, 0, 0))
    image.paste((255, 0, 0, 255), (0, 0, 6, 1))
    image.paste((0, 0, 255, 255), (6, 0, 8, 1))
    assert palette(image, 2) == ["#ff0000", "#0000ff"]


def test_palette_counts_partially_transparent_pixels_once() -> None:
    image = Image.new("RGBA", (4, 1), (0, 255, 0, 0))
    image.paste((255, 0, 0, 1), (0, 0, 3, 1))
    image.paste((0, 0, 255, 255), (3, 0, 4, 1))

    assert palette(image, 2) == ["#ff0000", "#0000ff"]


def test_palette_ties_use_color_order_deterministically() -> None:
    image = Image.new("RGB", (2, 1), "red")
    image.paste("blue", (1, 0, 2, 1))

    assert palette(image, 2) == ["#0000ff", "#ff0000"]
    assert palette(image, 2) == ["#0000ff", "#ff0000"]


def test_empty_image_rejected() -> None:
    with pytest.raises(ValueError, match="transparent"):
        normalize(Image.new("RGBA", (5, 5)), 50, 5)


def test_batch_outputs_and_overwrite_protection(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    Image.new("RGB", (30, 20), "red").save(source / "badge.png")
    output = tmp_path / "output"
    arguments = ["prepare", str(source), "--output", str(output), "--size", "100"]
    assert runner.invoke(app, arguments).exit_code == 0
    prepared = output / "badge.png"
    original = prepared.read_bytes()
    palette_data = json.loads((output / "badge.palette.json").read_text())
    assert palette_data == {"source": "badge.png", "colors": ["#ff0000"]}
    assert runner.invoke(app, arguments).exit_code == 1
    assert prepared.read_bytes() == original


def test_batch_collision_rejected_before_writing(tmp_path: Path) -> None:
    Image.new("RGB", (10, 10)).save(tmp_path / "badge.png")
    Image.new("RGB", (10, 10)).save(tmp_path / "badge.jpg")
    output = tmp_path / "output"
    result = runner.invoke(app, ["prepare", str(tmp_path), "--output", str(output)])
    assert result.exit_code == 1
    assert "duplicate" in result.output
    assert not output.exists()


def test_source_cannot_be_output(tmp_path: Path) -> None:
    source = tmp_path / "badge.png"
    Image.new("RGB", (10, 10)).save(source)
    original = source.read_bytes()
    result = runner.invoke(app, ["prepare", str(source), "--output", str(tmp_path)])
    assert result.exit_code == 1
    assert source.read_bytes() == original


def test_font_sample_flattens_and_resizes(tmp_path: Path) -> None:
    source, output = tmp_path / "badge.png", tmp_path / "sample.png"
    Image.new("RGBA", (20, 10)).save(source)
    font_sample(source, output, (2, 1, 12, 6), 3, "white")
    with Image.open(output) as sample:
        assert sample.size == (30, 15)
        assert sample.mode == "RGB"
        assert sample.getpixel((0, 0)) == (255, 255, 255)
    with pytest.raises(FileExistsError):
        font_sample(source, output, (2, 1, 12, 6), 3, "white")


def test_font_sample_uses_exif_coordinates_and_allows_boxes_ending_at_image_edges(
    tmp_path: Path,
) -> None:
    source = tmp_path / "rotated.png"
    image = Image.new("RGB", (3, 2), "black")
    image.paste("red", (0, 0, 1, 1))
    exif = Image.Exif()
    exif[274] = 6
    image.save(source, exif=exif)
    output = tmp_path / "sample.png"

    font_sample(source, output, (1, 0, 2, 3), 2, "white")

    with Image.open(output) as sample:
        assert sample.size == (2, 6)
        assert sample.mode == "RGB"
        assert sample.getpixel((0, 0)) == (255, 0, 0)


def test_font_sample_rejects_boxes_beyond_oriented_image(tmp_path: Path) -> None:
    source = tmp_path / "badge.png"
    Image.new("RGB", (3, 2), "black").save(source)

    with pytest.raises(ValueError, match="inside"):
        font_sample(source, tmp_path / "sample.png", (0, 0, 4, 2), 1, "white")


@pytest.mark.parametrize("box", ["1,2,3", "bad", "0,0,100,100", "5,0,1,2"])
def test_font_sample_invalid_box(tmp_path: Path, box: str) -> None:
    source = tmp_path / "badge.png"
    Image.new("RGB", (20, 10)).save(source)
    output = tmp_path / "sample.png"
    result = runner.invoke(app, ["font-sample", str(source), "--box", box, "--output", str(output)])
    assert result.exit_code == 1
    assert not output.exists()
