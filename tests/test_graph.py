"""Test handling complete Logseq graphs."""

import pytest

from rgb_logseq.graph import Graph


@pytest.fixture
def graph():
    """Return an empty Graph."""
    return Graph()


class TestGraphPages:
    def test_empty_graph(self):
        graph = Graph()

        assert not graph.pages


class TestGraphHasPage:
    def test_with_page_in_graph(self, graph, page):
        graph.add_page(page)

        assert graph.has_page(page.name)

    def test_with_page_not_in_graph(self, graph, page):
        assert not graph.has_page(page.name)


class TestGraphAddPage:
    def test_add_page(self, graph, page):
        graph.add_page(page)

        assert page.name in graph.pages

    def test_placeholders_added_for_page_links(self, graph, linked_pages):
        link_source = linked_pages.link_source
        link_target = linked_pages.link_target
        graph.add_page(link_source)

        assert link_target.name in graph.pages
        assert graph.pages[link_target.name].is_placeholder


class TestGraphLinks:
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

    def test_placeholder_page_added(self, graph, linked_pages):
        link_source = linked_pages.link_source
        link_target = linked_pages.link_target
        graph.add_page(link_source)

        assert link_target.name in graph.pages
