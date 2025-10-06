import os
import pytest
from services.ingestion import extract_text

def test_extract_text_txt(tmp_path):
    fp = tmp_path / 'sample.txt'
    fp.write_text('Page 1\nHello world.\nPage 2\nSecond line.\n')
    text, meta = extract_text(str(fp))
    assert 'Hello world.' in text
    assert meta.original_words >= 3
    assert meta.content_hash

def test_80_word_doc(tmp_path):
    fp = tmp_path / "eighty_words.txt"
    # Generate exactly 80 words
    words = [f"word{i}" for i in range(1, 81)]
    fp.write_text(" ".join(words))
    text, meta = extract_text(str(fp))
    assert meta.original_words == 80, f"Expected 80 words, got {meta.original_words}"
    # Ensure normalization didn’t drop words
    assert len(text.split()) == 80
    assert meta.content_hash


def test_unsupported_extension(tmp_path):
    fp = tmp_path / 'file.xyz'
    fp.write_text('dummy')
    with pytest.raises(ValueError):
        extract_text(str(fp))


def test_short_doc(tmp_path):
    fp = tmp_path / 'short.txt'
    fp.write_text('Too short.')
    with pytest.raises(ValueError):
        extract_text(str(fp))
