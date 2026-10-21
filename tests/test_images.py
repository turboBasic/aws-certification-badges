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


@pytest.mark.parametrize(
    ("extension", "image_format"),
    [
        ("png", "PNG"),
        ("jpg", "JPEG"),
        ("webp", "WEBP"),
        ("tiff", "TIFF"),
        ("bmp", "BMP"),
    ],
)
def test_prepare_supported_formats_preserves_expected_output_contract(
    tmp_path: Path, extension: str, image_format: str
) -> None:
    source = tmp_path / f"badge.{extension}"
    Image.new("RGB", (4, 2), (240, 32, 16)).save(source, format=image_format)
    output = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "prepare",
            str(source),
            "--output",
            str(output),
            "--size",
            "8",
            "--padding",
            "0",
            "--colors",
            "1",
        ],
    )

    assert result.exit_code == 0
    with Image.open(output / "badge.png") as prepared:
        assert prepared.mode == "RGBA"
        assert prepared.size == (8, 8)
        assert prepared.getchannel("A").getbbox() == (0, 2, 8, 6)
        pixel = prepared.getpixel((4, 3))
        assert isinstance(pixel, tuple)
        assert pixel[0] > 200 and pixel[1] < 60 and pixel[2] < 40 and pixel[3] == 255

    palette_data = json.loads((output / "badge.palette.json").read_text())
    assert set(palette_data) == {"source", "colors"}
    assert palette_data["source"] == source.name
    assert len(palette_data["colors"]) == 1
    assert isinstance(palette_data["colors"][0], str)
    assert len(palette_data["colors"][0]) == 7
    assert palette_data["colors"][0].startswith("#")


def test_batch_collision_rejected_before_writing(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    Image.new("RGB", (10, 10)).save(source / "badge.png")
    Image.new("RGB", (10, 10)).save(source / "badge.jpg")
    output = tmp_path / "output"
    result = runner.invoke(app, ["prepare", str(source), "--output", str(output)])
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


def test_prepare_rejects_unsupported_and_empty_inputs(tmp_path: Path) -> None:
    unsupported = tmp_path / "notes.txt"
    unsupported.write_text("not an image")
    empty = tmp_path / "empty"
    empty.mkdir()
    output = tmp_path / "output"

    unsupported_result = runner.invoke(app, ["prepare", str(unsupported), "--output", str(output)])
    empty_result = runner.invoke(app, ["prepare", str(empty), "--output", str(output)])

    assert unsupported_result.exit_code == 1
    assert "Unsupported raster image" in unsupported_result.output
    assert empty_result.exit_code == 1
    assert "No supported raster images" in empty_result.output
    assert not output.exists()


def test_prepare_reports_corrupt_image_without_traceback(tmp_path: Path) -> None:
    source = tmp_path / "corrupt.png"
    source.write_bytes(b"not an image")

    result = runner.invoke(app, ["prepare", str(source), "--output", str(tmp_path / "output")])

    assert result.exit_code == 1
    assert source.name in result.output
    assert "Traceback" not in result.output


def test_prepare_invalid_option_is_concise() -> None:
    result = runner.invoke(app, ["prepare", "missing.png", "--size", "0"])

    assert result.exit_code == 2
    assert "Traceback" not in result.output


@pytest.mark.parametrize("command", ["prepare", "font-sample"])
def test_command_help_names_supported_raster_formats(command: str) -> None:
    result = runner.invoke(app, [command, "--help"])

    assert result.exit_code == 0
    assert all(
        image_format in result.output for image_format in ("PNG", "JPEG", "WebP", "TIFF", "BMP")
    )


def test_prepare_reports_write_failure_without_traceback(tmp_path: Path) -> None:
    source = tmp_path / "badge.png"
    Image.new("RGB", (10, 10), "red").save(source)
    output_parent = tmp_path / "not-a-directory"
    output_parent.write_text("keep this file")

    result = runner.invoke(app, ["prepare", str(source), "--output", str(output_parent / "output")])

    assert result.exit_code == 1
    assert "Error preparing" in result.output
    assert "Traceback" not in result.output


def test_font_sample_reports_write_failure_without_traceback(tmp_path: Path) -> None:
    source = tmp_path / "badge.png"
    Image.new("RGB", (10, 10), "red").save(source)
    output_parent = tmp_path / "not-a-directory"
    output_parent.write_text("keep this file")

    result = runner.invoke(
        app,
        [
            "font-sample",
            str(source),
            "--box",
            "0,0,5,5",
            "--output",
            str(output_parent / "sample.png"),
        ],
    )

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Traceback" not in result.output


def test_prepare_rejects_symlink_input(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (2, 2), "red").save(source)
    link = tmp_path / "linked.png"
    link.symlink_to(source)

    result = runner.invoke(app, ["prepare", str(link), "--output", str(tmp_path / "output")])

    assert result.exit_code == 1
    assert "must not be a symlink" in result.output


def test_prepare_rejects_symlink_member_in_batch(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (2, 2), "red").save(source)
    batch = tmp_path / "batch"
    batch.mkdir()
    (batch / "linked.png").symlink_to(source)

    result = runner.invoke(app, ["prepare", str(batch), "--output", str(tmp_path / "output")])

    assert result.exit_code == 1
    assert "must not be a symlink" in result.output


def test_prepare_uses_first_frame_of_multi_frame_image(tmp_path: Path) -> None:
    source = tmp_path / "pages.tiff"
    Image.new("RGB", (4, 3), "red").save(
        source,
        save_all=True,
        append_images=[Image.new("RGB", (4, 3), "blue")],
    )
    output = tmp_path / "output"

    result = runner.invoke(
        app,
        [
            "prepare",
            str(source),
            "--output",
            str(output),
            "--size",
            "4",
            "--padding",
            "0",
            "--colors",
            "1",
        ],
    )

    assert result.exit_code == 0
    with Image.open(output / "pages.png") as prepared:
        assert prepared.getpixel((1, 1)) == (255, 0, 0, 255)


def test_prepare_rejects_output_nested_in_input_directory(tmp_path: Path) -> None:
    batch = tmp_path / "batch"
    batch.mkdir()
    Image.new("RGB", (2, 2), "red").save(batch / "badge.png")
    output = batch / "generated"

    result = runner.invoke(app, ["prepare", str(batch), "--output", str(output)])

    assert result.exit_code == 1
    assert "must not be inside" in result.output
    assert not output.exists()


def test_prepare_reports_decompression_bomb_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "large.png"
    Image.new("RGB", (20, 20), "red").save(source)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)

    result = runner.invoke(app, ["prepare", str(source), "--output", str(tmp_path / "output")])

    assert result.exit_code == 1
    assert "safe pixel limit" in " ".join(result.output.split())
    assert "Traceback" not in result.output


