#!/usr/bin/env python3
# FX Math oracle - mirrors engine.js with fractions.Fraction; money rounds half up to cents at each step.
import json, re
from fractions import Fraction
from math import floor

AMT_ERR = "amount must be a number above 0 and up to 999999999999 with at most 2 decimals"
RATE_ERR = "rate must be a number above 0 and up to 999999 with at most 6 decimals"
FEE_ERR = "flat fee must be a number from 0 with at most 2 decimals"
PCT_ERR = "percent fee must be from 0 to 20 with at most 2 decimals"
CUR_ERR = "currency codes must be three letters"
SAME_ERR = "the two currencies must differ"

def s_(t): return t.strip() if isinstance(t, str) else ""

def amt(t):
    t = s_(t)
    if not re.fullmatch(r"[0-9]{1,12}(\.[0-9]{1,2})?", t) or Fraction(t) == 0: raise ValueError(AMT_ERR)
    return Fraction(t)

def rate(t):
    t = s_(t)
    if not re.fullmatch(r"[0-9]{1,6}(\.[0-9]{1,6})?", t) or Fraction(t) == 0: raise ValueError(RATE_ERR)
    return Fraction(t)

def fee(t):
    t = s_(t)
    if not re.fullmatch(r"[0-9]{1,12}(\.[0-9]{1,2})?", t): raise ValueError(FEE_ERR)
    return Fraction(t)

def pctin(t):
    t = s_(t)
    if not re.fullmatch(r"[0-9]{1,2}(\.[0-9]{1,2})?", t) or Fraction(t) > 20: raise ValueError(PCT_ERR)
    return Fraction(t)

def cur(a, b):
    x, y = s_(a), s_(b)
    if not re.fullmatch(r"[A-Za-z]{3}", x) or not re.fullmatch(r"[A-Za-z]{3}", y): raise ValueError(CUR_ERR)
    x, y = x.upper(), y.upper()
    if x == y: raise ValueError(SAME_ERR)
    return x, y

def rnd(v, k):
    sc = floor(abs(v) * 10**k + Fraction(1, 2))
    return Fraction(-sc if v < 0 else sc, 10**k)

def fx(v, k):
    r = rnd(v, k)
    sc = int(abs(r) * 10**k)
    s = str(sc).rjust(k + 1, "0")
    out = s[:-k] + "." + s[-k:] if k else s
    return ("-" if r < 0 else "") + out

def rt(v):
    s = fx(v, 6)
    return s.rstrip("0").rstrip(".")

def money(v): return rnd(v, 2)
def share(a, b): return fx(a / b * 100, 2) + "%"

def spread_truth(f, t, reference, offered, amount):
    c = cur(f, t); ref = rate(reference); off = rate(offered); a = amt(amount)
    head = f"Against a reference rate of {rt(ref)} {c[1]} per {c[0]}, an offered rate of {rt(off)}"
    if off == ref:
        return head + f" is the same, so on {fx(a, 2)} {c[0]} nothing is lost or gained."
    below = off < ref
    d = abs(ref - off)
    gap = money(a * d)
    infrom = money(gap / ref)
    return (head + f" is {share(d, ref)} {'below' if below else 'above'} it. On {fx(a, 2)} {c[0]} that is {fx(gap, 2)} {c[1]}"
            f"{' fewer' if below else ' more'}, worth {fx(infrom, 2)} {c[0]} at the reference rate.")

def cost_truth(f, t, amount, r, flat, pct, reference):
    c = cur(f, t); a = amt(amount); r = rate(r); fl = fee(flat); p = pctin(pct); ref = rate(reference)
    pf = money(a * p / 100)
    net = a - fl - pf
    if net <= 0: raise ValueError("the fees are as large as the amount or larger")
    got = money(net * r); fair = money(a * ref)
    eff = got / a
    s = (f"Sending {fx(a, 2)} {c[0]} with a flat fee of {fx(fl, 2)} {c[0]} and a {fx(p, 2)}% fee ({fx(pf, 2)} {c[0]}) leaves {fx(net, 2)} {c[0]} "
         f"to convert at {rt(r)}, which gives {fx(got, 2)} {c[1]}, an effective {fx(eff, 6)} {c[1]} per {c[0]}. "
         f"At the reference rate of {rt(ref)} you would get {fx(fair, 2)} {c[1]}")
    if got == fair: return s + ", the same amount."
    dd = abs(fair - got)
    return s + f", which is {fx(dd, 2)} {c[1]} ({share(dd, fair)}) {'fewer' if got < fair else 'more'}."

def round_truth(f, t, amount, out, back):
    c = cur(f, t); a = amt(amount); ro = rate(out); rb = rate(back)
    mid = money(a * ro); ret = money(mid * rb)
    s = (f"Converting {fx(a, 2)} {c[0]} at {rt(ro)} gives {fx(mid, 2)} {c[1]}; converting that back at {rt(rb)} gives {fx(ret, 2)} {c[0]}")
    if ret == a: return s + ", exactly what you started with."
    dd = abs(a - ret)
    return s + f", which is {fx(dd, 2)} {c[0]} ({share(dd, a)}) {'fewer' if ret < a else 'more'} than you started with."

