"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
import os

from dotenv import load_dotenv
import kuzu
import polars

from .const import logger
from .graph import Graph
from .page import load_page_file

DB_NAME = "graph_db"
GRAPH_PATH_ENV = "GRAPH_PATH"
DB_SCHEMA = """
create node table Page(
    name string,
    is_placeholder boolean,
    is_public boolean,
    primary key (name)
);

create node table Property(
    name string,
    primary key(name)
);

create rel table Links(
    from Page to Page
);

create rel table PageHasProperty(
    from Page to Property,
    value string
);

create rel table PageIsTagged(
    from Page to Page
)
"""


PAGE_FOLDERS = ["journals", "pages"]
PAGE_GLOB = "./**/*.md"

CSV_FILE_PAGE = "page.csv"
CSV_FILE_LINKS = "links.csv"
CSV_FILE_PROPERTY = "property.csv"
CSV_FILE_PAGE_PROPS = "page_properties.csv"
CSV_FILE_PAGE_IS_TAGGED = "page_is_tagged.csv"

load_dotenv()


def create_db() -> kuzu.Connection:
    db = kuzu.Database(DB_NAME)
    conn = kuzu.Connection(db)
    conn.execute(DB_SCHEMA)

    return conn


def load_graph(graph_path: Path) -> Graph:
    """Load pages in Graph."""
    logger.info("path: %s", graph_path)
    graph = Graph()

    for folder in PAGE_FOLDERS:
        subfolder = graph_path / folder
        for md_path in subfolder.glob(PAGE_GLOB):
            logger.debug("md path: %s", md_path)
            page = load_page_file(md_path)
            logger.debug("page: %s", page)
            graph.add_page(page)

    return graph


def populate_database(conn: kuzu.Connection) -> None:
    """Copy graph info from CSV files to database."""
    # XXX: Does parameter binding not work for COPY?
    conn.execute(f'COPY Page from "{CSV_FILE_PAGE}"')
    conn.execute(f'COPY Links from "{CSV_FILE_LINKS}"')
    conn.execute(f'COPY Property from "{CSV_FILE_PROPERTY}"')
    conn.execute(f'COPY PageHasProperty from "{CSV_FILE_PAGE_PROPS}"')
    conn.execute(f'COPY PageIsTagged from "{CSV_FILE_PAGE_IS_TAGGED}"')


def save_graph_links(graph: Graph, filename: str) -> None:
    """Store direct link info from graph in a CSV file."""
    links_df = polars.DataFrame(graph.links)
    write_as_csv(links_df, filename)


def save_graph_page_props(
    graph: Graph, prop_filename: str, page_prop_filename: str
) -> None:
    """Store page properties from graph in CSV files."""
    page_properties = set()
    pages_with_properties = []

    for prop, pages_with_prop in graph.page_properties.items():
        page_properties.add(prop)
        # Tweaking nested strings until Kuzu issue #3461 is resolved.
        # - https://github.com/kuzudb/kuzu/issues/3461
        pages_with_properties += [
            {"from": page, "to": prop, "value": value.replace('"', "*")}
            for page, value in pages_with_prop.items()
        ]

    properties_df = polars.DataFrame(list(page_properties))
    page_props_df = polars.DataFrame(pages_with_properties)
    write_as_csv(properties_df, prop_filename)
    write_as_csv(page_props_df, page_prop_filename)


def save_graph_page_tags(graph: Graph, filename: str) -> None:
    """Store page tags from graph in a CSV file."""
    page_tags = []

    for tag, pages_with_tags in graph.page_tags.items():
        for page in pages_with_tags:
            info = {"from": page, "to": tag}
            page_tags.append(info)

    page_tags_df = polars.DataFrame(page_tags)
    write_as_csv(page_tags_df, filename)


def save_graph_pages(graph: Graph, filename: str) -> None:
    """Store page info from graph in a CSV file."""
    pages = [
        {
            "name": page.name,
            "is_placeholder": page.is_placeholder,
            "is_public": page.is_public,
        }
        for page in graph.pages.values()
    ]
    pages_df = polars.DataFrame(pages)
    write_as_csv(pages_df, filename)


def write_as_csv(df: polars.DataFrame, filename: str) -> None:
    """Write a DataFrame as CSV to the specified file."""
    df.write_csv(filename, include_header=False, quote_style="non_numeric")


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv(GRAPH_PATH_ENV)
    assert graph_path

    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    logger.info("Loaded graph %s; %s pages", pages_path.stem, len(graph.pages))

    save_graph_pages(graph, CSV_FILE_PAGE)
    save_graph_links(graph, CSV_FILE_LINKS)
    save_graph_page_props(graph, CSV_FILE_PROPERTY, CSV_FILE_PAGE_PROPS)
    save_graph_page_tags(graph, CSV_FILE_PAGE_IS_TAGGED)

    conn = create_db()
    populate_database(conn)


if __name__ == "__main__":
    main()
