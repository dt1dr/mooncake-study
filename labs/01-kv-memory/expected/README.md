# Expected evidence

`calculator.json` contains two official model presets, eight input cases and their
independently captured `totalBytes`. Tolerance: zero bytes; GB = bytes / 10^9,
GiB = bytes / 2^30. Model dimensions come from `data/kv_cache_calculator/models.yaml`;
the reference implementation is `assets/js/kv-cache-calculator.js` in
[kvcache-blog at 7d449d1fe1a5419af90c554f222e025dcc3756ba](https://github.com/kvcache-ai/kvcache-blog/tree/7d449d1fe1a5419af90c554f222e025dcc3756ba).

The outputs were captured by executing that JavaScript with Node. The settings are
`formula: standard_gqa`, `tensorParallel: 1`, `tokens` and `sequences` from each case,
and `precision: bf16_fp16` (2 bytes) or `fp8_int8` (1 byte). Optional caches use the
upstream defaults. The MHA counterfactual overrides `num_key_value_heads` to 64.

To independently recheck the reference, download the pinned JS to a temporary file,
then run from the repository root (Node is only needed for reference maintenance):

```sh
curl -fL https://raw.githubusercontent.com/kvcache-ai/kvcache-blog/7d449d1fe1a5419af90c554f222e025dcc3756ba/assets/js/kv-cache-calculator.js -o /tmp/kv-calculator.js
node <<'JS'
const { calculate } = require('/tmp/kv-calculator.js');
const ref = require('./labs/01-kv-memory/expected/calculator.json');
for (const c of ref.cases) {
  const model = {formula: 'standard_gqa', fields: {...ref.models[c.model], ...c.overrides}};
  const input = {tokens: c.tokens, sequences: c.batch_size, tensorParallel: 1,
    precision: c.bytes_per_element === 2 ? 'bf16_fp16' : 'fp8_int8'};
  require('node:assert/strict').equal(calculate(model, input).totalBytes, c.total_bytes);
}
JS
```
