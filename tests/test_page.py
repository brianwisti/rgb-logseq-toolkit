"""Tests for Logseq page handling."""

from pathlib import Path

import pytest

from rgb_logseq.page import load_page_file, parse_page_text

from .conftest import as_branch_block


@pytest.fixture
def page_path(page_name, branch_block_line, fs):
    path = Path(f"{page_name}.md")
    fs.create_file(path, contents=branch_block_line.raw)
    return path


# pylint: disable=missing-class-docstring, missing-function-docstring


class TestPageLoads:
    def test_empty(self, page_name):
        text = ""
        page = parse_page_text(text, name=page_name)

        assert page.blocks
        assert page.name == page_name

    def test_branch_block(self, branch_block_line, page_name):
        text = branch_block_line.raw
        page = parse_page_text(text, name=page_name)

        assert page.blocks

    def test_page_uses_root_properties(self, scalar_property, page_name):
        text = scalar_property.raw
        page = parse_page_text(text, name=page_name)

        assert page.properties[scalar_property.field] == scalar_property

    def test_page_ignores_branch_properties(self, scalar_property, page_name):
        text = as_branch_block(scalar_property.raw)
        page = parse_page_text(text, name=page_name)

        assert not page.properties


class TestPage:
    def test_is_public(self, public_prop, page_name):
        page = parse_page_text(public_prop.raw, name=page_name)

        assert page.is_public


class TestPageLoad:
    def test_load(self, page_path):
        page = load_page_file(page_path)

        assert page.name == page_path.stem
        assert page.blocks
        assert not page.is_public


class TestPageLinks:
    def test_listing_links(self, line_with_link):
        line, link = line_with_link
        text_line = line.raw
        page = parse_page_text(text_line, name="linked")
        targets = [link.target for link in page.links]

        assert link.target in targets
