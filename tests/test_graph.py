"""Test handling complete Logseq graphs."""

import pytest
from pathlib import Path

from rgb_logseq.graph import (
    DuplicateAssetError,
    DuplicatePageNameError,
    Graph,
    load_graph,
)
from rgb_logseq.page import NAMESPACE_SELF, Page, parse_page_text


@pytest.fixture
def graph():
    """Return an empty Graph."""
    return Graph()


def test_empty_graph():
    graph = Graph()

    assert not graph.pages
    assert not graph.blocks


class TestGraphAssetManagement:
    def test_empty_assets(self, graph):
        assert not graph.assets

    def test_add_asset(self, graph, asset_path):
        expected_name = f"../assets/{asset_path.name}"
        asset = graph.add_asset(asset_path)

        assert asset.path == asset_path
        assert asset.name == expected_name
        assert asset.name in graph.assets
        assert graph.assets[asset.name].path == asset_path

    def test_duplicate_asset_is_error(self, graph, asset_path):
        graph.add_asset(asset_path)

        with pytest.raises(DuplicateAssetError):
            graph.add_asset(asset_path)

    def test_empty_asset_links(self, graph: Graph):
        assert not graph.asset_links

    def test_asset_links(self, graph, asset_path):
        asset = graph.add_asset(asset_path)
        text_line = f"- ![image]({asset.name})"
        page = parse_page_text(text_line, name="test")
        graph.add_page(page)

        assert graph.asset_links
        print(graph.asset_links)
        assert any(link for link in graph.asset_links if link["target"] == asset.name)


class TestGraphPageManagement:
    def test_check_for_page_not_in_graph(self, graph, page):
        assert not graph.has_page(page.name)

    def test_add_and_check_for_page(self, graph, page):
        graph.add_page(page)

        assert graph.has_page(page.name)

    def test_add_page_notes_blocks(self, graph, page):
        graph.add_page(page)

        for block in page.blocks:
            assert block.id in graph.blocks

    def test_adding_placeholder_page(self, graph, page_name):
        graph.add_placeholder(page_name)

        assert graph.has_page(page_name)

    def test_adding_multiple_placeholders(self, graph, page, another_page):
        pages = [page.name, another_page.name]
        graph.add_placeholders(pages)

        assert page.name in graph.pages
        assert another_page.name in graph.pages

    def test_placeholder_links_are_flagged(self, graph, page_name):
        graph.add_placeholder(page_name)

        assert graph.pages[page_name].is_placeholder

    def test_adding_duplicate_page_is_error(self, graph, page):
        graph.add_page(page)

        with pytest.raises(DuplicatePageNameError):
            graph.add_page(page)

    def test_overwriting_placeholder_pages(self, graph, page):
        graph.add_placeholder(page.name)
        graph.add_page(page)

        assert not graph.pages[page.name].is_placeholder
        assert graph.pages[page.name] == page

    def test_adding_page_with_unknown_page_links(self, graph, linked_pages):
        link_source = linked_pages.link_source
        link_target = linked_pages.link_target
        graph.add_page(link_source)

        assert graph.has_page(link_target.name)


class TestDirectLinksInGraph:
    def test_with_empty_graph(self):
        graph = Graph()

        assert not graph.links

    def test_with_linked_pages(self, graph, linked_pages):
        link_source = linked_pages.link_source
        link_target = linked_pages.link_target
        graph.add_page(link_source)
        graph.add_page(link_target)

        assert graph.links
        assert any(
            link
            for link in graph.links
            if link["from"] == link_source.name and link["to"] == link_target.name
        )

    def test_with_placeholder_link(self, graph, linked_pages):
        link_source = linked_pages.link_source
        link_target = linked_pages.link_target
        graph.add_page(link_source)

        assert any(
            link
            for link in graph.links
            if link["from"] == link_source.name and link["to"] == link_target.name
        )


class TestGraphBlockProperties:
    def test_placeholders_created_for_block_props(self, graph, page_with_heading):
        graph.add_page(page_with_heading)

        assert "heading" in graph.pages


class TestGraphPageProperties:
    def test_with_empty_graph(self, graph):
        assert not graph.page_properties

    def test_page_property_recorded(self, graph, public_page):
        graph.add_page(public_page)

        assert "public" in graph.page_properties

    def test_entry_includes_pages_with_property(self, graph, public_page):
        graph.add_page(public_page)

        assert public_page.name in graph.page_properties["public"]

    def test_entry_includes_value_for_page(self, graph, public_page):
        graph.add_page(public_page)

        assert graph.page_properties["public"][public_page.name] == "true"

    def test_placeholder_created_for_property(self, graph, public_page):
        graph.add_page(public_page)

        assert "public" in graph.pages


class TestGraphPageTags:
    def test_empty_by_default(self, graph):
        assert not graph.page_tags

    def test_page_tags_recorded(self, graph, page_with_tags):
        graph.add_page(page_with_tags)
        tags_found = [tag for tag in graph.page_tags if tag in page_with_tags.tags]

        assert len(tags_found) == len(page_with_tags.tags)

    def test_page_names_returned_with_tags(self, graph, page_with_tags):
        graph.add_page(page_with_tags)
        page_tags = graph.page_tags

        for tag in page_with_tags.tags:
            assert page_tags[tag]
            assert page_with_tags.name in page_tags[tag]

    def test_placeholders_created_for_tags(self, graph, page_with_tags):
        graph.add_page(page_with_tags)
        pages = graph.pages

        for tag in page_with_tags.tags:
            assert tag in pages


class TestGraphTagLinks:
    def test_placeholders_created_for_tags(self, graph, page_with_tag_link):
        page, tag_link = page_with_tag_link
        graph.add_page(page)

        assert tag_link.target in graph.pages


class TestGraphPageNamespaces:
    def test_page_created_for_namespace(self, graph: Graph, page_in_namespace: Page):
        graph.add_page(page_in_namespace)

        assert page_in_namespace.namespace in graph.pages

    def test_recursive_namespace_pages(self, graph: Graph, page_in_namespace: Page):
        graph.add_page(page_in_namespace)
        namespace = Path(page_in_namespace.namespace)

        while str(namespace) != NAMESPACE_SELF:
            assert str(namespace) in graph.pages
            namespace = namespace.parent


class TestLoadGraphPages:
    def test_load_empty_graph(self, path_to_graph):
        graph = load_graph(path_to_graph)

        assert not graph.pages
