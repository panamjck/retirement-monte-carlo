# Monte Carlo Retirement Simulator – Delayed Retirement Analysis

This project runs a Monte Carlo simulation of retirement outcomes across **different retirement ages**, using **consistent market paths** so you can see the *true* impact of delaying retirement rather than random noise.

It explicitly models:

- Working years where **salary covers expenses** and savings flow into cash, taxable, and 401(k)
- Retirement years where **portfolio + pension + Social Security + side income** cover expenses
- Tax-aware withdrawals across accounts

⚠️ **Not financial advice.** This is a quantitative sandbox, not a planning tool.

---
<repo-root>/success_rate_by_retirement_age.png

## Key Features

This version of the simulator:

1. **Models working years explicitly**

   - Salary after 401(k) is taxed.
   - After-tax salary first covers living expenses.
   - Any leftover after-tax savings are split between:
     - cash (no growth)
     - taxable investments (SPY/QQQ mix)
   - Additional 401(k) contributions are added pre-tax.

2. **Uses one market path per simulation across all retirement ages**

   For each simulation:
   - A single market sequence is generated (via block bootstrap using SPY + NASDAQ history).
   - The *same* sequence is used for every retirement age (e.g., 55–65).
   - This isolates the effect of retirement age from randomness in return paths.

3. **Models multiple income sources**

   - Pension that increases with years of service.
   - Social Security starting at a configured age.
   - Optional post-retirement earned income (consulting/part-time) that stops at a configured age.
   - All income is inflation-adjusted.

4. **Implements tax-aware withdrawals**

   When portfolio withdrawals are needed:
   - Cash is used first (no tax).
   - Taxable investments next (capital gains tax).
   - 401(k) last (income tax).
   - If all accounts deplete, the simulation records the depletion age.

5. **Compares retirement ages and marginal benefit**

   For each retirement age in a range (e.g., 55–65) the code reports:
   - Success rate (did the portfolio last to the target age?)
   - Median and 10th percentile ending portfolio value at the target age
   - Average assets at retirement (and cash/pension levels)
   - Failure counts and median depletion age
   - Marginal benefit of each extra working year (delta in success rate and ending portfolio)

---

## Data & Assumptions

- Historical returns:
  - Hard-coded SPY and NASDAQ annual returns from 1979–2024.
  - Combined using `SPY_ALLOCATION` and `QQQ_ALLOCATION`.
- Market paths:
  - Generated via **block bootstrap** with a block size of 7 years and limited block reuse.
- Inflation:
  - Drawn from a normal distribution with `MEAN_INFLATION` and `INFLATION_STD`, clipped at a floor of -5%.
- Simulation horizon:
  - From `CURRENT_AGE` through `TARGET_AGE`.
  - Retirement ages tested from `MIN_RETIREMENT_AGE` to `MAX_RETIREMENT_AGE`.

All key parameters (age, balances, salary, allocations, tax rates, etc.) are at the top of the script for easy editing.

---

## Outputs

When you run the script, it:

1. Prints a working-years summary (salary, taxes, savings split).
2. Runs `NUM_SIMULATIONS` Monte Carlo runs.
3. For each retirement age, prints:
   - Assets at retirement (average)
   - Cash and pension at retirement (average)
   - Success rate
   - Median and 10th percentile ending portfolio values
4. Prints a failure table (failures, failure rate, median depletion age).
5. Prints a marginal-benefit table comparing adjacent retirement ages.

It also saves CSVs:

- `improved_retirement_analysis.csv` – one row per retirement age with summary metrics  
- `improved_marginal_benefits.csv` – marginal impact of each additional working year  

> **Note:** Update the output paths at the bottom of the script to something suitable for your system (or use relative paths).

---

## Requirements

- Python 3.x
- Packages:
  - `numpy`
  - `pandas`
  - `matplotlib` (currently imported; can be removed if not plotting)

Install with:

```bash
pip install numpy pandas matplotlib
