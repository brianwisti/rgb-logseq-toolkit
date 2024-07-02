"""Tests for Logseq page handling."""

import pytest
from faker import Faker
from rgb_logseq.page import NAMESPACE_SELF, Page, load_page_file, parse_page_text
from rgb_logseq.property import Property

from .conftest import as_branch_block

# pylint: disable=missing-class-docstring, missing-function-docstring


class TestPageLoads:
    def test_empty_defaults(self, page_name):
        text = ""
        page = parse_page_text(text, name=page_name)

        assert page.blocks
        assert page.name == page_name
        assert not page.is_placeholder

    def test_branch_block(self, branch_block_line, page_name):
        text = branch_block_line.raw
        page = parse_page_text(text, name=page_name)

        assert page.blocks

    def test_page_uses_root_properties(self, prop_scalar, page_name):
        text = prop_scalar.raw
        page = parse_page_text(text, name=page_name)

        assert page.properties[prop_scalar.field] == prop_scalar

    def test_page_ignores_branch_properties(self, prop_scalar, page_name):
        text = as_branch_block(prop_scalar.raw)
        page = parse_page_text(text, name=page_name)

        assert not page.properties

    def test_add_block(self, page, branch_block):
        page.add_block(branch_block)

        assert branch_block in page.blocks


class TestPage:
    def test_load(self, path_to_page):
        page = load_page_file(path_to_page)

        assert page.name == path_to_page.stem
        assert page.blocks
        assert not page.is_public

    def test_is_public(self, prop_public, page_name):
        page = parse_page_text(prop_public.raw, name=page_name)

        assert page.is_public

    def test_listing_links(self, line_with_link):
        line, link = line_with_link
        text_line = line.raw
        page = parse_page_text(text_line, name="linked")
        targets = [link.target for link in page.links]

        assert link.target in targets

    def test_no_namespace_by_default(self, page: Page):
        assert page.namespace == NAMESPACE_SELF

    def test_namespaces(self, page: Page, faker: Faker, range_cap: int):
        steps = [faker.unique.word() for _ in range(range_cap)]
        full_namespace = "/".join(steps)
        parent = "/".join(steps[:-1])
        page.name = full_namespace

        assert page.namespace == parent


class TestPageTags:
    def test_empty_tags_by_default(self, page):
        assert not page.tags

    @pytest.mark.parametrize(
        "tag_prop,tags",
        [("a", ("a",)), ("a,b", ("a", "b")), ("a, b", ("a", "b"))],
    )
    def test_with_tags_prop(self, page, tag_prop, tags):
        page.properties["tags"] = Property.loads(f"tags:: {tag_prop}")
        page_tags = page.tags
        found = [tag for tag in tags if tag in page_tags]

        assert len(found) == len(page_tags)
