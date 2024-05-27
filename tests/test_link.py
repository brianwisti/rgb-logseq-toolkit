"""Test graph links."""

from rgb_logseq.link import GraphLink, GraphLinkType


class TestGraphLink:
    def test_default_title_is_link(self, page_name):
        link = GraphLink(target=page_name)

        assert link.label == page_name

    def test_default_type_is_link(self, page_name):
        link = GraphLink(target=page_name)

        assert link.link_type == GraphLinkType.link

    def test_init_with_link_text(self, page_name, faker):
        link_text = faker.word()
        link = GraphLink(target=page_name, link_text=link_text)

        assert link.label == link_text
