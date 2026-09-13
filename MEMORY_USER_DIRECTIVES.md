# NiakVIO — User execution directives

Authoritative durable directive from the user, 2026-09-13:

- Manual tests already supplied by the user are authoritative input evidence for the active repair pass.
- Do **not** redo or reclassify the same provider tests from zero unless one narrowly targeted verification is strictly necessary to avoid a false fix.
- When the user says `continue`, resume immediately from the real current HEAD of the active repair branch and execute the remaining ZERO/regression fixes through validation and delivery.
- Do not stall on inventory, recounting, or repeated diagnosis when the user's existing manual evidence already identifies the failing lane or chain.
- Prefer concrete correction -> targeted proof -> full non-regression -> persistence, then move to the next open ZERO/regression.
- Never treat historical quarantine/repair labels alone as current regressions; current evidence wins.
- Do not touch `main` during the active `fix/labs-5.21.44-20260912` repair pass unless a later explicit publication step authorizes it.

This file is part of the durable recovery context and should be read together with `MEMORY.md` in future NiakVIO conversations.
