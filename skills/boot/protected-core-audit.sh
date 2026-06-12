#!/usr/bin/env bash
# Protected-core integrity audit — the mechanical verdict behind boot step 5b.
#
# WHY THIS IS A SCRIPT, NOT PROSE: on 2026-06-10 the inline 5b snippet was an LLM-
# interpreted instruction. Two cycles in a row "reasoned" about authorship, confused a
# genesis/scaffold commit with the newest one (citing e89b223, then 2725337 — both
# unrelated heartbeats that touch none of the protected files), fabricated a violation,
# and halted a clean repo for two days. A committed script removes the judgement: it
# emits one line + an exit code, and boot acts ONLY on that.
#
# RULE: newest-commit author per path is the ONLY signal. `git log -1` = the newest
# commit that touched the path. Genesis/oldest authorship is IRRELEVANT — the repo was
# scaffolded under the agent identity, so a protected file's *first* commit is usually
# agent-authored; one later human commit fully cleanses it. A protected file last-
# committed by the human (!= AGENT_ID) is expected and clean — that is how rails are
# maintained. NEVER reason from genesis, memory, or a guessed hash.
#
# OUTPUT (stdout):
#   PROTECTED_CORE_VIOLATIONS:[ <space-separated offending paths> ]
#   OFFENDING_COMMIT:<short-hash>     # only when the list is non-empty
# EXIT: 0 = clean (5b PASSES), 3 = violation (5b HALTS), 2 = could not run (treat as
#       inconclusive: log + continue, do NOT halt on a non-3 exit).
#
# Path list mirrors config/autonomy.md § Protected core — keep the two in sync (here + there).
set -uo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "AUDIT_ERROR:not_a_git_repo"; exit 2; }

AGENT_ID="${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}"

PATHS=(
  config/autonomy.md
  config/guardrails.md
  AGENTS.md
  skills/boot
  skills/persist
  skills/circuit-breaker
  skills/enact
  skills/recalibrate
  skills/risk
)

violations=""
offending=""
for p in "${PATHS[@]}"; do
  a=$(git log -1 --format=%ae -- "$p")   # newest commit's author ONLY
  [ -z "$a" ] && continue                # no history yet → skip
  if [ "$a" = "$AGENT_ID" ]; then
    violations="$violations $p"
    [ -z "$offending" ] && offending=$(git log -1 --format=%h -- "$p")
  fi
done

echo "PROTECTED_CORE_VIOLATIONS:[$violations ]"
if [ -n "$violations" ]; then
  echo "OFFENDING_COMMIT:$offending"
  exit 3
fi
exit 0
