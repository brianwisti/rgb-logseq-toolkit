"""Pytest shared support logic for testing."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest
from faker import Faker
from rgb_logseq import line
from rgb_logseq.block import Block, find_blocks
from rgb_logseq.graph import Graph
from rgb_logseq.link import PATH_ASSETS, DirectLink, ResourceLink
from rgb_logseq.page import Page, parse_page_text
from rgb_logseq.property import Property

RANGE_MAX = 20


@dataclass
class DirectivePair:
    """Holds strings to open and close a directive block."""

    directive: str

    @property
    def opener(self) -> str:
        """Return a string indicating the start of a directive."""
        return f"#+BEGIN_{self.directive}"

    @property
    def closer(self) -> str:
        """Return a string indicating the end of a directive."""
        return f"#+END_{self.directive}"


@dataclass
class LinkedPages:
    """Holds two Pages connected by a DirectLink."""

    link_source: Page
    link_target: Page
    link: DirectLink


def as_branch_block(text: str) -> str:
    """Return text argument reformatted as a Logseq branch block"""
    return f"- {text}"


def as_multiline_block(lines: list[str]) -> str:
    """Return a list of strings as a single multiline block."""
    first_line = as_branch_block(lines[0])
    remaining_lines = "\n".join(as_branch_continuation(line) for line in lines[1:])

    return "\n".join([first_line, remaining_lines])


def as_page_link(link: DirectLink) -> str:
    """Return a string indicating a page link to the DirectLink target."""

    return f"[[{link.target}]]"


def as_separate_branch_blocks(lines: list[str]) -> str:
    """Return a list of strings as a multiline string of branch blocks."""
    return "\n".join([as_branch_block(line) for line in lines])


def as_branch_continuation(text: str) -> str:
    """Return a string indented with ``MARK_BLOCK_CONTINUATION``."""
    return f"  {text}"


def generate_graph_link(faker: Faker) -> DirectLink:
    """Return a DirectLink usable by fixtures."""
    target = generate_page_name(faker)

    return DirectLink.to_page(target)


def generate_page_name(faker: Faker) -> str:
    """Return a string appropriate for graph page names."""
    return str(faker.unique.word())


def generate_text_line(faker: Faker) -> str:
    """Return a line of text usable by fixtures."""
    return str(faker.unique.sentence())


# pylint: disable=redefined-outer-name


@pytest.fixture
def asset_path(faker: Faker) -> PurePosixPath:
    return PurePosixPath(PATH_ASSETS) / faker.file_name()


@pytest.fixture
def branch_block(text_line: str) -> Block:
    """Return a one-line branch Block."""
    branch_block_line = as_branch_block(text_line)

    return find_blocks(branch_block_line)[0]


@pytest.fixture
def code_fence() -> str:
    """Return a Markdown code fence indicator."""
    return "```"


@pytest.fixture
def graph():
    """Return an empty Graph."""
    return Graph()


@pytest.fixture
def graph_link(page_name: str) -> DirectLink:
    """Return a direct link to a graph page."""
    return DirectLink.to_page(page_name)


@pytest.fixture
def graph_links(range_cap: int, faker: Faker) -> list[DirectLink]:
    """Return a list of DirectLink objects."""
    return [generate_graph_link(faker) for _ in range(range_cap)]


@pytest.fixture
def graph_name():
    """Return a name usable for test graphs."""
    return "test-graph"


@pytest.fixture
def labeled_graph_link(page_name: str, faker: Faker) -> DirectLink:
    """Return a link to a graph page using a custom label."""
    label = faker.word()

    return DirectLink.to_page(page_name, link_text=label)


@pytest.fixture
def line_with_link(graph_link: DirectLink) -> tuple[line.Line, DirectLink]:
    parsed = line.parse_line(as_page_link(graph_link))

    return (parsed, graph_link)


@pytest.fixture
def namespace(faker: Faker, range_cap: int) -> str:
    """Return a namespace path string."""
    return "/".join([faker.unique.word() for _ in range(range_cap)])


@pytest.fixture
def page(branch_block: Block, faker: Faker) -> Page:
    return parse_page_text(branch_block.raw, name=generate_page_name(faker))


@pytest.fixture
def page_in_namespace(page: Page, namespace: str) -> Page:
    """Return a Page that belongs in a namespace hierarchy."""
    page.name = namespace

    return page


@pytest.fixture
def page_with_heading(faker: Faker) -> Page:
    """Return a Page with a heading block."""
    heading_text = faker.sentence()
    heading_block = "\n".join(
        [
            f"- {heading_text}",
            "  heading:: true",
        ]
    )

    return parse_page_text(heading_block, name=generate_page_name(faker))


@pytest.fixture
def page_with_tag_link(word, faker):
    tag_link = DirectLink.as_tag(word)
    text_line = f"- #{word}"
    page = parse_page_text(text_line, name=generate_page_name(faker))

    return page, tag_link


@pytest.fixture
def page_with_tags(page: Page, prop_tags: Property) -> Page:
    """Return a Page with tags."""
    page.properties["tags"] = prop_tags
    return page


@pytest.fixture
def path_to_graph(graph_name, fs) -> Path:
    """Create a graph folder structure without pages on a fake filesystem."""
    path = Path(graph_name)
    fs.create_dir(path)
    fs.create_dir(path / "pages")

    return path


@pytest.fixture
def path_to_page(path_to_graph, page_name, branch_block_line, fs):
    """Create a page on a fake filesystem."""
    path = path_to_graph / "pages" / f"{page_name}.md"
    fs.create_file(path, contents=branch_block_line.raw)

    return path


@pytest.fixture
def public_page(prop_public: Property, page_name: str) -> Page:
    return parse_page_text(prop_public.raw, name=page_name)


@pytest.fixture
def tag_link(page_name: str) -> DirectLink:
    """Return a tag link to a graph page."""
    return DirectLink.as_tag(page_name)


@pytest.fixture
def word(faker: Faker) -> str:
    """Return a random unique word."""
    return str(faker.unique.word())


@pytest.fixture
def another_page(branch_block: Block, faker: Faker) -> Page:
    return parse_page_text(branch_block.raw, name=generate_page_name(faker))


@pytest.fixture
def linked_pages(page: Page, graph_link: DirectLink, faker: Faker) -> LinkedPages:
    graph_link.target = page.name
    link_text = as_page_link(graph_link)
    link_block = as_branch_block(link_text)
    link_source = parse_page_text(link_block, name=generate_page_name(faker))

    return LinkedPages(link_source=link_source, link_target=page, link=graph_link)


@pytest.fixture
def range_cap(faker: Faker) -> int:
    """Return an arbitrary limit on range for test collections."""
    return int(faker.random_int(min=2, max=RANGE_MAX))


@pytest.fixture
def resource_link(faker: Faker) -> ResourceLink:
    target = faker.uri()
    link_text = faker.word()

    return ResourceLink(target=target, link_text=link_text)


@pytest.fixture
def quote_directive_pair() -> DirectivePair:
    """Return a DirectivePair for quote blocks."""
    return DirectivePair(directive="QUOTE")


@pytest.fixture
def empty_line() -> str:
    """Return an empty string."""
    return ""


@pytest.fixture
def text_line(faker: Faker) -> str:
    """Generate and return a line of text."""
    return generate_text_line(faker)


@pytest.fixture
def text_lines(faker: Faker, range_cap: int) -> list[str]:
    """Return a list of generated sentences."""
    return [generate_text_line(faker) for _ in range(range_cap)]


@pytest.fixture
def root_block_line(text_line: str) -> line.Line:
    """Return a Line with depth 0."""
    return line.parse_line(text_line)


@pytest.fixture
def branch_block_line(text_line: str) -> line.Line:
    """Return a Line that opens a block."""
    raw_text = as_branch_block(text_line)

    return line.parse_line(raw_text)


@pytest.fixture
def prop_heading() -> Property:
    """Return a Property indicating a heading block."""
    return Property.loads("heading:: true")


@pytest.fixture
def prop_scalar(faker: Faker) -> Property:
    """Return a Property with a single string value."""
    field = faker.word()
    value = faker.word()

    return Property.loads(f"{field}:: {value}")


@pytest.fixture
def prop_public() -> Property:
    return Property.loads("public:: true")


@pytest.fixture
def prop_tags(faker: Faker, range_cap: int) -> Property:
    """Return a tags Property with a comma-separated list of tags."""
    tags = ",".join([faker.unique.word() for _ in range(range_cap)])

    return Property.loads(f"tags:: {tags}")


@pytest.fixture
def multiline_block_lines(text_lines: list[str]) -> list[line.Line]:
    """Return a list of Line objects that describe one block."""
    first_line = line.parse_line(f"- {text_lines[0]}")
    remaining_lines = [
        line.parse_line(f"  {text_line}") for text_line in text_lines[1:]
    ]
    return [first_line] + remaining_lines


@pytest.fixture
def page_name(faker: Faker) -> str:
    """Return an appropriate name for a Logseq page."""
    return generate_page_name(faker)
