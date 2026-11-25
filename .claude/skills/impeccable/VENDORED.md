# Vendored: Impeccable (design skill for coding agents)

- Source: https://github.com/pbakaus/impeccable, Claude Code variant (`.claude/skills/impeccable`)
- Commit: b49177d32788f2dc585c42831d845dacf1ebed2c (2026-11-18), skill version 4.10.0
- Licence: Apache-2.0 (LICENSE and NOTICE.md alongside)
- Not vendored: its design-detector hook (it would change project settings). Not installed through `npx skills add`.
- Hygiene: the launcher downloads its engine binary on first run into `$IMPECCABLE_HOME/bin/<version>/`
  (default `~/.impeccable`). `scripts/env.sh` / `env.ps1` set `IMPECCABLE_HOME` to `.cache/impeccable` so it stays
  inside this repo. Always source them before using the skill.