FNS = {"spreadTruth": spread_truth, "costTruth": cost_truth, "roundTruth": round_truth}
E, U = "EUR", "USD"
CASES = [
    ("spreadTruth", [E, U, "1.08", "1.05", "1000"]), ("spreadTruth", [E, U, "1.08", "1.08", "1000"]), ("spreadTruth", [E, U, "1.08", "1.10", "1000"]), ("spreadTruth", ["eur", " usd ", "1.0800", "1.0500", "1000.00"]),
    ("spreadTruth", ["USD", "JPY", "150.25", "148.9", "250.50"]), ("spreadTruth", ["JPY", "USD", "0.0067", "0.0065", "100000"]), ("spreadTruth", [E, U, "1.08", "1.079999", "0.01"]), ("spreadTruth", [E, U, "999999", "0.000001", "999999999999"]),
    ("spreadTruth", [E, U, "1", "0.5", "10"]), ("spreadTruth", [E, U, "1", "2", "10"]), ("spreadTruth", [E, U, "3", "2.99", "333.33"]), ("spreadTruth", ["GBP", "EUR", "1.1654", "1.1301", "2500"]),
    ("spreadTruth", [E, U, "1.08", "1.05", "0.01"]), ("spreadTruth", [E, U, "0", "1.05", "1000"]), ("spreadTruth", [E, U, "1.08", "0", "1000"]), ("spreadTruth", [E, U, "1.08", "1.05", "0"]),
    ("spreadTruth", [E, U, "1.08", "1.05", "-5"]), ("spreadTruth", [E, U, "1.0000001", "1.05", "5"]), ("spreadTruth", [E, E, "1.08", "1.05", "5"]), ("spreadTruth", ["EU", U, "1.08", "1.05", "5"]),
    ("spreadTruth", [E, "US1", "1.08", "1.05", "5"]), ("spreadTruth", [E, U, "x", "1.05", "5"]), ("spreadTruth", [E, U, "1.08", "1.05", "x"]), ("spreadTruth", ["", "", "1", "1", "1"]),
    ("costTruth", [E, U, "1000", "1.05", "5", "1", "1.08"]), ("costTruth", [E, U, "1000", "1.08", "0", "0", "1.08"]), ("costTruth", [E, U, "1000", "1.10", "0", "0", "1.08"]), ("costTruth", [E, U, "1000", "1.08", "0", "1", "1.08"]),
    ("costTruth", [E, U, "200", "1.0725", "3.99", "0.5", "1.0801"]), ("costTruth", [E, U, "50", "1.05", "4.5", "2.5", "1.08"]), ("costTruth", [E, U, "0.05", "1.05", "0.01", "0", "1.08"]), ("costTruth", [E, U, "1000", "1.05", "0", "20", "1.08"]),
    ("costTruth", [E, U, "1000", "1.05", "0", "20.01", "1.08"]), ("costTruth", [E, U, "10", "1.05", "10", "0", "1.08"]), ("costTruth", [E, U, "10", "1.05", "9.99", "0", "1.08"]), ("costTruth", [E, U, "10", "1.05", "20", "0", "1.08"]),
    ("costTruth", ["USD", "JPY", "12345.67", "148.375", "7.25", "1.25", "149.1"]), ("costTruth", ["JPY", "USD", "500000", "0.006612", "1500", "0.75", "0.00667"]), ("costTruth", [E, U, "1000", "1.05", "-1", "1", "1.08"]), ("costTruth", [E, U, "1000", "1.05", "x", "1", "1.08"]),
    ("costTruth", [E, U, "1000", "1.05", "5", "x", "1.08"]), ("costTruth", [E, U, "1000", "0", "5", "1", "1.08"]), ("costTruth", [E, U, "1000", "1.05", "5", "1", "0"]), ("costTruth", [E, U, "0", "1.05", "5", "1", "1.08"]),
    ("costTruth", [E, E, "1000", "1.05", "5", "1", "1.08"]), ("costTruth", ["EURO", U, "1000", "1.05", "5", "1", "1.08"]), ("costTruth", [E, U, "1000", "1.05", "5.123", "1", "1.08"]), ("costTruth", [E, U, "1000", "1.05", "5", "1.005", "1.08"]),
    ("roundTruth", [E, U, "1000", "1.05", "0.93"]), ("roundTruth", [E, U, "1000", "1.05", "0.952380952"]), ("roundTruth", [E, U, "1000", "1", "1"]), ("roundTruth", [E, U, "1000", "1.05", "0.96"]),
    ("roundTruth", [E, U, "100", "1.08", "0.9259"]), ("roundTruth", [E, U, "0.01", "1.05", "0.93"]), ("roundTruth", ["USD", "JPY", "5000", "149.5", "0.00665"]), ("roundTruth", [E, U, "999999999999", "999999", "0.000001"]),
    ("roundTruth", [E, U, "250.75", "1.0712", "0.9301"]), ("roundTruth", [E, U, "333.33", "3", "0.3333"]), ("roundTruth", [E, U, "10", "0.5", "2"]), ("roundTruth", [E, U, "10", "0.5", "2.01"]),
    ("roundTruth", [E, U, "0", "1.05", "0.93"]), ("roundTruth", [E, U, "10", "0", "0.93"]), ("roundTruth", [E, U, "10", "1.05", "0"]), ("roundTruth", [E, U, "10", "1.05", "x"]),
    ("roundTruth", [E, E, "10", "1.05", "0.93"]), ("roundTruth", [E, "", "10", "1.05", "0.93"]), ("roundTruth", [E, U, "10.999", "1.05", "0.93"]), ("roundTruth", [E, U, "10", "1.0000001", "0.93"]),
]
out = []
for fn, args in CASES:
    try:
        exp = FNS[fn](*args)
    except ValueError as e:
        exp = "ERR:" + str(e)
    out.append({"fn": fn, "args": args, "expected": exp})
with open("expected.json", "w") as f:
    json.dump(out, f, indent=1)
    f.write("\n")
print(len(out), "cases")
