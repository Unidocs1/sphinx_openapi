# models/schema_info.py
from pathlib import Path


class SchemaInfo:
    """
    Represents an OpenAPI schema with its source URL and destination file path.
    """

    def __init__(self, url: str, dest: Path) -> None:
        self.url: str = url
        self.dest: Path = dest
