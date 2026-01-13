# Gemini AI Integration

This document outlines the steps and considerations for integrating Gemini AI into the `option-pricing` project.

## Environment
- **CRITICAL:** Always run shell commands using the `webapp` conda environment.
- Use `conda run -n webapp <command>` or ensure the environment is active.

## Project Upgrade to Python 3.12+
To leverage the latest features and performance improvements, we will upgrade the project to Python 3.12+.

## Coding Style and Best Practices
- We use Python 3.12+. Use strict type hinting.
- Do not use `print()` for debugging; use the `logging` module.
- All date-times must be UTC.
- Rename file and variables to follow best practices.
- **CRITICAL:** comment every time 

## Testing
- Write unit tests using Vitest for every new utility function (JS) - *Legacy/Optional*.
- Run Python unit tests: `pytest opricer/tests`
- Run End-to-End browser tests: `PYTHONPATH=. pytest webapp/tests/test_e2e.py` (Requires `playwright install`)

## Agent Instructions
- **Change Transparency:** Every time you make changes in files, clearly state which part of the file you are changing.
- **Directory Structure:** `webapp` contains the Dash app (formerly `Utils`). `opricer` is the core package.
- **Git Policy:** NEVER merge changes to the `main` branch unless explicitly instructed by the user.