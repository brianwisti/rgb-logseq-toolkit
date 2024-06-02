"""Test handling complete Logseq graphs."""

import pytest

from rgb_logseq.graph import DuplicatePageNameError, Graph


@pytest.fixture
def graph():
    """Return an empty Graph."""
    return Graph()


class TestGraphPages:
    def test_empty_graph(self):
        graph = Graph()

        assert not graph.pages


class TestGraphPageManagement:
    def test_check_for_page_not_in_graph(self, graph, page):
        assert not graph.has_page(page.name)

    def test_add_and_check_for_page(self, graph, page):
        graph.add_page(page)

        assert graph.has_page(page.name)

    def test_adding_placeholder_pages(self, graph, page_name):
        graph.add_placeholder(page_name)

        assert graph.has_page(page_name)

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
