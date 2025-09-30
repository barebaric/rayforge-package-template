#!/usr/bin/env python3
"""
Validates a Rayforge package for correctness.

This script checks the 'rayforge-package.yaml' metadata file for schema
correctness, content consistency, and the existence of declared assets.

It can be run locally (e.g., as a pre-commit hook) or in a CI/CD
pipeline.
"""

import argparse
import ast
import importlib.util
import re
import sys
from pathlib import Path

import semver
import yaml

METADATA_FILENAME = "rayforge-package.yaml"

# Schema defines required keys and their expected types.
SCHEMA = {
    "name": {"type": str, "required": True},
    "description": {"type": str, "required": True},
    "author": {"type": dict, "required": True},
    "provides": {"type": dict, "required": True},
}

AUTHOR_SCHEMA = {
    "name": {"type": str, "required": True},
    "email": {"type": str, "required": True},
}


def _check_non_empty_str(value, key_name):
    """Raises ValueError if a string is None, empty, or just whitespace."""
    if not value or not value.strip():
        raise ValueError(f"Key '{key_name}' must not be empty.")


def _validate_dict_schema(data, schema, parent_key=""):
    """Recursively validates a dictionary against a defined schema."""
    for key, rules in schema.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if rules.get("required") and key not in data:
            raise ValueError(f"Missing required key: '{full_key}'")

        if key in data:
            expected_type = rules["type"]
            actual_value = data[key]
            if not isinstance(actual_value, expected_type):
                raise TypeError(
                    f"Key '{full_key}' has wrong type. "
                    f"Expected {expected_type.__name__}, but "
                    f"got {type(actual_value).__name__}."
                )


def validate_schema(data):
    """Checks for required keys and correct types in the metadata."""
    print("-> Running schema validation...")
    _validate_dict_schema(data, SCHEMA)
    _validate_dict_schema(data.get("author", {}), AUTHOR_SCHEMA, "author")
    print("   ... Schema OK")


def _check_tag(tag):
    """Validates that a tag is a valid semantic version."""
    if not tag:
        return
    try:
        semver.VersionInfo.parse(tag.lstrip("v"))
        print(f"   ... Version tag '{tag}' OK")
    except ValueError:
        raise ValueError(
            f"Version tag '{tag}' is not a valid semantic version "
            "(e.g., v1.2.3)."
        )


def _check_package_name(metadata_name, expected_name):
    """Validates package name in metadata against the expected one."""
    if not expected_name:
        return
    if metadata_name != expected_name:
        raise ValueError(
            f"Package name mismatch. Expected '{expected_name}', but "
            f"metadata has '{metadata_name}'."
        )
    print(f"   ... Package name '{expected_name}' OK")


def _check_author_content(author_data):
    """Checks for placeholders and valid content in the author field."""
    name = author_data.get("name", "")
    email = author_data.get("email", "")

    _check_non_empty_str(name, "author.name")
    _check_non_empty_str(email, "author.email")

    if "your-github-username" in name:
        raise ValueError(
            "Placeholder 'author.name' detected. Please update it."
        )

    # Basic email regex to catch common mistakes.
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, email):
        raise ValueError(f"Author email '{email}' has an invalid format.")


def _check_asset_path(path_str, root_path):
    """Validates an asset path for existence and security."""
    if not path_str or not isinstance(path_str, str):
        raise ValueError("Asset entry is missing a valid 'path' key.")

    if ".." in Path(path_str).parts:
        raise ValueError(
            f"Invalid asset path: '{path_str}'. Paths must not use '..'."
        )

    asset_path = root_path / path_str
    if not asset_path.exists():
        raise FileNotFoundError(f"Asset path '{path_str}' does not exist.")


def _check_code_entry_point(entry_point, root_path):
    """
    Validates a Python entry point without executing code.

    Checks that the module exists and the specified attribute is defined
    within it using static analysis (AST).
    """
    if ":" not in entry_point:
        raise ValueError(
            f"Code entry point '{entry_point}' is invalid. "
            "Expected format 'path.to.module:function_name'."
        )

    module_name, attr_name = entry_point.split(":", 1)

    # Temporarily add package root to path to allow finding the module
    sys.path.insert(0, str(root_path))
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None or spec.origin is None:
            raise FileNotFoundError(f"Module '{module_name}' not found.")

        module_path = Path(spec.origin)
        source = module_path.read_text()
        tree = ast.parse(source, filename=module_path.name)

        for node in tree.body:
            # Check for 'def attr_name(...)' or 'class attr_name(...)'
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if node.name == attr_name:
                    print(f"   ... Code entry point '{entry_point}' OK")
                    return
            # Check for 'attr_name = ...'
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == attr_name:
                        print(f"   ... Code entry point '{entry_point}' OK")
                        return

        raise NameError(
            f"Attribute '{attr_name}' not found in module '{module_name}'."
        )
    finally:
        sys.path.pop(0)


def _check_provides(provides_data, root_path):
    """Validates the content of the 'provides' section."""
    if not provides_data or not (
        "code" in provides_data or "assets" in provides_data
    ):
        raise ValueError(
            "The 'provides' section must contain 'code' and/or 'assets'."
        )

    if "assets" in provides_data:
        assets = provides_data["assets"]
        if not isinstance(assets, list):
            raise TypeError("'provides.assets' must be a list.")
        for asset_info in assets:
            if not isinstance(asset_info, dict):
                raise TypeError("Each entry in 'assets' must be a dictionary.")
            _check_asset_path(asset_info.get("path"), root_path)

    if "code" in provides_data:
        _check_code_entry_point(provides_data["code"], root_path)


def validate_content(data, root_path, tag=None, name=None):
    """Performs sanity checks on the metadata content."""
    print("-> Running content validation...")
    _check_tag(tag)
    _check_package_name(data.get("name"), name)

    _check_non_empty_str(data.get("name"), "name")
    _check_non_empty_str(data.get("description"), "description")

    _check_author_content(data.get("author", {}))
    _check_provides(data.get("provides", {}), root_path)
    print("   ... Content OK")


def _load_metadata(metadata_file):
    """Loads and parses the YAML metadata file."""
    if not metadata_file.is_file():
        print(
            f"\nERROR: Metadata file not found at '{metadata_file}'",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(metadata_file, "r") as f:
        return yaml.safe_load(f)


def main():
    """Main execution function. Parses arguments and runs validations."""
    parser = argparse.ArgumentParser(
        description="Validate a Rayforge package."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to package root directory (defaults to current dir).",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="The Git tag to validate (used by CI, optional locally).",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="The expected package name (used by CI, optional locally).",
    )
    args = parser.parse_args()

    root_path = Path(args.path).resolve()
    metadata_file = root_path / METADATA_FILENAME
    print(f"Validating package at: {root_path}")

    try:
        metadata = _load_metadata(metadata_file)
        if not isinstance(metadata, dict):
            raise TypeError(
                f"'{METADATA_FILENAME}' must be a YAML dictionary."
            )

        validate_schema(metadata)
        validate_content(metadata, root_path, tag=args.tag, name=args.name)

        print("\nSUCCESS: Your package metadata looks great!")
        return 0

    except (ValueError, TypeError, FileNotFoundError, NameError) as e:
        print(f"\nERROR: Validation failed. {e}", file=sys.stderr)
        return 1
    except yaml.YAMLError as e:
        print(
            f"\nERROR: Could not parse '{METADATA_FILENAME}'. {e}",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred. {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
