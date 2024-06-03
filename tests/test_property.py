"""Tests for Logseq property handling."""

from random import choice

import pytest

from rgb_logseq.property import Property, TRUE_VALUES


def spongebob_case(text: str):
    """Return text with upper and lower case randomized."""
    case_options = [str.upper, str.lower]

    return "".join(choice(case_options)(char) for char in text)


class TestIsTrue:
    def test_default_is_not_truthy(self, prop_scalar):
        assert not prop_scalar.is_true

    @pytest.mark.parametrize("value", TRUE_VALUES)
    def test_when_truthy(self, prop_scalar, value):
        prop_scalar.value = value

        assert prop_scalar.is_true

    @pytest.mark.parametrize("value", TRUE_VALUES)
    def test_case_insensitive(self, prop_scalar, value):
        prop_scalar.value = spongebob_case(value)

        assert prop_scalar.is_true


class TestProperty:
    def test_loads(self, prop_scalar):
        prop = Property.loads(prop_scalar.raw)
        assert prop == prop_scalar

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("a", ["a"]),
            ("a,b", ["a", "b"]),
            ("a, b", ["a", "b"]),
            ("a,b,c", ["a", "b", "c"]),
            ("a,b,b", ["a", "b", "b"]),  # want a list not a set!
        ],
    )
    def test_as_list(self, prop_scalar, value, expected):
        prop_scalar.value = value

        assert prop_scalar.as_list() == expected
