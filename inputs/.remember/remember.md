# Handoff

## State
Tasks 1–7 complètes sur 16, branche `feature/dashboard-tui` dans `/Users/Antoine/Developer/dashboard/`.
13 tests automatisés passent. Daemon opérationnel (génère les PNG EUR/USD, EUR/GBP, EUR/JPY).
Repo git initialisé au niveau parent (`/Users/Antoine/Developer/dashboard/`) — l'ancien `.git` d'`inputs/` a été supprimé.

## Next
1. Reprendre via `superpowers:subagent-driven-development` à la **Task 8** (com.user.dashboard.plist).
2. Tasks restantes : 8 (plist Launchd), 9 (squelette TUI), 10 (CurrencyWidget), 11 (ContextMenu), 12 (ConfigScreen), 13 (modal édition), 14 (bin/dashboard), 15 (bouton +), 16 (vérification finale).

## Context
- Le plan est dans `inputs/docs/superpowers/plans/2026-04-14-dashboard-tui.md`.
- Code applicatif dans `/Users/Antoine/Developer/dashboard/` (pas dans `inputs/`).
- `requirements.txt` = runtime seul ; `requirements-dev.txt` = runtime + pytest.
- Worktree non utilisé (repo frais) — travailler directement sur `feature/dashboard-tui`.
