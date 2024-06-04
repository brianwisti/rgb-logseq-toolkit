"""Test database prep and interaction."""

import pytest

from rgb_logseq import db


class TestPrepareText:
    def test_quotes_are_masked(self, word):
        source = f'"{word}"'
        expected = f"*{word}*"

        assert db.prepare_text(source) == expected

    def test_escaped_dollars_are_unescaped(self, word):
        source = f"\\${word}"
        expected = f"${word}"

        assert db.prepare_text(source) == expected

    @pytest.mark.parametrize("escape, doubled", [("\\", "\\\\"), ("\n", "\\\\n")])
    def test_most_escapes_are_doubled(self, escape, doubled, word):
        source = f"{escape}{word}"
        expected = f"{doubled}{word}"

        assert db.prepare_text(source) == expected