def test_batch_collision_checks_every_target_before_writing(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    Image.new("RGB", (10, 10), "red").save(source / "first.png")
    Image.new("RGB", (10, 10), "blue").save(source / "second.png")
    output = tmp_path / "output"
    output.mkdir()
    occupied = output / "second.palette.json"
    occupied.write_text("keep this file")

    result = runner.invoke(app, ["prepare", str(source), "--output", str(output)])

    assert result.exit_code == 1
    assert occupied.read_text() == "keep this file"
    assert not (output / "first.png").exists()
    assert not (output / "first.palette.json").exists()
    assert not (output / "second.png").exists()


def test_single_file_preflight_rejects_output_symlink_to_source(tmp_path: Path) -> None:
    source = tmp_path / "badge.png"
    Image.new("RGB", (10, 10), "red").save(source)
    original = source.read_bytes()
    output = tmp_path / "output"
    output.mkdir()
    (output / "badge.png").symlink_to(source)

    result = runner.invoke(app, ["prepare", str(source), "--output", str(output)])

    assert result.exit_code == 1
    assert source.read_bytes() == original
    assert (output / "badge.png").is_symlink()
    assert not (output / "badge.palette.json").exists()


def test_prepare_cleans_staged_files_after_staging_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from badge_prep import images

    source = tmp_path / "badge.png"
    Image.new("RGB", (10, 10), "red").save(source)
    output = tmp_path / "output"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve this file")

    def fail_dump(*args: object, **kwargs: object) -> None:
        raise OSError("injected palette staging failure")

    monkeypatch.setattr(images.json, "dump", fail_dump)

    with pytest.raises(OSError, match="injected palette staging failure"):
        images.prepare(source, output, 16, 0, 2)

    assert list(output.iterdir()) == [sentinel]
    assert sentinel.read_text() == "preserve this file"


def test_prepare_rolls_back_published_png_after_palette_publish_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from badge_prep import images

    source = tmp_path / "badge.png"
    Image.new("RGB", (10, 10), "red").save(source)
    original = source.read_bytes()
    output = tmp_path / "output"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_text("preserve this file")
    real_link = images.os.link
    calls = 0

    def fail_second_link(source_path: str | Path, target_path: str | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected palette publish failure")
        real_link(source_path, target_path)

    monkeypatch.setattr(images.os, "link", fail_second_link)

    with pytest.raises(OSError, match="injected palette publish failure"):
        images.prepare(source, output, 16, 0, 2)

    assert source.read_bytes() == original
    assert list(output.iterdir()) == [sentinel]
    assert sentinel.read_text() == "preserve this file"


def test_batch_reports_corrupt_member_and_keeps_valid_pair(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "a-corrupt.png").write_bytes(b"not a png")
    Image.new("RGB", (10, 10), "blue").save(source / "b-valid.png")
    output = tmp_path / "output"

    result = runner.invoke(app, ["prepare", str(source), "--output", str(output)])

    assert result.exit_code == 1
    assert "a-corrupt.png" in " ".join(result.output.split())
    assert "Batch complete: 1 succeeded, 1 failed." in result.output
    assert (output / "b-valid.png").is_file()
    assert (output / "b-valid.palette.json").is_file()
    assert not (output / "a-corrupt.png").exists()
    assert not (output / "a-corrupt.palette.json").exists()
    assert "Traceback" not in result.output
