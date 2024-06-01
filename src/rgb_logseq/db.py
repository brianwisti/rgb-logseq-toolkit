"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
import logging
import os

from dotenv import load_dotenv
from rich.logging import RichHandler
import kuzu
import polars

from .graph import Graph
from .page import load_page_file

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
load_dotenv()


def load_graph(graph_path: Path) -> Graph:
    """Load pages in Graph."""
    logging.info("path: %s", graph_path)
    graph = Graph()
    page_folders = ["journals", "pages"]

    for folder in page_folders:
        subfolder = graph_path / folder
        for md_path in subfolder.glob("./**/*.md"):
            logging.debug("md path: %s", md_path)
            page = load_page_file(md_path)
            logging.debug("page: %s", page)
            graph.add_page(page)

    return graph


PAGE_SCHEMA = """
    create node table Page(
        name string,
        is_placeholder boolean,
        primary key (name)
    )
"""

LINKS_SCHEMA = """
    create rel table Links(
        from Page
        to Page
    )
"""


def create_db() -> kuzu.Connection:
    db = kuzu.Database("./graph_db")
    conn = kuzu.Connection(db)
    conn.execute(PAGE_SCHEMA)
    conn.execute(LINKS_SCHEMA)

    return conn


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv("GRAPH_PATH")
    assert graph_path

    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    graph_name = pages_path.stem
    logging.info("Loaded graph %s; %s pages", graph_name, len(graph.pages))
    # TODO: refactor page listing to Graph method
    pages = [
        {"name": page.name, "is_placeholder": page.is_placeholder}
        for page in graph.pages.values()
    ]
    links = graph.links
    polars.DataFrame(pages).write_csv("page.csv", include_header=False)
    polars.DataFrame(links).write_csv("links.csv", include_header=False)
    conn = create_db()
    conn.execute('COPY Page from "page.csv"')
    conn.execute('COPY Links from "links.csv"')


if __name__ == "__main__":
    main()
