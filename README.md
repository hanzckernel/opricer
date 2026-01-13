# Option Pricing Tool

This package includes American, European, and Barrier option pricing models using Finite Difference (PDE) and Monte Carlo methods.
It features a modern web interface powered by **Dash** and **Dash Bootstrap Components**.

## Features
- **Core Library (`opricer`)**:
    - **Models**: Standardized option models (European, American, Barrier, Basket).
    - **Algorithms**: 
        - Analytic Solver (Black-Scholes).
        - PDE Solvers (Finite Difference).
        - Monte Carlo Solvers (Euler-Maruyama, Longstaff-Schwartz for American options).
- **Web App (`webapp`)**:
    - Interactive Dashboard with Stock Market visualization and Option Pricing tools.
    - Responsive, mobile-friendly UI using Bootstrap.
    - Real-time data fetching (Yahoo Finance, NewsAPI).

## Installation

### Prerequisites
- Python 3.12+
- `conda` (recommended)

### Setup
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install .
    # OR
    pip install -r requirements.txt
    ```

## Usage

### Library
```python
from opricer.model import models
from opricer.algo import analytics
from datetime import datetime, timezone

expiry = datetime(2025, 1, 1, tzinfo=timezone.utc)
underlying = models.Underlying(datetime.now(timezone.utc), 100.0)
option = models.EurOption(expiry, 'call')
option._attach_asset(100.0, underlying)

solver = analytics.AnalyticSolver()
price = solver(option)
print(price)
```

### Web App
To run the web application:
```bash
python index.py
```
Navigate to `http://127.0.0.1:8050/`.

## Testing
Run unit tests with `pytest`:
```bash
pytest
```

## License
MIT License
