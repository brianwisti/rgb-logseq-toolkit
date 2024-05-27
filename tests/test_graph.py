"""Test handling complete Logseq graphs."""

import pytest

from rgb_logseq.graph import Graph


@pytest.fixture
def graph():
    """Return an empty Graph."""
    return Graph()


class TestGraph:
    def test_empty_graph(self):
        graph = Graph()

        assert not graph.pages

    def test_add_page(self, graph, page):
        graph.add_page(page)

        assert page.name in graph.pages
