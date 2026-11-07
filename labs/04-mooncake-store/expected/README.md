# Expected evidence

Writer and reader must have different PIDs and successful setup/close codes. Put
returns zero; the reader compares all 1,048,576 bytes exactly. TCP received bytes on
the writer data port must cover the payload (protocol overhead is allowed).

After the sole segment owner closes and exits, a new reader returns zero bytes.
An unused master endpoint produces a nonzero setup code and a native `master_client.cpp`
error in `results/invalid.log` (it does not include the master address). All owned
processes must be reaped. These expectations follow the pinned API's teardown test;
see the source link in the lab README. The verifier never starts native services.
