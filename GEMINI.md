# Gemini AI Integration

This document outlines the steps and considerations for integrating Gemini AI into the `option-pricing` project.

## Environment
- **CRITICAL:** Always run shell commands using the `webapp` conda environment.
- Use `conda run -n webapp <command>` or ensure the environment is active.

## Project Upgrade to Python 3.12+

To leverage the latest features and performance improvements, we will upgrade the project to Python 3.12+. This section details the necessary steps for this transition.

## Coding Style and Best Practices
- We use Python 3.12+. Use strict type hinting.
- Do not use `print()` for debugging; use the `logging` module.
- All date-times must be UTC.
- Rename file and variables to follow best practices.
- **CRITICAL:** comment every time 

## Testing
- Write unit tests using Vitest for every new utility function.