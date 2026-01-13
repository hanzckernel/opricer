# Development Plan

## Stage 1: Modernization & Structure
- [x] **Project Structure Cleanup**
    - [x] Rename `Utils` to `webapp` to better reflect its purpose.
    - [x] Standardize `pyproject.toml` as the primary configuration file.
    - [x] Remove legacy `setup.py` if redundant.
- [x] **Module Initialization**
    - [x] Ensure `opricer/__init__.py` exposes a clean and explicit API.
    - [x] Move any script-like execution out of library files.

## Stage 2: Code Quality & Refactoring (Core `opricer`)
- [x] **Models (`opricer/model`)**
    - [x] Refactor `models.py` to use Python 3.12+ features (dataclasses, strict type hinting).
    - [x] Ensure proper UTC datetime handling.
- [x] **Algorithms (`opricer/algo`)**
    - [x] Refactor `mc.py` (Monte Carlo) for naming consistency (`logMCSolver` -> `LogMCSolver`) and performance.
    - [x] Refactor `pde.py` and `analytics.py`.
- [ ] **Tools (`opricer/tools`)**
    - [ ] Review and improve `mathtool.py`.

## Stage 3: Testing
- [x] **Setup**
    - [x] Configure `pytest`.
- [x] **Unit Tests**
    - [x] Write comprehensive tests for `models`.
    - [x] Write tests for `algo` solvers (MC, PDE, Analytic).
    - [x] Ensure high test coverage.

## Stage 4: Web App Integration
- [x] **Web App (`webapp`)**
    - [x] Update imports in `webapp` (formerly `Utils`) to match the new structure.
    - [x] Verify `dash` application functionality (via code inspection).

## Stage 5: Web UI Modernization (New)
- [x] **UI Setup & Assets**
    - [x] Install `dash-bootstrap-components`.
    - [x] Consolidate assets: Move `webapp/src/assets` content to `webapp/assets`.
    - [x] Update `app.py` to remove custom HTML injection and use standard `assets` folder.
    - [x] Configure `app.py` to use a Bootstrap theme (e.g., FLATLY or MATERIA).
- [x] **Layout Structure (Bootstrap)**
    - [x] Refactor `index.py` to use `dbc.Container` and `dbc.Navbar` (or `dcc.Tabs` styled with Bootstrap).
- [x] **Stock Tab (`stock.py`)**
    - [x] Replace custom HTML/CSS classes with `dbc.Row`, `dbc.Col`, `dbc.Card`.
    - [x] Replace inputs and dropdowns with `dbc` components.
    - [x] Ensure responsive stacking for mobile.
- [x] **Options Tab (`options.py`)**
    - [x] Refactor grid layout using `dbc.Row`/`dbc.Col`.
    - [x] Modernize the "New Option" modal using `dbc.Modal`.
    - [x] Improve "Correlation Heatmap" and "World Data" layout for small screens.
- [x] **Cleanup**
    - [x] Remove `webapp/src` directory (Materialize CSS/JS).
    - [x] Remove unused CSS files from `webapp/assets`.

## Stage 7: End-to-End Testing (New)
- [x] **Setup**
    - [x] Install `pytest-playwright` and browser binaries.
    - [x] Configure `pytest` for E2E.
- [x] **Basic Navigation**
    - [x] Test app title and navbar links.
- [x] **Feature Tests**
    - [x] Test Stock ticker input and graph loading.
    - [x] Test Option asset creation modal and pricing computation.