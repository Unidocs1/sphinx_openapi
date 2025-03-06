# sphinx_openapi/__init__.py
from sphinx.application import Sphinx
from .sphinx_openapi import SphinxOpenApi
import importlib.metadata
from pathlib import Path

try:
    __version__ = importlib.metadata.version("sphinx_openapi")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

def setup(app: Sphinx) -> dict:
    """
    Sets up the sphinx_openapi extension.
    """
    app.add_config_value("openapi_spec_list", [], "env")
    app.add_config_value("openapi_use_xbe_workarounds", False, "env")
    app.add_config_value("openapi_stop_build_on_error", False, "env")
    app.add_config_value("openapi_combined_schema_file_path", None, "env")

    openapi_ext = SphinxOpenApi(app)
    app.connect("builder-inited", openapi_ext.setup_openapi)
    print(f"[sphinx_openapi] Extension loaded with version: {__version__}")
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
