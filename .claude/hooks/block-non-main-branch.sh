#!/usr/bin/env bash
# PreToolUse(Bash) guard — this repo is strictly main-only.
#
# Blocks the agent from: creating/switching to a new branch (checkout -b/-B,
# switch -c/-C/--create), adding a git worktree, creating a branch
# (git branch <name>), or publishing/tracking a non-main branch
# (git push -u / --set-upstream). Routine git flow (bare `git push`, commit,
# add, fetch, pull --rebase, cherry-pick, branch listing/deletion) is allowed.
#
# This gates the AGENT, not the human: a person at their own terminal does not
# run through Claude Code hooks, and can always create branches explicitly.
# Pushing is additionally gated at the git layer by .githooks/pre-push.
#
# Exit 2 = block the tool call (message on stderr is shown to the model/user).
set -uo pipefail

cmd=$(jq -r '.tool_input.command // ""' 2>/dev/null || printf '')

if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]+(checkout[[:space:]]+-[bB]|switch[[:space:]]+(-[cC]|--create)|worktree[[:space:]]+add|branch[[:space:]]+[^-[:space:]]|push[[:space:]]+[^|;&]*(-u[[:space:]]|--set-upstream))'; then
  echo 'BLOCKED (main-only repo): the agent may not create or switch to a new branch, add a git worktree, or publish a non-main branch. Do all work on main. Only a human may create branches, explicitly. See AGENTS.md.' >&2
  exit 2
fi

exit 0
