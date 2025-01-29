"""Test graph links."""

import pytest
from pydantic import ValidationError

from rgb_logseq.link import BlockLink, DirectLink, LinkType, ResourceLink


class TestDirectLink:
    def test_default_title_is_link(self, page_name):
        link = DirectLink(target=page_name, link_type=LinkType.PAGE)

        assert link.label == page_name

    def test_to_page(self, page_name):
        link = DirectLink.to_page(page_name)

        assert link.target == page_name
        assert link.link_type == LinkType.PAGE

    def test_as_tag(self, word):
        link = DirectLink.as_tag(word)

        assert link.target == word
        assert link.link_type == LinkType.TAG

    def test_init_with_link_text(self, page_name, faker):
        link_text = faker.word()
        link = DirectLink(
            target=page_name, link_text=link_text, link_type=LinkType.PAGE
        )

        assert link.label == link_text


class TestBlockLink:
    def test_to_block(self, branch_block):
        link = BlockLink(target=branch_block.id)

        assert link.target == branch_block.id


class TestResourceLink:
    def test_link_text_is_required(self, faker):
        with pytest.raises(ValidationError):
            _ = ResourceLink(target=faker.word(), link_text="")

    def test_local_file_is_asset(self, asset_path):
        link_text = asset_path.name
        link = ResourceLink(target=str(asset_path), link_text=link_text)

        assert link.is_asset_file

    def test_uri_is_not_asset(self, faker):
        link_text = faker.word()
        link = ResourceLink(target=faker.uri(), link_text=link_text)

        assert not link.is_asset_file

    def test_external_file_is_error(self, faker):
        link_text = faker.word()
        link_path = faker.file_path()
        with pytest.raises(ValidationError):
            _ = ResourceLink(target=link_path, link_text=link_text, is_embed=True)

    @pytest.mark.parametrize(
        "link_path", ["/index.xml", "/post/index.xml", "/journal/index.xml"]
    )
    def test_rss_feed_exemption(self, link_path):
        assert ResourceLink(target=link_path, link_text=link_path)
