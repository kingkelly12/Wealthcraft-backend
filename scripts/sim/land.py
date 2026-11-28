"""
Is land balanced? Plays thousands of owners through the rules in app/game/land.py
and compares them with the other things money can buy.

    ../.venv/bin/python ../scripts/sim/land.py     (from my_flask_app/)

"Multiple" = (everything the money paid out + what it is worth at the end) / what
it cost, over HORIZON paydays. Nothing is reinvested.
"""
import math
import os
import random
import statistics
import sys
from decimal import Decimal

sys.path.insert(0, os.getcwd())
from app.game import economy, land  # noqa: E402

RUNS = 20000
HORIZON = 4 * land.PAYDAYS       # four game years: about 104 real days at two weeks a day


def grow(price, months):
    value, held = Decimal(price), 0
    for _ in range(months):
        value, held = economy.appreciate({'value': value, 'purchase_price': price, 'months_held': held})
    return value


GROWN = {}


def grown(price, months):
    if (price, months) not in GROWN:
        GROWN[price, months] = float(grow(price, months))
    return GROWN[price, months]


def play(key, policy, rng):
    plot = land.PLOTS[key]
    price = plot['price']
    fate = land.draw_fate(plot, False, rng)
    cash, lease, status = 0.0, None, 'owned'
    row = {'plot_key': key, 'status': status, 'fate': fate}
    for month in range(1, HORIZON + 1):
        cash -= plot['upkeep']
        if lease:
            pay, lease, _ = land.lease_payday(lease, rng)
            cash += float(pay)
            if not lease:
                row['status'] = 'owned'
            continue
        if month != fate['offer_month']:     # skips comebacks: every offer below is accepted
            continue
        offer = land.terms(plot, plot['annual'], month)
        if policy == 'negotiate':
            cash -= plot['annual'] * float(land.NEGOTIATE_FEE)
            if rng.random() >= land.NEGOTIATE_WINS:
                continue
            offer = land.terms(plot, Decimal(plot['annual']) * land.NEGOTIATE_BOOST, month, negotiated=True)
        if policy == 'sell':
            return (cash + offer['sell']) / price
        lease = land.new_lease(offer['annual'])
        row['status'] = 'leased'
    return (cash + grown(price, HORIZON)) / price


def report(name, results):
    results = sorted(results)
    n = len(results)
    print(f"{name:<34}{statistics.mean(results):>7.2f}{statistics.median(results):>8.2f}"
          f"{results[int(n * .95)]:>8.2f}{sum(r < 1 for r in results) / n:>9.0%}")


def business(price, monthly, band, rng):
    income = sum(monthly * rng.uniform(*band) for _ in range(HORIZON))
    return (income + grown(price, HORIZON)) / price


def let_home(price, rent, upkeep, rng):
    income = sum(rent * rng.uniform(0.75, 1.0) * 0.9 - upkeep for _ in range(HORIZON))
    return (income + grown(price, HORIZON) * 0.95) / price


def market(drift, vol, rng):
    value = 1.0
    for _ in range(4 * 52):
        value *= max(1 + drift / 52 + rng.gauss(0, vol / math.sqrt(52)), 0.4)
    return value


if __name__ == '__main__':
    rng = random.Random(7)
    print(f"{HORIZON} paydays, {RUNS} runs each\n")
    print(f"{'':<34}{'mean':>7}{'median':>8}{'top 5%':>8}{'lose $':>9}")
    for key, plot in land.PLOTS.items():
        for policy in ('lease', 'sell', 'negotiate'):
            report(f"{plot['name']} · {policy}", [play(key, policy, rng) for _ in range(RUNS)])
    for policy in ('lease', 'sell'):
        total = sum(p['price'] for p in land.PLOTS.values())
        report(f"All four plots · {policy}",
               [sum(play(k, policy, rng) * p['price'] for k, p in land.PLOTS.items()) / total for _ in range(RUNS)])
    print()
    report('Index fund', [market(0.07, 0.15, rng) for _ in range(RUNS // 4)])
    report('Let studio flat', [let_home(95000, 950, 120, rng) for _ in range(RUNS // 4)])
    report('Gym (medium risk)', [business(85000, 1600, (0.70, 1.30), rng) for _ in range(RUNS // 4)])
    report('Vending machine (medium risk)', [business(2800, 85, (0.70, 1.30), rng) for _ in range(RUNS // 4)])

    print("\nChance of at least one offer if you own all four:",
          f"{1 - math.prod(1 - p['chance'] for p in land.PLOTS.values()):.0%}")
    for key, p in land.PLOTS.items():
        print(f"  {p['name']}: lease a year is {p['annual'] / 50000:.1f}x a $50k salary")
