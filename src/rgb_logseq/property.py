"""Handle metadata common to Logseq blocks and pages."""

from __future__ import annotations

from pydantic import BaseModel

from .const import MARK_PROPERTY

TRUE_VALUES = ("true", "1", "yes", "on", "enabled")
ValueList = list[str]


class Property(BaseModel):
    """A block or page property."""

    raw: str
    field: str
    value: str

    @classmethod
    def loads(cls, text: str) -> Property:
        """Return Property object from parsing input text."""
        field, value = text.lstrip().split(MARK_PROPERTY)

        return Property(raw=text, field=field, value=value)

    @property
    def is_true(self) -> bool:
        """Return True if value in TRUE_VALUES."""
        return self.value.lower() in TRUE_VALUES

    def as_list(self) -> ValueList:
        """Return value parsed as a list."""
        return [value.strip() for value in self.value.split(",")]
