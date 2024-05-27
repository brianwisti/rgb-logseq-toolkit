"""Test parsing a single lines in a Logseq block or page."""

import pytest

from rgb_logseq.const import MARK_BLOCK_CONTINUATION, MARK_BLOCK_OPENER
from rgb_logseq.line import parse_line

from .conftest import as_branch_block, as_branch_continuation, as_page_link

# pylint: disable=missing-class-docstring, missing-function-docstring


class TestParseLine:
    def test_empty_line_parsed(self, empty_line):
        line = parse_line(empty_line)

        assert not line.raw
        assert not line.content
        assert line.depth == 0
        assert line.is_content
        assert not line.is_block_opener
        assert not line.is_code_fence

    def test_plain_content_line_parsed(self, text_line):
        line = parse_line(text_line)

        assert line.raw == text_line
        assert line.content == text_line
        assert line.depth == 0
        assert not line.is_block_opener
        assert not line.is_code_fence

    @pytest.mark.parametrize(
        "marker, is_block_opener",
        ((MARK_BLOCK_OPENER, True), (MARK_BLOCK_CONTINUATION, False)),
    )
    def test_block_markers_parsed(self, text_line, marker, is_block_opener):
        block_line = f"{marker}{text_line}"
        line = parse_line(block_line)

        assert line.raw == block_line
        assert line.content == text_line
        assert line.depth == 1
        assert line.is_block_opener == is_block_opener

    def test_indented_block_opener_parsed(self, text_line):
        block_line = f"\t{as_branch_block(text_line)}"
        line = parse_line(block_line)

        assert line.raw == block_line
        assert line.content == text_line
        assert line.depth == 2
        assert line.is_block_opener

    def test_empty_branch_line_parsed(self):
        branch_line = "-"
        line = parse_line(branch_line)
        assert line.raw == branch_line
        assert line.content == ""
        assert line.depth == 1
        assert line.is_empty
        assert line.is_block_opener


class TestPropertyLine:
    def test_property_line_parsed(self, scalar_property):
        line = parse_line(scalar_property.raw)

        assert not line.is_content
        assert line.is_property

    def test_parsed_property_attributes(self, scalar_property):
        line = parse_line(scalar_property.raw)
        prop = line.as_property()

        assert prop.raw == scalar_property.raw
        assert prop.field == scalar_property.field
        assert prop.value == scalar_property.value

    def test_branch_block_property_line_parsed(self, scalar_property):
        property_line = as_branch_continuation(scalar_property.raw)
        line = parse_line(property_line)

        assert line.is_property
        assert line.as_property().field == scalar_property.field

    def test_branch_block_code_fence_parsed(self, code_fence):
        text_line = as_branch_block(code_fence)
        line = parse_line(text_line)

        assert line.is_code_fence

    def test_property_in_code_fence_ignored(self, code_fence, scalar_property):
        text_line = as_branch_block(f"{code_fence} {scalar_property.raw}")
        line = parse_line(text_line)

        assert line.is_code_fence
        assert not line.is_property


class TestDirectiveLine:
    def test_directive_opener(self, quote_directive_pair):
        text_line = as_branch_block(quote_directive_pair.opener)
        line = parse_line(text_line)

        assert line.is_directive_opener
        assert not line.is_content
        assert line.directive == "QUOTE"

    def test_directive_closer(self, quote_directive_pair):
        text_line = as_branch_continuation(quote_directive_pair.closer)
        line = parse_line(text_line)

        assert line.is_directive_closer
        assert not line.is_content
        assert line.directive == quote_directive_pair.directive


class TestLineLinks:
    def test_standalone_link_parsed(self, graph_link):
        text_line = as_page_link(graph_link)
        line = parse_line(text_line)

        assert any(link for link in line.links if link.target == graph_link.target)

    def test_multiple_links_parsed(self, graph_links):
        text_line = " ".join([as_page_link(link) for link in graph_links])
        line = parse_line(text_line)
        parsed_targets = [link.target for link in line.links]
        matched_links = [link for link in graph_links if link.target in parsed_targets]

        assert len(matched_links) == len(graph_links)

    def test_links_in_code_ignored(self, graph_link):
        link_text = as_page_link(graph_link)
        text_line = f"`{link_text}`"
        line = parse_line(text_line)

        assert not line.links
