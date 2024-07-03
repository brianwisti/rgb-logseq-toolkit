"""Functions and classes for exporting to a static site generator."""

import json
from pathlib import Path

import kuzu
from pydantic import BaseModel, Field
from slugify import slugify

from .const import logger
from .db import connect

PageMap = dict[str, dict[str, str | bool]]


class Publisher(BaseModel):
    """Manages publishing a complete graph to SSG content folder."""

    model_config = {"arbitrary_types_allowed": True}
    output_dir: Path
    conn: kuzu.Connection = Field(default_factory=connect)

    def publish(self) -> None:
        """Export the graph to the output directory."""
        page_map = self.__load_page_map()
        logger.info("Loaded %s pages", len(page_map))

        for page_name, page_info in page_map.items():
            if page_info["is_placeholder"]:
                continue

            page_slug = page_info["slug"]
            page_content = self.__load_page_content(page_name)
            page_properties = self.__load_page_properties(page_name)

            if page_properties:
                logger.debug("Adding properties to %s: %s", page_slug, page_properties)
                post.metadata.update(page_properties)

            logger.info("Post metadata: %s", post.metadata)

    def __load_page_content(self, page_name: str) -> str:
        """Return the content of a page."""
        # Extract page content by recursively extracting blocks.
        last_depth = 0
        content = ""
        block_query = """
            MATCH
                (:Page {name: $page_name})-[h:Holds]->(block:Block)
            RETURN
                h.position,
                h.depth,
                COUNT { MATCH (block)-[:Holds]->(subblock:Block) },
                block
            ORDER BY h.position
        """
        block_result = self.conn.execute(block_query, {"page_name": page_name})

        while block_result.has_next():
            pos, depth, child_count, block = block_result.get_next()

            if not block["content"]:
                continue

            logger.debug(block)
            block_uuid = block["uuid"]
            content_lines = []
            content_lines.append(f"<Block id='{block_uuid}'>")

            if block["is_heading"]:
                heading_level = depth + 1
                content_lines.append(
                    f"<Heading level={heading_level}>{block['content']}</Heading>"
                )
            else:
                content_lines.append(block["content"])

                if not child_count or depth < last_depth:
                    content_lines.append("</Block>")

            content += "\n".join(content_lines) + "\n"

            if depth != last_depth:
                last_depth = depth

        return content

    def __load_page_map(self) -> PageMap:
        """Return a mapping of page names to their content."""
        page_map = {}
        page_map_query = """
            MATCH
                (p:Page {is_public: true})
            RETURN
                p.name,
                p.is_placeholder
        """
        page_map_result = self.conn.execute(page_map_query)

        while page_map_result.has_next():
            name, is_placeholder = page_map_result.get_next()

            page_map[name] = {
                "is_placeholder": is_placeholder,
                "slug": page_slug(name),
            }

        return page_map

    def __load_page_properties(self, page_name: str) -> dict[str, str]:
        """Return the properties of a page."""
        list_props = ["tags"]
        link_props = ["date"]

        page_title = Path(page_name).stem
        page_properties = {"title": page_title}
        page_query = """
            MATCH
                (p:Page {name: $page_name})-[h:HasProperty]->(prop:Page)
            WHERE
                prop.name <> "public" AND
                h.value <> "-"
            RETURN
                prop.name,
                h.value
        """
        page_result = self.conn.execute(page_query, {"page_name": page_name})
        prop_count = page_result.get_num_tuples()
        logger.debug("Found %s properties for %s", prop_count, page_name)

        while page_result.has_next():
            prop_name, prop_value = page_result.get_next()

            if not prop_name:
                # I'm not sure, but I think this is a Kuzu bug.
                logger.warning("empty property row returned for %s", page_name)
                continue

            if prop_name in list_props:
                prop_value = prop_value.split(", ")
            elif prop_name in link_props:
                prop_value = strip_wiki_link(prop_value)

            page_properties[prop_name] = prop_value

        logger.debug("Page properties loaded for %s: %s", page_name, page_properties)

        return page_properties


def page_slug(page_name: str) -> str:
    """Return the destination path for a given page name."""
    separator = "/"
    return separator.join([slugify(step) for step in page_name.split(separator)])


def strip_wiki_link(text: str) -> str:
    """Return the text without wiki links."""
    return text.replace("[[", "").replace("]]", "")


def main() -> None:
    """Run the publisher."""
    publisher = Publisher(output_dir=Path("content"))
    publisher.publish()


if __name__ == "__main__":
    main()
