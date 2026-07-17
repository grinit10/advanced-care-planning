# Workspace Coding Standards

- Whenever Python source code is modified, added, or refactored:
  1. Always run `uv run ruff check .` to verify code linting, formatting, and import organization.
  2. Always run `uv run pyright` to verify strict static type safety and PEP-compliant annotations.
- Resolve all lint errors, style warnings, and type checker issues before concluding any task.
