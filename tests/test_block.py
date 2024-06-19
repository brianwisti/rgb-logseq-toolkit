"""Test loading and processing Logseq blocks."""

import uuid

import pytest

from rgb_logseq.block import BlockDepthError, find_blocks, from_lines
from rgb_logseq.line import Line, parse_line, parse_lines

from .conftest import (
    as_branch_block,
    as_branch_continuation,
    as_multiline_block,
    as_separate_branch_blocks,
)

# pylint: disable=missing-class-docstring, missing-function-docstring


class TestBlock:
    def test_root_block_structure(self, root_block_line):
        block = from_lines([root_block_line])

        assert root_block_line in block.lines

        assert block.id
        assert block.raw == root_block_line.raw
        assert block.content == root_block_line.content
        assert block.depth == 0
        assert not block.has_code_block
        assert not block.is_public
        assert not block.tags
        assert not block.is_directive

    def test_block_id_is_unique(self, root_block_line):
        block_a = from_lines([root_block_line])
        block_b = from_lines([root_block_line])

        assert block_a.id != block_b.id

    def test_block_id_from_props(self, root_block_line, faker):
        id_prop = faker.uuid4()
        id_prop_line = Line(raw=f"id:: {id_prop}")
        block = from_lines([id_prop_line, root_block_line])

        assert block.id == uuid.UUID(id_prop)


class TestBranches:
    def test_empty_branches(self, root_block_line):
        block = from_lines([root_block_line])

        assert not block.branches


class TestFindBlocks:
    def test_empty_line_is_parsed(self):
        blocks = find_blocks("")

        assert blocks

    def test_root_block_content_is_parsed(self, text_line):
        blocks = find_blocks(text_line)

        assert blocks

    def test_branch_block_line_is_parsed(self, text_line):
        branch_block_line = as_branch_block(text_line)
        blocks = find_blocks(branch_block_line)

        assert blocks

    def test_multiple_branch_block_lines_are_parsed(self, text_lines):
        branch_block_lines = as_separate_branch_blocks(text_lines)
        print(branch_block_lines)
        blocks = find_blocks(branch_block_lines)

        assert len(blocks) == len(text_lines)

    def test_multiline_block_is_parsed(self, text_lines):
        block_string = as_multiline_block(text_lines)
        blocks = find_blocks(block_string)

        assert len(blocks) == 1

    def test_first_line_must_be_flush(self, text_line):
        branch_continuation_line = as_branch_continuation(text_line)

        with pytest.raises(BlockDepthError):
            _ = find_blocks(branch_continuation_line)


class TestBlockFromLines:
    def test_root_block_structure(self, root_block_line):
        block = from_lines([root_block_line])

        assert block.raw == root_block_line.raw
        assert block.content == root_block_line.content
        assert block.depth == 0
        assert not block.has_code_block
        assert not block.is_public
        assert not block.tags
        assert not block.is_directive

    def test_branch_block_structure(self, branch_block_line):
        block = from_lines([branch_block_line])

        assert block.depth == 1
        assert block.raw == branch_block_line.raw
        assert block.content == branch_block_line.content

    def test_multiline_block_structure(self, multiline_block_lines):
        block = from_lines(multiline_block_lines)
        raw = "\n".join(line.raw for line in multiline_block_lines)
        content = "\n".join(line.content for line in multiline_block_lines)

        assert block.depth == 1
        assert block.raw == raw
        assert block.content == content

    def test_multiline_block_depth_mismatch(self, multiline_block_lines):
        multiline_block_lines[1].raw = f"\t{multiline_block_lines[1].raw}"

        with pytest.raises(ValueError):
            _ = from_lines(multiline_block_lines)

    def test_block_property(self, prop_scalar):
        line = parse_line(prop_scalar.raw)
        block = from_lines([line])

        assert block.properties[prop_scalar.field] == prop_scalar

    def test_block_property_without_property_line(self, root_block_line, prop_scalar):
        block = from_lines([root_block_line])

        assert prop_scalar.field not in block.properties

    def test_multiline_block_with_property(self, multiline_block_lines, prop_scalar):
        property_line = parse_line(f"  {prop_scalar.raw}")
        all_lines = [property_line] + multiline_block_lines
        block = from_lines(all_lines)

        assert block.properties[prop_scalar.field].value == prop_scalar.value

    def test_property_not_in_block_content(self, root_block_line, prop_scalar):
        property_line = parse_line(prop_scalar.raw)
        all_lines = [property_line, root_block_line]
        block = from_lines(all_lines)

        assert property_line.content not in block.content

    @pytest.mark.parametrize("is_public", ["true", "True", "1", "yes", "on", "enabled"])
    def test_is_public_when_true(self, is_public):
        input_string = f"public:: {is_public}"
        block = from_lines([parse_line(input_string)])

        assert block.is_public

    @pytest.mark.parametrize(
        "is_public",
        ["false", "False", "0", "no", "off", "disabled", "waffles"],
    )
    def test_is_public_when_false(self, is_public):
        input_string = f"public:: {is_public}"
        block = from_lines([parse_line(input_string)])

        assert not block.is_public

    @pytest.mark.parametrize(
        "tag_prop_value, tags",
        [
            ("post", ["post"]),
            ("post, waffles", ["post", "waffles"]),
        ],
    )
    def test_tags(self, tag_prop_value, tags):
        input_string = f"tags:: {tag_prop_value}"
        block = from_lines([parse_line(input_string)])

        assert block.tags == tags


