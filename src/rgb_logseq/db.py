"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
import os

from dotenv import load_dotenv
import kuzu

from .const import logger
from .graph import Graph, load_graph, load_graph_blocks, load_graph_pages

GRAPH_PATH_ENV = "GRAPH_PATH"

DB_NAME = "graph_db"
DB_SCHEMA_PATH = Path("etc/schema.cypher")

load_dotenv()


def create_db(db_name: str, schema_path: Path) -> kuzu.Connection:
    """Create the database for our Logseq graph and return a connection."""
    db = kuzu.Database(db_name)
    conn = kuzu.Connection(db)
    schema = schema_path.read_text(encoding="utf-8")
    conn.execute(schema)

    return conn


def populate_db(graph: Graph, conn: kuzu.Connection) -> None:
    """Add page and block data to an empty Kuzu database."""
    save_graph_pages(graph, conn)
    save_graph_blocks(graph, conn)


def save_graph_blocks(graph: Graph, conn: kuzu.Connection) -> None:
    """Store Blocks and their Page connections in CSV files."""
    graph_block_info = load_graph_blocks(graph)

    blocks = graph_block_info["blocks"]
    logger.info("Saving %s blocks", len(blocks))
    conn.execute(
        """
            COPY Block FROM (
                LOAD FROM blocks
                RETURN cast(uuid, 'UUID'), content, is_heading, directive
            )
        """
    )

    branches = graph_block_info["branches"]
    logger.info("Saving %s block branches", len(branches))
    conn.execute(
        """
            COPY Holds_Block_Block FROM (
                LOAD FROM branches
                RETURN cast(parent, 'UUID'), cast(uuid, 'UUID'), position, depth
            )
        """
    )

    links = graph_block_info["links"]
    logger.info("Saving %s direct links", len(links))
    conn.execute(
        """
            COPY Links FROM (
                LOAD FROM links
                RETURN cast(source, 'UUID'), target
            )
        """
    )

    block_properties = graph_block_info["block_properties"]
    logger.info("Saving %s block properties", len(block_properties))
    conn.execute(
        """
            COPY HasProperty_Block_Page FROM (
                LOAD FROM block_properties
                RETURN cast(block, 'UUID'), prop, value
            )
        """
    )

    page_memberships = graph_block_info["page_memberships"]
    logger.info("Saving %s page memberships", len(page_memberships))
    conn.execute(
        """
        COPY Holds_Page_Block FROM (
            LOAD FROM page_memberships
            RETURN page, cast(block, 'UUID'), position, depth
        )
        """
    )

    tag_links = graph_block_info["tag_links"]
    logger.info("Saving %s tag links", len(tag_links))

    if len(tag_links):
        conn.execute(
            """
                COPY LinksAsTag FROM (
                    LOAD FROM tag_links
                    RETURN cast(source, 'UUID'), target
                )
            """
        )

    block_links = graph_block_info["block_links"]
    logger.info("Saving %s block links", len(block_links))

    if len(block_links):
        conn.execute(
            """
                COPY LinksToBlock FROM (
                    LOAD FROM block_links
                    RETURN cast(source, 'UUID'), cast(target, 'UUID')
                )
            """
        )

    resources = graph_block_info["resources"]
    logger.info("Saving %s resources", len(resources))
    conn.execute("COPY Resource FROM (LOAD FROM resources RETURN *)")

    resource_links = graph_block_info["resource_links"]
    logger.info("Saving %s resource links", len(resource_links))

    if len(resource_links):
        conn.execute(
            """
                COPY LinksToResource FROM (
                    LOAD FROM resource_links
                    RETURN cast(source, 'UUID'), target, label
                )
            """
        )

    logger.info("Finished saving block data.")


def save_graph_pages(graph: Graph, conn: kuzu.Connection) -> None:
    """Store page info from graph in a CSV file."""
    page_data = load_graph_pages(graph)

    pages = page_data["pages"]
    logger.info("Saving %s pages", len(pages))
    conn.execute("COPY Page FROM (LOAD FROM pages RETURN *)")

    namespaces = page_data["namespaces"]
    logger.info("Saving %s namespaces", len(namespaces))
    conn.execute("COPY InNamespace FROM (LOAD FROM namespaces RETURN *)")

    page_properties = page_data["page_properties"]
    logger.info("Saving %s page properties", len(page_properties))
    conn.execute("COPY HasProperty_Page_Page FROM (LOAD FROM page_properties RETURN *)")

    tags = page_data["tags"]
    logger.info("Saving %s tags", len(tags))
    conn.execute("COPY PageIsTagged FROM (LOAD FROM tags RETURN *)")

    logger.info("Database populated with page data.")


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv(GRAPH_PATH_ENV)
    assert graph_path

    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    conn = create_db(DB_NAME, DB_SCHEMA_PATH)
    populate_db(graph, conn)


if __name__ == "__main__":
    main()
