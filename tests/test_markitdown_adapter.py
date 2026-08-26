from __future__ import annotations

from pathlib import Path

import pytest

from rag.ingestion.markitdown import LocalMarkItDownAdapter, MarkItDownInputError


class _FakeResult:
    def __init__(self, markdown: object) -> None:
        self.markdown = markdown


class _FakeConverter:
    instances: list["_FakeConverter"] = []
    response: object = "# Local title\r\n\r\nBody\r\n"
    error: Exception | None = None

    def __init__(self, **kwargs) -> None:
        self.constructor_kwargs = kwargs
        self.local_calls: list[tuple[Path, dict]] = []
        self.stream_calls: list[dict] = []
        type(self).instances.append(self)

    def convert_local(self, path: Path, **kwargs):
        self.local_calls.append((path, kwargs))
        if self.error is not None:
            raise self.error
        return _FakeResult(self.response)

    def convert_stream(self, stream, **kwargs):
        self.stream_calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return _FakeResult(self.response)


def _adapter(tmp_path: Path) -> LocalMarkItDownAdapter:
    _FakeConverter.instances.clear()
    _FakeConverter.response = "# Local title\r\n\r\nBody\r\n"
    _FakeConverter.error = None
    return LocalMarkItDownAdapter(
        originals_dir=tmp_path / "originals",
        converter_factory=_FakeConverter,
    )


def _original(tmp_path: Path, name: str = "version.pdf") -> Path:
    root = tmp_path / "originals"
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_bytes(b"validated original")
    return path


def test_allowed_server_owned_path_uses_local_api_and_canonicalizes_output(tmp_path):
    original = _original(tmp_path)
    adapter = _adapter(tmp_path)

    result = adapter.convert(original)

    assert result.status == "ok"
    assert result.markdown == "# Local title\n\nBody\n"
    converter = _FakeConverter.instances[0]
    assert converter.constructor_kwargs == {"enable_plugins": False}
    assert converter.local_calls == [(original.resolve(), {})]


def test_allowed_server_owned_stream_uses_stream_info_without_url(tmp_path):
    original = _original(tmp_path)
    adapter = _adapter(tmp_path)

    with original.open("rb") as stream:
        result = adapter.convert(stream, extension=".pdf")

    assert result.status == "ok"
    stream_info = _FakeConverter.instances[0].stream_calls[0]["stream_info"]
    assert stream_info.extension == ".pdf"
    assert stream_info.mimetype == "application/pdf"
    assert stream_info.filename == "validated-original.pdf"
    assert stream_info.url is None


def test_path_outside_originals_is_rejected_before_converter(tmp_path):
    root = tmp_path / "originals"
    root.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"outside")
    adapter = _adapter(tmp_path)

    with pytest.raises(MarkItDownInputError) as excinfo:
        adapter.convert(outside)

    assert excinfo.value.code == "path_outside_originals"
    assert _FakeConverter.instances == []


def test_symlink_original_is_rejected_before_converter(tmp_path, monkeypatch):
    original = _original(tmp_path)
    link = original.with_name("link.pdf")
    try:
        link.symlink_to(original)
    except OSError:
        # Exercise the same deterministic branch when this Windows runner does
        # not grant symlink creation to the test process.
        real_is_symlink = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda path: path == link or real_is_symlink(path))

    adapter = _adapter(tmp_path)
    with pytest.raises(MarkItDownInputError) as excinfo:
        adapter.convert(link)

    assert excinfo.value.code == "symlink_rejected"
    assert _FakeConverter.instances == []


@pytest.mark.parametrize("source", ["file://C:/secret.pdf", "https://example.test/file.pdf"])
def test_file_uri_and_url_inputs_are_rejected(source, tmp_path):
    adapter = _adapter(tmp_path)

    with pytest.raises(MarkItDownInputError) as excinfo:
        adapter.convert(source)

    assert excinfo.value.code == "uri_input_rejected"
    assert _FakeConverter.instances == []


def test_caller_path_string_is_rejected(tmp_path):
    adapter = _adapter(tmp_path)

    with pytest.raises(MarkItDownInputError) as excinfo:
        adapter.convert(str(_original(tmp_path)))

    assert excinfo.value.code == "path_string_rejected"
    assert _FakeConverter.instances == []


def test_unverifiable_binary_stream_is_rejected(tmp_path):
    import io

    adapter = _adapter(tmp_path)
    with pytest.raises(MarkItDownInputError) as excinfo:
        adapter.convert(io.BytesIO(b"not server-owned"), extension=".pdf")

    assert excinfo.value.code == "stream_origin_unverifiable"
    assert _FakeConverter.instances == []


def test_converter_exception_is_a_safe_failed_result(tmp_path):
    original = _original(tmp_path)
    adapter = _adapter(tmp_path)
    _FakeConverter.error = RuntimeError("document-derived or path-sensitive detail")

    result = adapter.convert(original)

    assert result.status == "failed"
    assert result.markdown is None
    assert result.error_code == "converter_exception"
    assert result.warnings == ("converter_exception",)
    assert "document-derived" not in str(result.warnings)


def test_whitespace_output_is_distinct_empty_result(tmp_path):
    original = _original(tmp_path)
    adapter = _adapter(tmp_path)
    _FakeConverter.response = " \r\n\t  "

    result = adapter.convert(original)

    assert result.status == "empty"
    assert result.markdown == ""
    assert result.error_code == "empty_markdown"
    assert result.warnings == ("empty_markdown",)


def test_non_text_converter_output_is_a_failed_result(tmp_path):
    original = _original(tmp_path)
    adapter = _adapter(tmp_path)
    _FakeConverter.response = object()

    result = adapter.convert(original)

    assert result.status == "failed"
    assert result.markdown is None
    assert result.error_code == "invalid_converter_result"
    assert result.warnings == ("invalid_converter_result",)


def test_parser_metadata_is_pinned_and_deterministic(tmp_path):
    adapter_a = _adapter(tmp_path)
    adapter_b = _adapter(tmp_path)

    assert (adapter_a.parser_name, adapter_a.parser_version, adapter_a.parser_provenance) == (
        "markitdown",
        "0.1.7",
        "markitdown@9dc0d6579b8739c9d0671ff205e071e3053c7df1",
    )
    assert (adapter_a.parser_name, adapter_a.parser_version, adapter_a.parser_provenance) == (
        adapter_b.parser_name,
        adapter_b.parser_version,
        adapter_b.parser_provenance,
    )
