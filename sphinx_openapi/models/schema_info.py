# models/schema_info.py
from pathlib import Path


class SchemaInfo:
    """
    Represents an OpenAPI schema with its source (URL or file path) 
    and destination file path.
    """

    def __init__(self, source: str, dest: Path) -> None:
        self.source: str = source
        self.dest: Path = dest
