# sphinx_openapi/sphinx_openapi.py
from pathlib import Path

import requests
import yaml
from requests.exceptions import Timeout
from sphinx.application import Sphinx

from models.schema_info import SchemaInfo


class SphinxOpenApi:
    """
    Sphinx extension to download OpenAPI YAML schemas, apply workarounds,
    and combine multiple schemas into one unified spec.
    """

    def __init__(self, app: Sphinx) -> None:
        self.app: Sphinx = app
        self.schema_info_list: list[SchemaInfo] = app.config.openapi_spec_list
        self.openapi_use_xbe_workarounds: bool = app.config.openapi_use_xbe_workarounds
        self.openapi_stop_build_on_error: bool = app.config.openapi_stop_build_on_error
        self.combined_schema_file_path: Path = app.config.openapi_combined_schema_file_path

    def setup_openapi(self, app: Sphinx) -> None:
        """
        Downloads each OpenAPI schema, applies workarounds if enabled,
        and combines them into a single unified YAML file.
        """
        self.log("Starting setup. Spec URLs:")
        for schema in self.schema_info_list:
            self.log(f"- {schema.url}")

        for schema in self.schema_info_list:
            self.download_file(schema.url, schema.dest)
            if self.openapi_use_xbe_workarounds:
                self._apply_xbe_workarounds(schema)

        if self.combined_schema_file_path:
            self._combine_schemas()

        self.log("Finished setup.")

    @staticmethod
    def download_file(url: str, save_to_path: Path, timeout: int = 5) -> None:
        """
        Downloads a file from the given URL to the provided path.
        Overwrites any existing file.
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            save_to_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_to_path, "wb") as f:
                f.write(response.content)
            print(f"[sphinx_openapi] Successfully downloaded '{url}' to: '{save_to_path}'")
        except Timeout:
            print(f"[sphinx_openapi] Timeout occurred while downloading: '{url}'")
        except requests.exceptions.HTTPError as http_err:
            print(f"[sphinx_openapi] HTTP error for '{url}': {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"[sphinx_openapi] Error downloading '{url}': {req_err}")
        except Exception as e:
            print(f"[sphinx_openapi] Unexpected error downloading '{url}': {e}")

    def _apply_xbe_workarounds(self, schema: SchemaInfo) -> None:
        """
        Applies XBE workarounds by injecting a logo into the schema.
        """
        try:
            with open(schema.dest, "r", encoding="utf-8") as f:
                spec = yaml.safe_load(f)
            if isinstance(spec, dict) and "info" in spec:
                spec["info"]["x-logo"] = "../../../_static/images/xbe_static_docs/logo.png"
            with open(schema.dest, "w", encoding="utf-8") as f:
                yaml.safe_dump(spec, f)
            self.log(f"Applied XBE workarounds to '{schema.dest}'")
        except Exception as e:
            self.log(f"Failed to apply XBE workarounds to '{schema.dest}': {e}")
            if self.openapi_stop_build_on_error:
                raise

    def _combine_schemas(self) -> None:
        """
        Combines all downloaded OpenAPI YAML schemas into one unified spec.
        Merges the 'paths' and 'components' sections.
        """
        specs = []
        for schema in self.schema_info_list:
            try:
                with open(schema.dest, "r", encoding="utf-8") as f:
                    spec = yaml.safe_load(f)
                    specs.append(spec)
            except Exception as e:
                self.log(f"Error reading '{schema.dest}' for combination: {e}")
                if self.openapi_stop_build_on_error:
                    raise
        try:
            merged_spec = self.merge_openapi_specs(specs)
            self.combined_schema_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.combined_schema_file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(merged_spec, f)
            self.log(f"Combined schemas written to '{self.combined_schema_file_path}'")
        except Exception as e:
            self.log(f"Error writing combined schema file: {e}")
            if self.openapi_stop_build_on_error:
                raise

    @staticmethod
    def merge_openapi_specs(specs: list[dict]) -> dict:
        """
        Merges a list of OpenAPI specification dictionaries into one unified spec.
        This basic merging algorithm:
          - Uses the 'openapi' version and 'info' from the first spec.
          - Merges all 'paths', allowing duplicate paths by appending a numeric suffix (-1, -2, etc.).
          - Merges 'components' by shallow-merging each component category.
        """
        if not specs:
            raise ValueError("[sphinx_openapi] No specifications provided for merging.")

        merged_spec = {
            "openapi": specs[0].get("openapi", "3.0.0"),
            "info": specs[0].get("info", {}),
            "paths": {},
        }
        merged_components = {}

        for spec in specs:
            for path, path_item in spec.get("paths", {}).items():
                unique_path = path
                counter = 1
                while unique_path in merged_spec["paths"]:
                    unique_path = f"{path}-{counter}"
                    counter += 1
                merged_spec["paths"][unique_path] = path_item

            components = spec.get("components", {})
            for comp_key, comp_val in components.items():
                if comp_key not in merged_components:
                    merged_components[comp_key] = comp_val
                else:
                    for item_key, item_val in comp_val.items():
                        if item_key in merged_components[comp_key]:
                            counter = 1
                            unique_item_key = f"{item_key}-{counter}"
                            while unique_item_key in merged_components[comp_key]:
                                counter += 1
                                unique_item_key = f"{item_key}-{counter}"
                            merged_components[comp_key][unique_item_key] = item_val
                        else:
                            merged_components[comp_key][item_key] = item_val

        if merged_components:
            merged_spec["components"] = merged_components

        return merged_spec

    @staticmethod
    def log(message: str) -> None:
        """
        Logs a message with a standard prefix.
        """
        print(f"[sphinx_openapi] {message}")
