# Reading nano-mooncake before attempting lab07

[nano-mooncake](https://github.com/BokaiGuo/nano-mooncake) is a separate teaching runtime.
This repository provides paper-to-evidence exercises and does not reproduce its runtime.
No dependency or implementation from that project is vendored. Before a hands-on
exercise, select and record its commit, then answer these questions with exact file paths:

1. Who owns the KV blocks and how long do they remain readable after a process exits?
2. What identifies a reusable prefix, and where is a partial-prefix gap rejected?
3. Which scheduler inputs are measured and which are modeled?
4. Which bytes cross a process boundary? How is hidden prefill recomputation detected?
5. What does NC1 preserve, and which cache advantage must disappear?
6. Which results demonstrate a mechanism, a trend or a comparable numerical result?

For the optional lab07, pin nano-vllm as a submodule only when implementation begins,
keep changes as patches, and compare deterministic output token by token. One GPU does
not establish the performance benefits of independent prefill/decode resource pools.
