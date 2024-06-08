"""Test graph links."""

from rgb_logseq.link import BlockLink, DirectLink, LinkType


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
