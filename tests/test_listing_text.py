from pathlib import Path
import pytest

from playtool.core import ToolError
from playtool.listing import validate_listing_text, _read_text


def test_listing_text_limits_pass():
    result = validate_listing_text(
        "Comunica-CIATA",
        "Mensagens acessíveis com foco em autonomia e inclusão.",
        "Aplicativo de comunicação acessível desenvolvido pelo CIATA.",
        "https://www.youtube.com/watch?v=abc123",
    )
    assert result["valid"] is True
    assert result["character_counts"]["title"] == len("Comunica-CIATA")


def test_listing_text_limits_fail():
    result = validate_listing_text("x" * 31, "y" * 81, "z" * 4001)
    assert result["valid"] is False
    assert len(result["errors"]) == 3


def test_youtube_url_must_be_https():
    result = validate_listing_text("App", "Resumo", "Descrição", "http://youtube.com/watch?v=1")
    assert result["valid"] is False
    assert "HTTPS" in result["errors"][0]


def test_read_text_from_utf8_file(tmp_path: Path):
    p = tmp_path / "descricao.txt"
    p.write_text("  Texto acessível.\n", encoding="utf-8")
    assert _read_text(None, p, "descrição") == "Texto acessível."


def test_read_text_rejects_two_sources(tmp_path: Path):
    p = tmp_path / "titulo.txt"
    p.write_text("Título", encoding="utf-8")
    with pytest.raises(ToolError):
        _read_text("Título", p, "título")
