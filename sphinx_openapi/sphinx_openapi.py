"""
Xsolla Sphinx Extension: sphinx_openapi
- See README for more info
"""

import orjson  # Way more efficient than `json` lib for handling giant files
import os
import requests
from pathlib import Path
from enum import Enum
from requests.exceptions import Timeout
from sphinx.application import Sphinx


class OpenApiFileType(Enum):
    JSON = "json"
    YAML = "yaml"


class SphinxOpenApi:
    def __init__(self, app: Sphinx):
        self.app = app
        self.openapi_use_xbe_workarounds = app.config.openapi_use_xbe_workarounds
        self.openapi_spec_url_noext = app.config.openapi_spec_url_noext
        self.openapi_dir_path = Path(app.config.openapi_dir_path)
        self.openapi_generated_file_posix_path = Path(app.config.openapi_generated_file_posix_path).as_posix()

        # This is the file type we'll use for openapi docgen | json or yaml
        self.openapi_file_type = OpenApiFileType[app.config.openapi_file_type.upper()]
        self.openapi_file_path_no_ext = Path(self.openapi_dir_path / "openapi").resolve().as_posix()
        self.openapi_file_path = Path(self.openapi_file_path_no_ext + self.openapi_file_type.value)  # .json or .yaml

    def download_schema_files(self):
        try:
            # Construct properly formatted URLs
            json_src_url = self.openapi_spec_url_noext + ".json"
            yaml_dest_file = Path(self.openapi_file_path_no_ext + ".json")
            self.download_file(json_src_url, yaml_dest_file)
        except Exception as e:
            print(f'[sphinx_openapi.py] Failed to download "{self.openapi_spec_url_noext}.json": {e}')
            return

        try:
            yaml_url_src = self.openapi_spec_url_noext + ".yaml"
            yaml_dest_file = Path(self.openapi_file_path_no_ext + ".yaml")
            self.download_file(yaml_url_src, yaml_dest_file)
        except Exception as e:
            print(f'[sphinx_openapi.py] Failed to download "{self.openapi_spec_url_noext}.yaml": {e}')
            return

    def setup_openapi(self, app):
        print("")
        print("[sphinx_openapi.py] Attempting to download schema files...")

        if not os.path.exists(self.openapi_dir_path):
            os.makedirs(self.openapi_dir_path)

        try:
            self.download_schema_files()

            if self.openapi_file_type == OpenApiFileType.JSON:
                self.preprocess_json_schema_file()
            else:
                print(
                    f"[sphinx_openapi] openapi_file_type ({self.openapi_file_type}) "
                    f"!= 'json'; skipping preprocessing..."
                )

            print(
                f"[sphinx_openapi.py] Done:\n"
                f"- Generated from: {self.openapi_file_path}'\n"
                f"- Built to: 'build/html/{self.openapi_generated_file_posix_path}.html'\n"
            )
        except Exception as e:
            # Crash or continue?
            if self.app.config.openapi_stop_build_on_error:
                raise RuntimeError(f"[sphinx_openapi.py] Critical Error: {e}")
            else:
                print(f"[sphinx_openapi.py] Non-critical error occurred: {e}")

    @staticmethod
    def download_file(url, save_to_path, timeout=5):
        try:
            # Attempt to get the response with the specified timeout
            response = requests.get(url, timeout=timeout)

            # Check if the response was successful; if not, raise an HTTPError
            response.raise_for_status()

            # If successful, write the content to the file
            with open(save_to_path, "wb") as f:
                f.write(response.content)
            print(f"- Successfully downloaded {url} to: '{save_to_path}'")

        except Timeout:
            print(f"- Timeout occurred while downloading: {url}")
        except requests.exceptions.HTTPError as http_err:
            # Capture HTTP errors and print the status code and response content
            print(f"- HTTP error occurred while downloading: {url}: {http_err}")
            print(f"- HTTP response content: {http_err.response.text}")
        except requests.exceptions.SSLError as ssl_err:
            # Capture SSL errors and print the specific SSL error
            print(f"- SSL error occurred while downloading {url}: {ssl_err}")
        except requests.exceptions.RequestException as req_err:
            # Capture any other request-related exceptions and print the error
            print(f"- Failed to download {url}: {req_err}")
        except Exception as e:
            # Capture any unexpected exceptions
            print(f"- An unexpected error occurred while downloading {url}: {e}")

    @staticmethod
    def set_xbe_workarounds(schema):
        """
        TODO: Fix these and remove this workaround, caller, and openapi_use_xbe_workarounds flag:
        TODO: Confirm if we still need these
        - 1. Bug workarounds - Replace these refs with null:
          - a. Invalid reference token: models.Address
          - b. Invalid reference token: models.Defaults
          - c. Invalid reference token: models.DownloadInfo
        - 2. Injections:
          - a. Add logo: `../../../_static/images/xbe_static_docs/logo.png`
        """
        # (1) Bug fixes, if schemas exist -> Set None
        if "components" in schema and "schemas" in schema["components"]:
            # Handle models.Contact -> properties -> address
            if "models.Contact" in schema["components"]["schemas"]:
                contact_properties = schema["components"]["schemas"]["models.Contact"].get("properties", {})
                if "address" in contact_properties and "$ref" in contact_properties["address"]:
                    contact_properties["address"]["$ref"] = None

            # Handle models.Resource -> properties -> defaults
            if "models.Resource" in schema["components"]["schemas"]:
                resource_properties = schema["components"]["schemas"]["models.Resource"].get("properties", {})
                if "defaults" in resource_properties and "$ref" in resource_properties["defaults"]:
                    resource_properties["defaults"]["$ref"] = None
    
            # (2) Injections, if image and schema exist -> set x-logo
            if "info" in schema:
                schema["info"]["x-logo"] = "../../../_static/images/xbe_static_docs/logo.png"

    # TODO: Add support for yaml
    def preprocess_json_schema_file(self):
        """Reads json file, implement bug workarounds, adds logo"""
        print(
            "[sphinx_openapi.py] Preprocessing openapi.json (bug workarounds, inject logo)..."
        )

        try:
            schema_file_name = (self.openapi_file_path_no_ext + f".{self.openapi_file_type.value}")
            schema_file_path = Path(self.openapi_dir_path, schema_file_name)

            with open(schema_file_path, "rb") as f:  # Reading in binary mode for orjson
                schema = orjson.loads(f.read())

            if self.openapi_use_xbe_workarounds:
                self.set_xbe_workarounds(schema)

            # Save the schema back to the file, keeping it minimized
            with open(schema_file_path, "wb") as f:  # Writing in binary mode for orjson
                f.write(orjson.dumps(schema))

        except Exception as e:
            raise Exception(f"[sphinx_openapi.py] Failed to preprocess_json_schema_file: {e}")
