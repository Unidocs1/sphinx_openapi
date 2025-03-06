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


def unique_schema_info(urls: list[str], dest_dir: Path) -> list[SchemaInfo]:
    """
    Given a list of URLs and a destination directory, returns a list of SchemaInfo
    with unique destination file names. If duplicate file names occur, appends '-1', '-2', etc.
    """
    dest_names: dict[str, int] = {}
    schema_info_list = []
    for url in urls:
        original_filename = Path(url.split("/")[-1]).name
        base = Path(original_filename).stem
        ext = Path(original_filename).suffix
        candidate = f"{base}{ext}"
        if candidate in dest_names:
            dest_names[candidate] += 1
            candidate = f"{base}-{dest_names[candidate]}{ext}"
        else:
            dest_names[candidate] = 0
        schema_info_list.append(SchemaInfo(url, dest_dir / candidate))
    return schema_info_list


def main() -> None:
    """
    CLI entry point for downloading and processing multiple OpenAPI schemas.
    Each URL is downloaded to the destination directory using a unique file name.
    Displays help/instructions when run with --help.
    """
    parser = argparse.ArgumentParser(
        description="Sphinx OpenAPI CLI: Download, process, and optionally combine OpenAPI schemas."
    )
    parser.add_argument(
        "--urls",
        nargs="+",
        type=str,
        required=True,
        help="List of OpenAPI spec URLs to download. Do not include surrounding brackets.",
    )
    parser.add_argument(
        "--dest-dir",
        type=Path,
        required=False,
        default=Path.cwd(),
        help="Destination directory where the downloaded schemas will be saved.",
    )
    parser.add_argument(
        "--use-xbe-workarounds",
        action="store_true",
        help="Enable XBE workarounds to inject a logo into the schema.",
    )
    parser.add_argument(
        "--combined-schema-file",
        nargs="?",
        type=Path,
        const=Path("./combined_openapi.yaml"),
        default=None,
        help=(
            "Optional flag for combining schemas. If provided without a value, "
            "defaults to './combined_openapi.yaml'. If omitted, no combined file is produced."
        ),
    )
    args = parser.parse_args()

    if args.dest_dir.exists():
        if not args.dest_dir.is_dir():
            parser.error(f"--dest-dir must be a directory, got file: {args.dest_dir}")
    else:
        args.dest_dir.mkdir(parents=True, exist_ok=True)

    # Process URLs to ensure unique destination filenames.
    schema_info_list = unique_schema_info(args.urls, args.dest_dir)
    config = SimpleNamespace(
        openapi_spec_list=schema_info_list,
        openapi_use_xbe_workarounds=args.use_xbe_workarounds,
        openapi_stop_build_on_error=False,
        openapi_combined_schema_file_path=args.combined_schema_file,
    )
    dummy_app = DummyApp(config)
    openapi_ext = SphinxOpenApi(dummy_app)  # type: ignore
    openapi_ext.setup_openapi(dummy_app)      # type: ignore


if __name__ == "__main__":
    main()
