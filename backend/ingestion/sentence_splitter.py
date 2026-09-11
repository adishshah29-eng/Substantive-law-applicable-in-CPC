"""
Splits Paragraphs into Sentences using spaCy (en_core_web_sm), preserving
paragraph and sentence indices and character offsets into a reconstructed
document text (paragraphs joined in order, separated by "\n\n").
"""
from __future__ import annotations

import spacy

from backend.models.schemas import Paragraph, Sentence

_PARAGRAPH_SEPARATOR = "\n\n"

_nlp: spacy.Language | None = None


def get_nlp() -> spacy.Language:
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def split_sentences(paragraphs: list[Paragraph]) -> list[Sentence]:
    nlp = get_nlp()
    sentences: list[Sentence] = []
    offset = 0

    for para in paragraphs:
        doc = nlp(para.text)
        for sent_idx, sent in enumerate(doc.sents):
            text = sent.text.strip()
            if not text:
                continue
            sentences.append(
                Sentence(
                    paragraph_index=para.index,
                    sentence_index=sent_idx,
                    text=text,
                    char_start=offset + sent.start_char,
                    char_end=offset + sent.end_char,
                )
            )
        offset += len(para.text) + len(_PARAGRAPH_SEPARATOR)

    return sentences
