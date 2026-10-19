// FX Math test: engine.js vs oracle.py's expected.json.
const fs = require("fs");
eval(fs.readFileSync("engine.js", "utf8"));
const cases = JSON.parse(fs.readFileSync("expected.json", "utf8"));
const fns = { spreadTruth, costTruth, roundTruth };
let fail = 0;
for (const c of cases) {
  let got;
  try { got = fns[c.fn](...c.args); } catch (e) { got = "ERR:" + e.message; }
  if (got !== c.expected) {
    fail++;
    console.log(`FAIL ${c.fn} ${JSON.stringify(c.args)}\n  expected: ${c.expected}\n  got:      ${got}`);
  }
}
console.log(`${cases.length} cases / ${cases.length - fail} checks, ${fail} failed`);
process.exit(fail ? 1 : 0);
