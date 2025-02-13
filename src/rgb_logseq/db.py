"""Explore my Logseq graph in Kuzu."""

import os
import shutil
from pathlib import Path

import kuzu
from dotenv import load_dotenv

from .const import logger
from .graph import Graph, load_graph
from .graph_exporter import GraphExporter

GRAPH_PATH_ENV = "GRAPH_PATH"

DB_NAME = "graph_db"
DB_SCHEMA_PATH = Path("etc/schema.cypher")

load_dotenv()


def clear(db_name: str = DB_NAME) -> None:
    """Remove all data from the database."""
    db_path = Path(db_name)

    if db_path.is_dir():
        shutil.rmtree(db_path)
        logger.info("Database %s cleared.", db_name)


def connect(db_name: str = DB_NAME) -> kuzu.Connection:
    """Create the database for our Logseq graph and return a connection."""
    db = kuzu.Database(db_name)
    conn = kuzu.Connection(db)

    return conn


def populate_db(
    graph: Graph, conn: kuzu.Connection, schema_path: Path = DB_SCHEMA_PATH
) -> None:
    """Add page and block data to an empty Kuzu database."""
    schema = schema_path.read_text(encoding="utf-8")
    conn.execute(schema)
    exporter = GraphExporter(graph=graph)
    save_graph_pages(exporter, conn)
    save_graph_blocks(exporter, conn)


def save_graph_blocks(exporter: GraphExporter, conn: kuzu.Connection) -> None:
    """Store Blocks and their Page connections in CSV files."""

    blocks = exporter.blocks
    logger.info("Saving %s blocks", len(blocks))
    conn.execute(
        """
            COPY Block FROM (
                LOAD FROM blocks
                RETURN cast(uuid, 'UUID'), content, is_heading, directive
            )
        """
    )

    branches = exporter.block_branches
    logger.info("Saving %s block branches", len(branches))
    conn.execute(
        """
            COPY HOLDS_Block_Block FROM (
                LOAD FROM branches
                RETURN cast(parent, 'UUID'), cast(uuid, 'UUID'), position, depth
            )
        """
    )

    links = exporter.links
    logger.info("Saving %s direct links", len(links))
    conn.execute(
        """
            COPY LINKS FROM (
                LOAD FROM links
                RETURN cast(source, 'UUID'), target
            )
        """
    )

    block_properties = exporter.block_properties
    logger.info("Saving %s block properties", len(block_properties))
    conn.execute(
        """
            COPY HAS_PROPERTY_Block_Page FROM (
                LOAD FROM block_properties
                RETURN cast(block, 'UUID'), property, value
            )
        """
    )

    page_memberships = exporter.page_memberships
    logger.info("Saving %s page memberships", len(page_memberships))
    conn.execute(
        """
        COPY HOLDS_Page_Block FROM (
            LOAD FROM page_memberships
            RETURN page, cast(block, 'UUID'), position, depth
        )
        """
    )

    tag_links = exporter.tag_links
    logger.info("Saving %s tag links", len(tag_links))

    if len(tag_links):
        conn.execute(
            """
                COPY LINKS_AS_TAG FROM (
                    LOAD FROM tag_links
                    RETURN cast(source, 'UUID'), target
                )
            """
        )

    block_links = exporter.block_links
    logger.info("Saving %s block links", len(block_links))

    if len(block_links):
        conn.execute(
            """
                COPY LINKS_TO_BLOCK FROM (
                    LOAD FROM block_links
                    RETURN cast(source, 'UUID'), cast(target, 'UUID')
                )
            """
        )

    resources, resource_links = exporter.resource_links
    logger.info("Saving %s resources", len(resources))
    conn.execute("COPY Resource FROM (LOAD FROM resources RETURN *)")

    logger.info("Saving %s resource links", len(resource_links))

    if len(resource_links):
        conn.execute(
            """
                COPY LINKS_TO_RESOURCE FROM (
                    LOAD FROM resource_links
                    RETURN cast(source, 'UUID'), target, label
                )
            """
        )

    logger.info("Finished saving block data.")


def save_graph_pages(exporter: GraphExporter, conn: kuzu.Connection) -> None:
    """Store page info from graph in a CSV file."""

    pages = exporter.pages
    logger.info("Saving %s pages", len(pages))
    conn.execute("COPY Page FROM (LOAD FROM pages RETURN *)")

    namespaces = exporter.namespaces
    logger.info("Saving %s namespaces", len(namespaces))
    conn.execute("COPY IN_NAMESPACE FROM (LOAD FROM namespaces RETURN *)")

    page_properties = exporter.page_properties
    logger.info("Saving %s page properties", len(page_properties))
    conn.execute(
        "COPY HAS_PROPERTY_Page_Page FROM (LOAD FROM page_properties RETURN *)"
    )

    tags = exporter.page_tags
    logger.info("Saving %s tags", len(tags))
    conn.execute("COPY IS_TAGGED_Page_Page FROM (LOAD FROM tags RETURN *)")

    logger.info("Database populated with page data.")


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv(GRAPH_PATH_ENV)
    assert graph_path

    clear()
    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    conn = connect(DB_NAME)
    populate_db(graph, conn)


if __name__ == "__main__":
    main()
