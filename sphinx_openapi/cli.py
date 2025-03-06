# sphinx_openapi/cli.py
import argparse
from pathlib import Path
from types import SimpleNamespace

from sphinx_openapi import SphinxOpenApi
from models.schema_info import SchemaInfo

class DummyApp:
    """
    Minimal dummy Sphinx app for CLI mode.
    Only implements the attributes and methods required by SphinxOpenApi.
    """
    def __init__(self, config: SimpleNamespace) -> None:
        self.config = config

    def connect(self, *args, **kwargs) -> None:
        pass

def main() -> None:
    """
    CLI entry point for downloading and processing a single OpenAPI schema.
    Displays help/instructions when run with --help.
    """
    parser = argparse.ArgumentParser(
        description="Sphinx OpenAPI CLI: Download, process, and combine an OpenAPI schema."
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL of the OpenAPI spec to download.",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        required=True,
        help="Destination path for the downloaded OpenAPI spec.",
    )
    parser.add_argument(
        "--use-xbe-workarounds",
        action="store_true",
        help="Enable XBE workarounds to inject a logo into the schema.",
    )
    parser.add_argument(
        "--combined-schema-file",
        type=Path,
        required=False,
        help="Path for the combined schema output file.",
    )
    args = parser.parse_args()

    schema_info = SchemaInfo(args.url, args.dest)
    config = SimpleNamespace(
        openapi_spec_list=[schema_info],
        openapi_use_xbe_workarounds=args.use_xbe_workarounds,
        openapi_stop_build_on_error=False,
        openapi_combined_schema_file_path=args.combined_schema_file,
    )
    dummy_app = DummyApp(config)
    openapi_ext = SphinxOpenApi(dummy_app)  # type: ignore
    openapi_ext.setup_openapi(dummy_app)      # type: ignore

if __name__ == "__main__":
    main()
