// FX Math engine: currency exchange spread and fee arithmetic on exact BigInt fractions. Money rounds half up to cents.
var AMT_ERR = "amount must be a number above 0 and up to 999999999999 with at most 2 decimals";
var RATE_ERR = "rate must be a number above 0 and up to 999999 with at most 6 decimals";
var FEE_ERR = "flat fee must be a number from 0 with at most 2 decimals";
var PCT_ERR = "percent fee must be from 0 to 20 with at most 2 decimals";
var CUR_ERR = "currency codes must be three letters";
var SAME_ERR = "the two currencies must differ";

function _dec(text, re, err) {
  var t = typeof text === "string" ? text.trim() : "";
  if (!re.test(t)) throw new Error(err);
  var parts = t.split("."), frac = parts.length > 1 ? parts[1] : "";
  return { n: BigInt(parts[0] + frac), d: 10n ** BigInt(frac.length) };
}
function _mul(a, b) { return { n: a.n * b.n, d: a.d * b.d }; }
function _div(a, b) { return { n: a.n * b.d, d: a.d * b.n }; }
function _sub(a, b) { return { n: a.n * b.d - b.n * a.d, d: a.d * b.d }; }
function _cmp(a, b) { var x = a.n * b.d, y = b.n * a.d; return x < y ? -1 : x > y ? 1 : 0; }
function _isZero(a) { return a.n === 0n; }
function _round(v, k) {
  var neg = v.n < 0n, n = neg ? -v.n : v.n, p = 10n ** BigInt(k);
  var s = (2n * n * p + v.d) / (2n * v.d);
  return { n: neg ? -s : s, d: p };
}
function _fmt(v, k) {
  var r = _round(v, k), neg = r.n < 0n, s = (neg ? -r.n : r.n).toString();
  while (s.length < k + 1) s = "0" + s;
  var out = k ? s.slice(0, s.length - k) + "." + s.slice(s.length - k) : s;
  return (neg && r.n !== 0n ? "-" : "") + out;
}
function _amt(t) { var v = _dec(t, /^[0-9]{1,12}(\.[0-9]{1,2})?$/, AMT_ERR); if (v.n === 0n) throw new Error(AMT_ERR); return v; }
function _rate(t) { var v = _dec(t, /^[0-9]{1,6}(\.[0-9]{1,6})?$/, RATE_ERR); if (v.n === 0n) throw new Error(RATE_ERR); return v; }
function _fee(t) { return _dec(t, /^[0-9]{1,12}(\.[0-9]{1,2})?$/, FEE_ERR); }
function _pct(t) {
  var v = _dec(t, /^[0-9]{1,2}(\.[0-9]{1,2})?$/, PCT_ERR);
  if (_cmp(v, { n: 20n, d: 1n }) > 0) throw new Error(PCT_ERR);
  return v;
}
function _cur(a, b) {
  var x = typeof a === "string" ? a.trim() : "", y = typeof b === "string" ? b.trim() : "";
  if (!/^[A-Za-z]{3}$/.test(x) || !/^[A-Za-z]{3}$/.test(y)) throw new Error(CUR_ERR);
  x = x.toUpperCase(); y = y.toUpperCase();
  if (x === y) throw new Error(SAME_ERR);
  return [x, y];
}
function _money(v) { return _round(v, 2); }
function _rt(v) { return _fmt(v, 6).replace(/0+$/, "").replace(/\.$/, ""); }
function _share(a, b) { return _fmt(_mul(_div(a, b), { n: 100n, d: 1n }), 2) + "%"; }

// The spread truth: how far an offered rate sits from a reference rate, on a sum.
function spreadTruth(from, to, reference, offered, amount) {
  var c = _cur(from, to), ref = _rate(reference), off = _rate(offered), a = _amt(amount);
  var cmp = _cmp(off, ref);
  var head = "Against a reference rate of " + _rt(ref) + " " + c[1] + " per " + c[0] + ", an offered rate of " + _rt(off);
  if (cmp === 0) return head + " is the same, so on " + _fmt(a, 2) + " " + c[0] + " nothing is lost or gained.";
  var diff = _sub(ref, off), below = cmp < 0;
  var gap = _money(_mul(a, below ? diff : _sub(off, ref)));
  var inFrom = _money(_div(gap, ref));
  var pct = _share(below ? diff : _sub(off, ref), ref);
  return head + " is " + pct + (below ? " below" : " above") + " it. On " + _fmt(a, 2) + " " + c[0] + " that is " + _fmt(gap, 2) + " " + c[1] +
    (below ? " fewer" : " more") + ", worth " + _fmt(inFrom, 2) + " " + c[0] + " at the reference rate.";
}

// The cost truth: fees and rate together, against what the reference rate would give.
function costTruth(from, to, amount, rate, flat, pct, reference) {
  var c = _cur(from, to), a = _amt(amount), r = _rate(rate), f = _fee(flat), p = _pct(pct), ref = _rate(reference);
  var pctFee = _money(_div(_mul(a, p), { n: 100n, d: 1n }));
  var net = _sub(_sub(a, f), pctFee);
  if (net.n <= 0n) throw new Error("the fees are as large as the amount or larger");
  var got = _money(_mul(net, r)), fair = _money(_mul(a, ref));
  var eff = _div(got, a);
  var cmp = _cmp(got, fair);
  var s = "Sending " + _fmt(a, 2) + " " + c[0] + " with a flat fee of " + _fmt(f, 2) + " " + c[0] + " and a " + _fmt(p, 2) + "% fee (" + _fmt(pctFee, 2) +
    " " + c[0] + ") leaves " + _fmt(net, 2) + " " + c[0] + " to convert at " + _rt(r) + ", which gives " + _fmt(got, 2) + " " + c[1] +
    ", an effective " + _fmt(eff, 6) + " " + c[1] + " per " + c[0] + ". At the reference rate of " + _rt(ref) + " you would get " + _fmt(fair, 2) + " " + c[1];
  if (cmp === 0) return s + ", the same amount.";
  var d = _sub(fair, got);
  var below = cmp < 0;
  var dd = below ? d : { n: -d.n, d: d.d };
  return s + ", which is " + _fmt(dd, 2) + " " + c[1] + " (" + _share(dd, fair) + ") " + (below ? "fewer" : "more") + ".";
}

// The round trip truth: convert out and straight back at the two rates given.
function roundTruth(from, to, amount, out, back) {
  var c = _cur(from, to), a = _amt(amount), ro = _rate(out), rb = _rate(back);
  var mid = _money(_mul(a, ro)), ret = _money(_mul(mid, rb));
  var s = "Converting " + _fmt(a, 2) + " " + c[0] + " at " + _rt(ro) + " gives " + _fmt(mid, 2) + " " + c[1] + "; converting that back at " + _rt(rb) +
    " gives " + _fmt(ret, 2) + " " + c[0];
  var cmp = _cmp(ret, a);
  if (cmp === 0) return s + ", exactly what you started with.";
  var d = _sub(a, ret);
  var dd = cmp < 0 ? d : { n: -d.n, d: d.d };
  return s + ", which is " + _fmt(dd, 2) + " " + c[0] + " (" + _share(dd, a) + ") " + (cmp < 0 ? "fewer" : "more") + " than you started with.";
}
