"""Tests for Logseq property handling."""

from random import choice

import pytest

from rgb_logseq.property import Property, TRUE_VALUES


def spongebob_case(text: str):
    """Return text with upper and lower case randomized."""
    case_options = [str.upper, str.lower]

    return "".join(choice(case_options)(char) for char in text)


class TestIsTrue:
    def test_default_is_not_truthy(self, scalar_property):
        assert not scalar_property.is_true

    @pytest.mark.parametrize("value", TRUE_VALUES)
    def test_when_truthy(self, scalar_property, value):
        scalar_property.value = value

        assert scalar_property.is_true

    @pytest.mark.parametrize("value", TRUE_VALUES)
    def test_case_insensitive(self, scalar_property, value):
        scalar_property.value = spongebob_case(value)

        assert scalar_property.is_true


class TestProperty:
    def test_loads(self, scalar_property):
        prop = Property.loads(scalar_property.raw)
        assert prop == scalar_property

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
    def test_as_list(self, scalar_property, value, expected):
        scalar_property.value = value

        assert scalar_property.as_list() == expected
