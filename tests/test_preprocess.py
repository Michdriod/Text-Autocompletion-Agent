import pytest
from services.preprocess import clean_text, sentence_split, preprocess, filter_short_sentences

RAW_SAMPLE = """Page 1
INTRODUCTION
----
* Bullet one explains something.
- Bullet two elaborates.
* Bullet three provides extended narrative detail so we have a higher word count for robust preprocessing tests. It discusses context, rationale, and implications for downstream summarization accuracy and stability.
Page 2
This is a continuation. Dr. Smith presented results. e.g. further data followed. The committee acknowledged limitations; however, momentum continued. Prof. Allen outlined future work streams.

Another paragraph appears here!  Spacing   is    irregular. It includes multiple sentences to ensure sentence segmentation works correctly. Prof. Allen later clarified ambiguous metrics. Etc. Additional lines broaden narrative continuity and add lexical diversity for token planning.

Page 3
Final line. A concluding remark summarizes the preceding discussion while reinforcing the importance of preprocessing consistency across diverse document structures and source formatting artifacts.
"""

def test_clean_text_removes_page_and_bullets():
    cleaned = clean_text(RAW_SAMPLE)
    assert 'Page 1' not in cleaned
    assert 'Bullet one' in cleaned  # content retained sans marker
    assert 'Page 3' not in cleaned
    assert '----' not in cleaned
    # No double blank lines
    assert '\n\n' not in cleaned
    # Expanded sample should now exceed 120 words post-cleaning
    assert len(cleaned.split()) > 120


def test_sentence_split_fallback():
    cleaned = clean_text(RAW_SAMPLE)
    sentences = sentence_split(cleaned, prefer_nltk=False)
    assert any(s.startswith('This is a continuation') for s in sentences)
    assert any('Dr. Smith presented results.' in s for s in sentences)
    # We should have more sentences due to expansion
    assert len(sentences) >= 10


def test_preprocess_pipeline():
    cleaned, sentences = preprocess(RAW_SAMPLE)
    assert len(cleaned) > 40
    assert len(sentences) >= 10


def test_filter_short_sentences():
    sentences = ["One", "Two words", "This is a longer sentence"]
    filtered = filter_short_sentences(sentences, min_words=2)
    assert "One" not in filtered
    assert "Two words" in filtered
    assert "This is a longer sentence" in filtered


def test_abbreviation_handling():
    cleaned = clean_text(RAW_SAMPLE)
    sentences = sentence_split(cleaned, prefer_nltk=False)
    # Ensure 'e.g.' did not cause an incorrect split
    assert any('e.g. further data followed' in s.lower() for s in sentences)
    # Ensure 'Prof. Allen' stays coherent
    assert any('Prof. Allen outlined future work streams.' in s for s in sentences)
