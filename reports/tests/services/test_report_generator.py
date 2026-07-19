import json
from pathlib import Path

from app.services import report_generator


def test_generate_json(sample_report_request, tmp_path: Path):
    request = sample_report_request.model_copy(update={"format": "json"})
    result = report_generator.generate(request, tmp_path)

    assert result.format == "json"
    assert result.filename == f"{request.scan.id}.json"
    output_file = tmp_path / result.filename
    assert output_file.exists()
    json.loads(output_file.read_text(encoding="utf-8"))


def test_generate_markdown(sample_report_request, tmp_path: Path):
    request = sample_report_request.model_copy(update={"format": "markdown"})
    result = report_generator.generate(request, tmp_path)

    assert result.filename == f"{request.scan.id}.md"
    output_file = tmp_path / result.filename
    assert "DVWA Default Login" in output_file.read_text(encoding="utf-8")


def test_generate_html(sample_report_request, tmp_path: Path):
    request = sample_report_request.model_copy(update={"format": "html"})
    result = report_generator.generate(request, tmp_path)

    assert result.filename == f"{request.scan.id}.html"
    output_file = tmp_path / result.filename
    assert "<!DOCTYPE html>" in output_file.read_text(encoding="utf-8")


def test_creates_output_dir_if_missing(sample_report_request, tmp_path: Path):
    output_dir = tmp_path / "nested" / "dir"
    assert not output_dir.exists()

    request = sample_report_request.model_copy(update={"format": "json"})
    report_generator.generate(request, output_dir)

    assert output_dir.exists()
