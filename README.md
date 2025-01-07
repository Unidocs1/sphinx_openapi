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

# -- OpenAPI Shared: Used in multiple extensions --------------------------

# Downloads json|yaml files to here
openapi_dir_path = Path("_static/specs").absolute().as_posix()

# openapi_stop_build_on_error = manifest_is_production_stage  # Only stop if production, else just show errs
openapi_stop_build_on_error = True  # TEST - DELETE ME

# Link here from rst with explicit ".html" ext (!) but NOT from a doctree
openapi_generated_file_posix_path = Path("content/-/api/index").as_posix()  # Parses to forward/slashes/

# -- Extension: sphinx_openapi (OpenAPI Local Download/Updater) -----------
# Used in combination with the sphinxcontrib.redoc extension
# Use OpenAPI ext to download/update → redoc ext to generate

openapi_use_xbe_workarounds = True  # We have some floating workarounds; TODO: Fix + Remove
openapi_spec_url_noext = "https://api.demo.goxbe.cloud/v1/openapi"  # Swap this with your own
openapi_file_type = "json"  # or yaml; we'll download them both but generate from only 1
openapi_use_xbe_workaround = True  # We have some floating workarounds within the extension; TODO: Fix + remove

# -- Extension: sphinxcontrib.redoc --------------------------------------
# OpenAPI Docgen: Similar to sphinxcontrib-openapi, but +1 column for example responses
# (!) Prereq: OpenAPI Local Download (above)
# Doc | https://sphinxcontrib-redoc.readthedocs.io/en/stable
# Demo | https://sphinxcontrib-redoc.readthedocs.io/en/stable/api/github/

# (!) Works around a critical bug that default grabs old 1.x ver (that !supports OpenAPI 3+)
redoc_uri = "https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"

# Intentional forward/slashes/ for html; eg: "_static/specs/openapi.json"
xbe_spec = Path(openapi_dir_path, "openapi.json")

redoc = [{
    "name": "Xsolla Backend API",
    "page": openapi_generated_file_posix_path,  # content/-/api/index
    "spec": Path("_static/specs/openapi.json"),
    "embed": True,  # Local file only (!) but embed is less powerful
    "template": Path("_templates/redoc.j2"),
    "opts": {
        "lazy-rendering": True,  # Formerly called `lazy`; almost required for giant docs
        "required-props-first": True,  # Useful, (!) but slower
        "native-scrollbars": False,  # Improves perf on big specs when False
        "expand-responses": [],  # "200", "201",
        "suppress-warnings": False,
        "hide-hostname": False,
        "untrusted-spec": False,
    },
}]

print(f'[conf.py::sphinxcontrib.redoc] Build from redoc[0].spec: {redoc[0]["spec"]}')
print(f'[conf.py::sphinxcontrib.redoc] Displaying at redoc[0].page: {redoc[0]["page"]}')
print("")
```

## Requirements

- Python>=3.6
- Sphinx>=7

This may work with older versions, but has not been tested.

## Entry Point

See `setup(app)` definition at `sphinx_openapi.py`.

## Tested in

- Windows 11 via PowerShell 7
- Ubuntu 22.04 via ReadTheDocs (RTD) CI
- Python 3.10~3.12
- Sphinx 7~8

## Notes

- `__init__.py` is required for both external pathing and to treat the directory as a pkg
- **@ XBE Docs devs:** In conf.py, add `openapi_use_xbe_workarounds = True`, for now, for WIP bug workarounds
