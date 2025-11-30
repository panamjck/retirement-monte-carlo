import numpy as np
import pandas as pd

# ---- PARAMETERS ----

START_AGE = 55
END_AGE = 95
YEARS = END_AGE - START_AGE

START_CASH = 160_000.0
START_INVEST = 1_000_000.0

TD_FRACTION = 0.60        # 401k / pre-tax
TAXABLE_FRACTION = 0.40   # independent stocks

START_TD = START_INVEST * TD_FRACTION
START_TAXABLE = START_INVEST * TAXABLE_FRACTION

MONTHLY_EXPENSE = 7_500.0       # includes in-law support
MONTHLY_PENSION = 700.0
MONTHLY_SS = 2_450.0            # starts at 65

ANNUAL_EXPENSE = MONTHLY_EXPENSE * 12
ANNUAL_PENSION = MONTHLY_PENSION * 12
ANNUAL_SS = MONTHLY_SS * 12

INFLATION = 0.03

# For a 60/40 style portfolio, something like:
EXPECTED_RETURN = 0.14          # 6.5% nominal
RETURN_VOL = 0.20                # 11% volatility

TD_TAX_RATE = 0.22               # effective tax on 401k withdrawals
TAXABLE_TAX_RATE = 0.12          # effective tax on taxable withdrawals (capital gains approx)

N_PATHS = 10_000
SEED = 42

# ---- EARNED INCOME LOGIC ----
# Define earned income by age here.
# Example: $2,000/month from 55 to 64 (i.e., 24,000/year), then 0 after 65.

ANNUAL_EARNED_BEFORE_65 = 24_000.0  # change this to whatever you want

def get_earned_income(age):
    """
    Returns annual earned income for a given age.

    You can customize this:
      - flat income until 65
      - or bands (e.g., more at 55-60, less at 61-64)
    """
    if 55 <= age < 65:
        return ANNUAL_EARNED_BEFORE_65
    else:
        return 0.0

# ---- CORE SIMULATION ----
def simulate_paths(n_paths=N_PATHS, seed=SEED):
    rng = np.random.default_rng(seed)

    balances = np.zeros((YEARS + 1, n_paths))   # total invest balance each year
    ruin_age = np.full(n_paths, np.nan)         # age when portfolio hits zero

    ages = np.arange(START_AGE, END_AGE + 1)

    for p in range(n_paths):
        cash = START_CASH
        td = START_TD
        taxable = START_TAXABLE

        exp = ANNUAL_EXPENSE
        pension = ANNUAL_PENSION
        ss = 0.0

        balances[0, p] = td + taxable

        ruined = False

        for y in range(1, YEARS + 1):
            age = START_AGE + y - 1

            # inflate expenses and pension/SS from year 2 onward
            if y > 1:
                exp *= (1 + INFLATION)
                pension *= (1 + INFLATION)
                if ss > 0:
                    ss *= (1 + INFLATION)

            # start SS at 65 in current dollars
            if age >= 65 and ss == 0:
                ss = ANNUAL_SS

            # earned income for this age (not inflated here by default)
            earned = get_earned_income(age)

            # total non-portfolio income
            income = pension + ss + earned

            needed_net = max(exp - income, 0.0)

            # draw from cash first (no tax)
            if cash > 0 and needed_net > 0:
                draw = min(cash, needed_net)
                cash -= draw
                needed_net -= draw

            # draw from investments if still needed
            if needed_net > 0:
                total_inv = td + taxable

                if total_inv <= 0:
                    ruined = True
                    if np.isnan(ruin_age[p]):
                        ruin_age[p] = age
                    td = 0.0
                    taxable = 0.0
                else:
                    # proportional split between TD and taxable
                    p_td = td / total_inv if total_inv > 0 else 0.0
                    eff_net_per_gross = (
                        p_td * (1 - TD_TAX_RATE) +
                        (1 - p_td) * (1 - TAXABLE_TAX_RATE)
                    )
                    gross_needed = needed_net / max(eff_net_per_gross, 1e-6)
                    gross_needed = min(gross_needed, total_inv)

                    draw_td = gross_needed * p_td
                    draw_taxable = gross_needed * (1 - p_td)

                    # handle edge cases if one bucket runs out
                    if draw_td > td:
                        excess = draw_td - td
                        draw_td = td
                        draw_taxable = min(draw_taxable + excess, taxable)

                    if draw_taxable > taxable:
                        excess = draw_taxable - taxable
                        draw_taxable = taxable
                        draw_td = min(draw_td + excess, td)

                    td -= draw_td
                    taxable -= draw_taxable

            # apply investment returns
            r = rng.normal(EXPECTED_RETURN, RETURN_VOL)
            r = max(r, -0.95)   # floor to avoid going past zero

            td *= (1 + r)
            taxable *= (1 + r)

            balances[y, p] = td + taxable

        if ruined and np.isnan(ruin_age[p]):
            ruin_age[p] = END_AGE

    return ages, balances, ruin_age

# ---- SUMMARY FUNCTIONS ----
def compute_ruin_probabilities(ruin_age, checkpoints=(60, 65, 70, 75, 80, 85, 90, 95)):
    probs = {}
    for age in checkpoints:
        probs[age] = float(np.mean(ruin_age <= age))
    return probs

def compute_balance_percentiles(ages, balances, percentiles=(5, 50, 95)):
    rows = []
    for i, age in enumerate(ages):
        bal = balances[i, :]
        stats = np.percentile(bal, percentiles)
        row = {"Age": int(age)}
        for p, val in zip(percentiles, stats):
            row[f"P{p}"] = val
        rows.append(row)
    return pd.DataFrame(rows)

def main():
    ages, balances, ruin_age = simulate_paths()

    ruin_probs = compute_ruin_probabilities(ruin_age)
    print("Probability of ruin by age:")
    for age in sorted(ruin_probs.keys()):
        print(f"  {age}: {ruin_probs[age]*100:.1f}%")

    df_percentiles = compute_balance_percentiles(ages, balances)
    print("\nBalance percentiles (sample):")
    print(df_percentiles.head(12))  # first ~12 years

    # To save the full table:
    # df_percentiles.to_csv("retirement_percentiles_with_income.csv", index=False)


if __name__ == "__main__":
    main()
