# `strategy_evolution`

Sent by `daily-close` step 10 (after `daily_summary`, and `weekly_recap` on Sundays) when today's `reflection` event in the trade-log satisfies **either**:

- `edited == true` (any `reason`: `normal` / `risk_tighten` / `auto_revert`), OR
- `edited == false AND reason == "regression_blocked"` (gate held — system tried to learn but self-refused).

Never fires on `reason == "no_data"` or any other silent no-op — that's noise.

Visual-first PM brief. Pick the variant matching `reason`. All three render in ≤12 short lines.

## Variant A — edit (`reason == "normal"` | `"risk_tighten"`)

Header swaps 🧠 → 🛡 and appends ` · risk-tighten` when `reason == "risk_tighten"`.

```
🧠 *Strategy* `v<old>` → `v<new>` · `<mode>`

🔧 *Change*
  • <bullet 1>
  • <bullet 2>
  • <bullet 3>

📊 *Why* Brier *<before>* → *<after>* · Δ *<±x>* (30d)

⏭ Active next cycle
```

**How to compose bullets (max 3, most material first):**

1. Each non-empty entry in `promoted[]` → `hypothesis <id> → watch`.
2. Each non-empty entry in `demoted[]` → `hypothesis <id> → demoted (+14d)`.
3. Each non-empty entry in `probation_started[]` / `probation_resolved[]` → `<id> probation` / `<id> promoted`.
4. Up to 2 largest-magnitude entries in `per_feature_tag[]` or `per_source[]` → `<tag>: adj <old>→<new>` or `<provider>: penalty <x>`.
5. If bullets still <3 and `rationale` is concrete (names a feature/market class), append a single italicized 1-line rationale bullet (≤80 chars, strip newlines).

If no bullets qualify, drop the `🔧 *Change*` block entirely.

**Values:**
- `<before>` / `<after>` = `metrics.brier_skill_before` / `metrics.brier_skill_after`, 3 dp.
- `<±x>` = signed delta, 3 dp. Drop the `📊 *Why*` line entirely if both are `null` (cold start with risk_tighten — rare).

## Variant B — auto-revert (`reason == "auto_revert"`)

```
↩️ *Revert* `v<failed>` → `v<good>` · `<mode>`

📉 *Why* 3 reflections Brier worse than `v<good>` (*<recent>* vs *<good>*)

⏭ Active next cycle
```

**Values:**
- `<failed>` = `prior_version`. `<good>` = `reverted_to`.
- `<recent>` = `metrics.brier_skill_after` (or `brier_skill_before` if `after` is `null`).
- `<good>` = `metrics` field for last-good baseline (fall back to literal "baseline" if not present).

## Variant C — guard held (`edited == false AND reason == "regression_blocked"`)

No edit applied; current version stays. No `⏭` line.

```
🛡 *Guard held* `v<n>` · `<mode>`

🚫 Sim Brier *<after>* < threshold (*<before>*−0.005)

🧪 *Pending*
  • <pending 1>
  • <pending 2>
```

**Values:**
- `<n>` = `prior_version`.
- `<before>` / `<after>` from `metrics`.
- Pending bullets = up to 3 entries from `pending[]`. Each ≤80 chars, newline-stripped. Drop the `🧪` block if `pending[]` is empty.

## Markdown safety

Per § Markdown safety in `SKILL.md`. Backtick-wrap every version tag (`v<n>`), hypothesis id, provider, and feature_tag. Sanitize bullets — strip unbalanced `*` `_` `` ` ``, collapse whitespace. Never include raw market URLs or token-bearing strings.