class TestCodeBlock:
    def test_code_block(self, text_line):
        text_lines = [
            "- ```",
            f"  {text_line}",
            "  ```",
        ]
        block = from_lines(parse_lines(text_lines))

        assert block.has_code_block

    def test_code_block_must_end(self, text_line):
        text_lines = [
            "- ```",
            f"  {text_line}",
        ]

        with pytest.raises(ValueError):
            _ = from_lines(parse_lines(text_lines))

    def test_properties_in_code_blocks_are_ignored(self, prop_scalar):
        text_lines = [
            "- ```",
            f"  {prop_scalar.raw}",
            "  ```",
        ]
        block = from_lines(parse_lines(text_lines))

        assert prop_scalar.field not in block.properties

    def test_links_in_code_blocks_are_ignored(self):
        text_lines = [
            "- ```",
            '  alta2.set_index("date")[["snow"]]',
            "  ```",
        ]
        block = from_lines(parse_lines(text_lines))
        assert not block.links


class TestBlockIsHeading:
    def test_default_is_false(self, branch_block):
        assert not branch_block.is_heading

    def test_with_heading_prop(self, branch_block, prop_heading):
        branch_block.properties["heading"] = prop_heading

        assert branch_block.is_heading

    @pytest.mark.parametrize(
        "prefix",
        ["#", "##", "###", "####", "#####", "######"],
    )
    def test_with_atx_prefix(self, prefix: str, text_line: str):
        text_line = f"- {prefix} {text_line}"
        block = from_lines([Line(raw=text_line)])

        assert block.is_heading


class TestLoadDirectiveBlock:
    def test_loads(self):
        text_lines = ["- #+BEGIN_QUOTE", "  Hello!", "  #+END_QUOTE"]
        lines = parse_lines(text_lines)
        print(lines)
        block = from_lines(lines)

        assert block.content == "Hello!"
        assert block.directive == "QUOTE"

    def test_unclosed(self):
        text_lines = ["- #+BEGIN_QUOTE", "  Hello!"]
        lines = parse_lines(text_lines)

        with pytest.raises(ValueError):
            _ = from_lines(lines)

    def test_close_without_open(self):
        text_lines = ["  Hello!", "  #+END_QUOTE"]
        lines = parse_lines(text_lines)

        with pytest.raises(ValueError):
            _ = from_lines(lines)


class TestLinks:
    def test_listing_block_links(self, branch_block):
        text_line = f"- (({branch_block.id.hex}))"
        block = from_lines([Line(raw=text_line)])

        assert branch_block.id in [link.target for link in block.block_links]

    def test_listing_page_links(self, line_with_link):
        line, link = line_with_link
        block = from_lines([line])
        targets = [link.target for link in block.links]

        assert link.target in targets

    def test_listing_tag_links(self):
        text_line = "- [Standard Ebooks](https://standardebooks.org/) #Read"
        line = parse_line(text_line)
        block = from_lines([line])
        targets = [link.target for link in block.tag_links]

        assert "Read" in targets

    def test_listing_resource_links(self, resource_link):
        text_line = f"- [{resource_link.link_text}]({resource_link.target})"
        line = parse_line(text_line)
        block = from_lines([line])

        targets = [link.target for link in block.resource_links]
        assert resource_link.target in targets
