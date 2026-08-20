import json
from pathlib import Path

import pytest

from app.services import report_generator


def test_generate_path_traversal_rejected(sample_report_request, tmp_path: Path):
    malicious_scan = sample_report_request.scan.model_copy(update={"id": "../../evil"})
    request = sample_report_request.model_copy(update={"format": "json", "scan": malicious_scan})

    escaped_path = tmp_path.parent.parent / "evil.json"

    with pytest.raises(report_generator.InvalidReportRequestError):
        report_generator.generate(request, tmp_path)

    # nothing should have been written outside (or inside) output_dir
    assert not escaped_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_generate_rejects_same_dir_subpath(sample_report_request, tmp_path: Path):
    # Regression: a scan.id containing "/" that still resolves *inside*
    # output_dir (e.g. "abc/def") used to pass the old parents-only check
    # and then crash with an unhandled FileNotFoundError, since only
    # output_dir itself (not "abc/") was ever created.
    malicious_scan = sample_report_request.scan.model_copy(update={"id": "abc/def"})
    request = sample_report_request.model_copy(update={"format": "json", "scan": malicious_scan})

    with pytest.raises(report_generator.InvalidReportRequestError):
        report_generator.generate(request, tmp_path)

    assert list(tmp_path.iterdir()) == []


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
