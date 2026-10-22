# AGENTS.md

## Shipping

Tier: **push**. This repo uses trunk-based development: no pull requests.

1. Work in an isolated worktree or session for the task.
2. Prove it: there is no verify command yet (none passed on a clean checkout), so run the repo's checks by hand; for user-visible changes also run the app end to end and say what you ran.
3. Land: `git fetch`, rebase onto `origin/main`, re-run verify if new commits came in, then `git push origin HEAD:main` with a 10-minute command timeout. The push runs the shipgate review (bugbot) and can take several minutes. If it is blocked, fix the `[high]` findings, commit, and push again.
4. Never use `--no-verify`, change `core.hooksPath`, set `BUGBOT_OVERRIDE`, or force-push main.
5. Ask-first paths (`.shipgate.toml` itself, plus any `ask_first` entries in it) need Ben's approval before landing; stop and tell Ben.
6. Record what landed and the proof with `ledger note`.

Cloud agents: push a branch named `land/<task>` instead of pushing main (the lander arrives later; until then tell Ben the branch name).
