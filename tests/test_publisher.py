"""Automated tests for graph export to SSG."""

import pytest

from rgb_logseq.publisher import Publisher, page_slug


class TestPageSlug:
    @pytest.mark.parametrize(
        "name, export_path",
        [("Page", "page"), ("My Page", "my-page")],
    )
    def test_path_is_slugified(self, name, export_path):
        assert page_slug(name) == export_path

    @pytest.mark.parametrize("name, export_path", [("Post/My Post", "post/my-post")])
    def test_path_reflects_namespace(self, name, export_path):
        assert page_slug(name) == export_path


class TestPublisher:
    def test_page_map(self, graph, page):
        graph.add_page(page)
        publisher = Publisher(graph=graph)

        assert publisher.page_map
        assert publisher.page_map[page.name] == page_slug(page.name)
