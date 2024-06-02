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
PAGE_SCHEMA = """
    create node table Page(
        name string,
        is_placeholder boolean,
        is_public boolean,
        primary key (name)
    )
"""

PROPERTY_SCHEMA = """
    create node table Property(
        name string,
        primary key(name)
    )
"""

LINKS_SCHEMA = """
    create rel table Links(
        from Page to Page
    )
"""

PAGE_PROPERTIES_SCHEMA = """
    create rel table PageHasProperty(
        from Page to Property,
        value string
    )
"""

PAGE_FOLDERS = ["journals", "pages"]
PAGE_GLOB = "./**/*.md"
load_dotenv()


def create_db() -> kuzu.Connection:
    db = kuzu.Database(DB_NAME)
    conn = kuzu.Connection(db)
    conn.execute(PAGE_SCHEMA)
    conn.execute(LINKS_SCHEMA)
    conn.execute(PROPERTY_SCHEMA)
    conn.execute(PAGE_PROPERTIES_SCHEMA)

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


def write_as_csv(df: polars.DataFrame, filename: str) -> None:
    """Write a DataFrame as CSV to the specified file."""
    df.write_csv(filename, include_header=False, quote_style="non_numeric")


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv(GRAPH_PATH_ENV)
    assert graph_path

    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    graph_name = pages_path.stem
    logger.info("Loaded graph %s; %s pages", graph_name, len(graph.pages))

    pages = [
        {
            "name": page.name,
            "is_placeholder": page.is_placeholder,
            "is_public": page.is_public,
        }
        for page in graph.pages.values()
    ]
    pages_df = polars.DataFrame(pages)
    links_df = polars.DataFrame(graph.links)

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

    page_csv_file = "page.csv"
    links_csv_file = "links.csv"
    property_csv_file = "property.csv"
    page_props_csv_file = "page_properties.csv"

    write_as_csv(pages_df, page_csv_file)
    write_as_csv(links_df, links_csv_file)
    write_as_csv(properties_df, property_csv_file)
    write_as_csv(page_props_df, page_props_csv_file)

    conn = create_db()
    # XXX: Does parameter binding not work for COPY?
    conn.execute(f'COPY Page from "{page_csv_file}"')
    conn.execute(f'COPY Links from "{links_csv_file}"')
    conn.execute(f'COPY Property from "{property_csv_file}"')
    conn.execute(f'COPY PageHasProperty from "{page_props_csv_file}"')


if __name__ == "__main__":
    main()
