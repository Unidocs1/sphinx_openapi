# sphinx_openapi/sphinx_openapi.py
from pathlib import Path

import requests
import yaml
from requests.exceptions import Timeout
from sphinx.application import Sphinx

from sphinx_openapi.models.schema_info import SchemaInfo


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
        self.openapi_debug_stop_on_done: bool = app.config.openapi_debug_stop_on_done
        self.combined_schema_file_path: Path = (
            app.config.openapi_combined_schema_file_path
        )

    def setup_openapi(self, app: Sphinx) -> None:
        """
        Downloads each OpenAPI schema, applies workarounds if enabled,
        and combines them into a single unified YAML file.
        """
        if not self.schema_info_list:
            self.log("No OpenAPI specs configured, skipping setup")
            return

        print("")
        self.log("--------------------------------")
        self.log("Starting setup. Spec sources:")
        for schema in self.schema_info_list:
            self.log(f"- {schema.source}")

        for schema in self.schema_info_list:
            self.download_file(schema.source, schema.dest)
            if self.openapi_use_xbe_workarounds:
                self._apply_xbe_workarounds(schema)

        if self.combined_schema_file_path:
            self._combine_schemas()

        print("")
        self.log("Finished setup.")
        
        if self.openapi_debug_stop_on_done:
            self.log("Debug mode: Stopping build after OpenAPI setup", is_error=True)
            import sys
            sys.exit(0)

    @staticmethod
    def download_file(source: str | Path, save_to_path: Path, timeout: int = 5) -> None:
        """
        Downloads a file from the given URL or copies from local path to the provided path.
        Overwrites any existing file.
        """
        try:
            source_str = str(source)
            if source_str.startswith(('http://', 'https://')):
                response = requests.get(source_str, timeout=timeout)
                response.raise_for_status()
                content = response.content
            else:
                # Handle local file
                with open(source_str, 'rb') as f:
                    content = f.read()
            
            save_to_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_to_path, "wb") as f:
                f.write(content)
            print("")
            print(
                f"[sphinx_openapi] Successfully {'downloaded' if source_str.startswith(('http://', 'https://')) else 'copied'} '{source_str}' to: '{save_to_path}'"
            )
        except Timeout:
            print(f"[sphinx_openapi] Timeout occurred while downloading: '{source_str}'")
        except requests.exceptions.HTTPError as http_err:
            print(f"[sphinx_openapi] HTTP error for '{source_str}': {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"[sphinx_openapi] Error downloading '{source_str}': {req_err}")
        except FileNotFoundError:
            print(f"[sphinx_openapi] File not found: '{source_str}'")
        except Exception as e:
            print(f"[sphinx_openapi] Unexpected error processing '{source_str}': {e}")

    def _apply_xbe_workarounds(self, schema: SchemaInfo) -> None:
        """
        Applies XBE workarounds by injecting a logo into the schema.
        """
        try:
            with open(schema.dest, "r", encoding="utf-8") as f:
                spec = yaml.safe_load(f)
            if isinstance(spec, dict) and "info" in spec:
                spec["info"][
                    "x-logo"
                ] = "../../../_static/images/xbe_static_docs/logo.png"
            with open(schema.dest, "w", encoding="utf-8") as f:
                yaml.safe_dump(spec, f)
            self.log(f"Applied XBE workarounds to '{schema.dest}'")
        except FileNotFoundError:
            self.log(f"Schema file not found: '{schema.dest}'", is_error=True)
        except yaml.YAMLError as e:
            self.log(f"Invalid YAML in '{schema.dest}': {str(e)}", is_error=True)
        except Exception as e:
            self.log(f"Failed to apply XBE workarounds to '{schema.dest}': {str(e)}", is_error=True)

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
            except FileNotFoundError:
                self.log(f"Schema file not found: '{schema.dest}'", is_error=True)
                continue
            except yaml.YAMLError as e:
                self.log(f"Invalid YAML in '{schema.dest}': {str(e)}", is_error=True)
                continue
            except Exception as e:
                self.log(f"Error reading '{schema.dest}': {str(e)}", is_error=True)
                continue

        if not specs:
            self.log("No valid schemas to combine", is_error=True)
            return

        try:
            merged_spec = self.merge_openapi_specs(specs)
            self.combined_schema_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.combined_schema_file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(merged_spec, f)
            print("")
            self.log(f"Combined schemas written to '{self.combined_schema_file_path}'")
        except Exception as e:
            self.log(f"Error writing combined schema file: {str(e)}", is_error=True)

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
    def log(message: str, is_error: bool = False) -> None:
        """
        Logs a message with a standard prefix.
        If is_error is True, the message will be shown in red with line breaks.
        """
        if is_error:
            print(f"\n[sphinx_openapi] \033[91m{message}\033[0m\n")
        else:
            print(f"[sphinx_openapi] {message}")
