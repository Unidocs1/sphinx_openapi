# Sphinx Extension: OpenAPI

<!-- Badges go here on the same line; PyPi doesn't support `\` or single-multi-line (it'll stack vertically) -->
[![PyPI](https://img.shields.io/pypi/v/sphinx-openapi)](https://pypi.org/project/sphinx-openapi/) [![PyPI - License](https://img.shields.io/pypi/l/sphinx-openapi)](https://opensource.org/licenses/MIT)

## Description

This Sphinx extension allows for downloading updated OpenAPI json + yaml specs for use with the
[sphinxcontrib.redoc](https://pypi.org/project/sphinxcontrib-redoc/) extension.

## Setup

Add the following to your `conf.py` (includes `redoc` extension setup):

```python
from pathlib import Path

html_context = {}  # This is usually already defined for other themes/extensions
extensions = [
    'sphinx_openapi',
    'sphinxcontrib.redoc',
]

# -- sphinx_openapi extension (OpenAPI Local Download/Updater) ------------

# Downloads json|yaml files to here
openapi_dir_path = Path(confdir / "_static/specs").absolute().as_posix()
openapi_generated_file_posix_path = Path(confdir / "content/-/api/index").as_posix()
openapi_combined_schema_file_path = Path(confdir / "_static/specs/openapi-combined.yaml")
openapi_stop_build_on_error = False

# Ensure that each SchemaInfo has a unique destination file name.
openapi_spec_list = [
    SchemaInfo(
        source="https://raw.githubusercontent.com/Redocly/openapi-starter/refs/heads/main/openapi/openapi.yaml",
        dest=Path("_static/specs/openapi-redocly.yaml")
    ),
    SchemaInfo(
        source="https://raw.githubusercontent.com/swagger-api/swagger-petstore/refs/heads/master/src/main/resources/openapi.yaml",
        dest=Path("_static/specs/openapi-petstore.yaml")
    )
]
```

## Requirements

- Python>=3.10
- Sphinx>=7  # Tested with 8

This may work with older versions, but has not been tested.

## Entry Point

See `setup(app)` definition at `sphinx_openapi.py`.

## Tested in

- Windows 11 via PowerShell 7
- Ubuntu 22.04 via ReadTheDocs (RTD) CI
- Python 3.10~3.12
- Sphinx 7~8

## Notes

- **@ XBE Docs devs:** In conf.py, consider these extra options, showing defaults below:

    ```py
    openapi_debug_stop_on_done = False  # Use this to test live edits to the plugin
    openapi_use_xbe_workarounds = False  # Injects info.x-logo into schema
    ```
