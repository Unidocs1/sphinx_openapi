# sphinx_openapi/sphinx_openapi.py
"""
Standard imports and module docstring.
"""
import os
import requests
import yaml
from pathlib import Path
from requests.exceptions import Timeout
from sphinx.application import Sphinx
from models.schema_info import SchemaInfo

class SphinxOpenApi:
    """
    Sphinx extension to download OpenAPI YAML schemas, apply workarounds,
    and combine multiple schemas into one file.
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
        and combines them into a single YAML file.
        """
        self.log(f"Starting setup. Spec URLs: {[s.url for s in self.schema_info_list]}")

        if not self._dest_paths_unique():
            msg = "Duplicate destination file names detected."
            self.log(msg)
            if self.openapi_stop_build_on_error:
                raise RuntimeError(msg)

        for schema_info in self.schema_info_list:
            self._download_schema(schema_info)

        if self.combined_schema_file_path:
            self._combine_schemas()

        self.log("Finished setup.")

    def _dest_paths_unique(self) -> bool:
        """
        Checks that all destination file names in schema_info_list are unique.
        """
        dest_names = [schema.dest.name for schema in self.schema_info_list]
        return len(dest_names) == len(set(dest_names))

    def _download_schema(self, schema_info: SchemaInfo, timeout: int = 5) -> None:
        """
        Downloads a YAML schema from the provided URL to its destination path.
        """
        try:
            response = requests.get(schema_info.url, timeout=timeout)
            response.raise_for_status()
            schema_info.dest.parent.mkdir(parents=True, exist_ok=True)
            with open(schema_info.dest, "wb") as f:
                f.write(response.content)
            self.log(f"Downloaded {schema_info.url} to {schema_info.dest}")
            if self.openapi_use_xbe_workarounds:
                self._apply_xbe_workarounds(schema_info)
        except Timeout:
            self.log(f"Timeout occurred while downloading: {schema_info.url}")
            if self.openapi_stop_build_on_error:
                raise
        except requests.exceptions.HTTPError as http_err:
            self.log(f"HTTP error for {schema_info.url}: {http_err}")
            if self.openapi_stop_build_on_error:
                raise
        except Exception as e:
            self.log(f"Error downloading {schema_info.url}: {e}")
            if self.openapi_stop_build_on_error:
                raise

    def _apply_xbe_workarounds(self, schema_info: SchemaInfo) -> None:
        """
        Applies XBE workarounds by injecting a logo into the schema.
        """
        try:
            with open(schema_info.dest, "r", encoding="utf-8") as f:
                schema = yaml.safe_load(f)
            if isinstance(schema, dict) and "info" in schema:
                schema["info"]["x-logo"] = "../../../_static/images/xbe_static_docs/logo.png"
            with open(schema_info.dest, "w", encoding="utf-8") as f:
                yaml.safe_dump(schema, f)
            self.log(f"Applied XBE workarounds to {schema_info.dest}")
        except Exception as e:
            self.log(f"Failed to apply XBE workarounds to {schema_info.dest}: {e}")
            if self.openapi_stop_build_on_error:
                raise

    def _combine_schemas(self) -> None:
        """
        Combines all downloaded YAML schemas into one file.
        """
        combined_schemas = []
        for schema_info in self.schema_info_list:
            try:
                with open(schema_info.dest, "r", encoding="utf-8") as f:
                    schema = yaml.safe_load(f)
                combined_schemas.append(schema)
            except Exception as e:
                self.log(f"Error reading {schema_info.dest} for combination: {e}")
                if self.openapi_stop_build_on_error:
                    raise
        try:
            self.combined_schema_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.combined_schema_file_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(combined_schemas, f)
            self.log(f"Combined schemas written to {self.combined_schema_file_path}")
        except Exception as e:
            self.log(f"Error writing combined schema file: {e}")
            if self.openapi_stop_build_on_error:
                raise

    def log(self, message: str) -> None:
        """
        Logs a message with a standard prefix.
        """
        print(f"[sphinx_openapi] {message}")
