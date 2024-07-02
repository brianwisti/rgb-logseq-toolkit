"""Automated tests for graph export to SSG."""

import pytest
from rgb_logseq.publisher import page_slug


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
