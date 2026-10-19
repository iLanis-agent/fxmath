# FX Math

Currency exchange spread and fee arithmetic. Convert 1000.00 EUR to USD and straight back at 1.05 and 0.93, and 23.50 EUR is gone.

## What it computes

- **The spread truth** - how far an offered rate sits from a reference rate you enter, in percent and on a sum.
- **The cost truth** - flat and percent fees taken from the amount, the converted amount, the effective rate, and the gap against the reference rate.
- **The round trip truth** - convert out and straight back at two rates, and what is left.

Amounts are above 0 with up to 2 decimals. Rates are above 0 with up to 6 decimals. The percent fee is 0 to 20. Currency codes are three letters and must differ. Money rounds half up to the cent at each step.

## Boundary

Arithmetic only. It does not know any real exchange rate, bank or card policy, hidden fee or tax, and gives no advice on where to convert. The reference rate and every figure are the owner's own entries.

## Files

- `index.html` - landing page.
- `app.html` - the interactive calculator.
- `engine.js` - the arithmetic (BigInt fractions, no floating point).
- `oracle.py` - the Python mirror (fractions.Fraction) that generates `expected.json`.
- `test.js` - compares every engine output against `expected.json` (68 cases).
- `expected.json` - the golden answers.

## Test

```
python3 oracle.py
node test.js
```

Live: https://ilanis-agent.github.io/fxmath/
Repo: https://github.com/iLanis-agent/fxmath
