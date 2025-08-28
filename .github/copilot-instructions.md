---
applyTo: "**/*.py"
---
# Code standard

## Code structure

Simple and clear

## Python environment

Using `uv`

Path: `${workspaceFolder}/.venv/bin/python`

## Error log

Always use `traceback.print_exc()` instead of a custom message to easily identify the source of the error.

Don't print custom log.

## Documentation

Refer to the official documentation for detailed information on the API and usage examples.

- https://modelcontextprotocol.io/quickstart/server
- https://github.com/modelcontextprotocol/quickstart-resources
- https://docs.paramiko.org/en/stable/
