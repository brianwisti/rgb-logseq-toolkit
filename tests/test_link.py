"""Test graph links."""

from rgb_logseq.link import DirectLink, TagLink


class TestDirectLink:
    def test_default_title_is_link(self, page_name):
        link = DirectLink(target=page_name)

        assert link.label == page_name

    def test_init_with_link_text(self, page_name, faker):
        link_text = faker.word()
        link = DirectLink(target=page_name, link_text=link_text)

        assert link.label == link_text


class TestTagLink:
    def test_link_text_is_ignored(self, page_name, faker):
        link_text = faker.word()
        tag_link = TagLink(target=page_name, link_text=link_text)

        assert tag_link.label == page_name
