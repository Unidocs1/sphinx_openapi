# sphinx_openapi/__init__.py
from .sphinx_openapi import SphinxOpenApi
from sphinx.application import Sphinx
import importlib.metadata

# Dynamically fetch the version from pyproject.toml
try:
    __version__ = importlib.metadata.version("sphinx_openapi")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"


# ENTRY POINT >>
def setup(app: Sphinx):
    app.add_config_value("openapi_use_xbe_workarounds", False, "env")  # Default is False
    app.add_config_value("openapi_spec_url_noext", "", "env")  # Default is an empty string
    app.add_config_value("openapi_dir_path", "_specs", "env")  # Default is "_specs"
    app.add_config_value("openapi_generated_file_posix_path", "", "env")  # Default is an empty string
    app.add_config_value("openapi_file_type", "json", "env")  # Default is "json"
    app.add_config_value("openapi_stop_build_on_error", False, "env")  # Default is False

    openapi_downloader = SphinxOpenApi(app)
    app.connect("builder-inited", openapi_downloader.setup_openapi)

    print(f"[sphinx_openapi::setup] Extension loaded with version: {__version__}")

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
