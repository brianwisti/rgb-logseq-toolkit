"""Pytest shared support logic for testing."""

from dataclasses import dataclass
import pytest

from rgb_logseq import line
from rgb_logseq.block import find_blocks
from rgb_logseq.link import GraphLink
from rgb_logseq.page import parse_page_text
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


def as_branch_block(text: str):
    """Return text argument reformatted as a Logseq branch block"""
    return f"- {text}"


def as_multiline_block(lines: list[str]):
    """Return a list of strings as a single multiline block."""
    first_line = as_branch_block(lines[0])
    remaining_lines = "\n".join(as_branch_continuation(line) for line in lines[1:])
    return "n".join([first_line, remaining_lines])


def as_page_link(link: GraphLink):
    """Return a string indicating a page link to the GraphLink target."""
    return f"[[{link.target}]]"


def as_separate_branch_blocks(lines: list[str]):
    """Return a list of strings as a multiline string of branch blocks."""
    return "\n".join([as_branch_block(line) for line in lines])


def as_branch_continuation(text: str):
    """Return a string indented with ``MARK_BLOCK_CONTINUATION``."""
    return f"  {text}"


def generate_graph_link(faker):
    """Return a GraphLink usable by fixtures."""
    target = generate_page_name(faker)

    return GraphLink(target=target)


def generate_page_name(faker):
    """Return a string appropriate for graph page names."""
    return faker.word()


def generate_text_line(faker):
    """Return a line of text usable by fixtures."""
    return faker.sentence()


# pylint: disable=redefined-outer-name


@pytest.fixture
def branch_block(text_line):
    """Return a one-line branch Block."""
    branch_block_line = as_branch_block(text_line)
    return find_blocks(branch_block_line)[0]


@pytest.fixture
def code_fence():
    """Return a Markdown code fence indicator."""
    return "```"


@pytest.fixture
def graph_link(page_name):
    """Return a direct link to a graph page."""
    return GraphLink(target=page_name)


@pytest.fixture
def graph_links(range_cap, faker):
    """Return a list of GraphLink objects."""
    return [generate_graph_link(faker) for _ in range(range_cap)]


@pytest.fixture
def labeled_graph_link(page_name, faker):
    """Return a link to a graph page using a custom label."""
    label = faker.word()
    return GraphLink(target=page_name, link_text=label)


@pytest.fixture
def line_with_link(graph_link):
    parsed = line.parse_line(as_page_link(graph_link))

    return (parsed, graph_link)


@pytest.fixture
def page(branch_block, page_name):
    return parse_page_text(branch_block.raw, name=page_name)


@pytest.fixture
def another_page(branch_block, page_name):
    return parse_page_text(branch_block.raw, name=page_name)


@pytest.fixture
def linked_pages(page, graph_link, page_name):
    graph_link.target = page.name
    link_block = as_branch_block(graph_link.raw)
    linked_page = parse_page_text(link_block, name=page_name)

    return page, linked_page, graph_link


@pytest.fixture
def range_cap(faker):
    """Return an arbitrary limit on range for test collections."""
    return faker.random_int(min=2, max=RANGE_MAX)


@pytest.fixture
def quote_directive_pair():
    """Return a DirectivePair for quote blocks."""
    return DirectivePair(directive="QUOTE")


@pytest.fixture
def empty_line():
    """Return an empty string."""
    return ""


@pytest.fixture
def text_line(faker):
    """Generate and return a line of text."""
    return generate_text_line(faker)


@pytest.fixture
def text_lines(faker, range_cap):
    """Return a list of generated sentences."""
    return [generate_text_line(faker) for _ in range(range_cap)]


@pytest.fixture
def root_block_line(text_line):
    """Return a Line with depth 0."""
    return line.parse_line(text_line)


@pytest.fixture
def branch_block_line(text_line):
    """Return a Line that opens a block."""
    raw_text = as_branch_block(text_line)
    return line.parse_line(raw_text)


@pytest.fixture
def scalar_property(faker):
    """Return a Property with a single string value."""
    field = faker.word()
    value = faker.word()

    return Property.loads(f"{field}:: {value}")


@pytest.fixture
def public_prop():
    return Property.loads("public:: true")


@pytest.fixture
def multiline_block_lines(text_lines):
    """Return a list of Line objects that describe one block."""
    first_line = line.parse_line(f"- {text_lines[0]}")
    remaining_lines = [
        line.parse_line(f"  {text_line}") for text_line in text_lines[1:]
    ]
    return [first_line] + remaining_lines


@pytest.fixture
def page_name(faker):
    """Return an appropriate name for a Logseq page."""
    return faker.word()
