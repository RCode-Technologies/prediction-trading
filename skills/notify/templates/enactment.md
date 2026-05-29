# `enactment`

Sent by `daily-close` step 9d (`enact`, Sundays) on every status transition. **Suppression-exempt**
— the human must always see autonomous code changes and how to veto them, in paper *and* mainnet.
Not date-deduped (each status is a distinct, must-see event).

Visual-first. ≤12 short lines. The `enacted` variant is the default; swap the header + relevant lines
per § Variants.

```
⚙️ *Enacted* `<slug>` · `<mode>`
*<title>*

🔧 `<sha>` · <n> file(s)
   `<path>` · `<path>`

🔭 *Watching* <baseline metric armed for auto-rollback, ≤80 chars>

↩️ *Veto* `git revert <sha>`  ·  or set `LEDGER` status `vetoed`

📄 `proposals/<id>.md`
```

## Variants (by `enactment.status`)

- `enacted` (default, above): `⚙️ *Enacted*`.
- `reverted` (auto-rollback): `↩️ *Auto-reverted* \`<slug>\``. Replace the `🔧` line with
  `🔧 \`<revert sha>\` reverts \`<orig sha>\``; the `🔭 *Watching*` line becomes
  `📉 *Reason* <metric that regressed, ≤80 chars>`; drop the `↩️ *Veto*` line.
- `refused` (→ `awaiting_human`): `🙅 *Needs you* \`<slug>\``. Drop `🔧`/`🔭`/`↩️`; add
  `🚧 *Why* touches protected core or capital — won't self-enact.` Keeps the `📄` pointer.
- `failed`: `⚠️ *Enact failed* \`<slug>\``. Replace `🔧`/`🔭`/`↩️` with
  `🩺 *Reason* <validation/push failure, ≤80 chars>` and `↩️ Discarded — no commit pushed.`
- `live` (graduation): **not sent** (silent — see SKILL.md). No template needed.

## Values & rules

- `<slug>`, `<id>`, `<title>` from the RFC frontmatter. `<sha>` from the enactment commit.
- `<mode>` = `config/mode.json.network`.
- `<n>` + the path list from `enactment.files` (show ≤4 paths; `+k more` if longer).
- `🔭 *Watching*` summarizes the armed baseline (`enactment.baseline`) — e.g.
  `brier_skill 0.07 · null_cycles 0`.

## Markdown safety

Per § Markdown safety in `SKILL.md`. Backtick-wrap `<slug>`, `<id>`, every `<path>`, both shas, the
mode tag. Sanitize `<title>` + any free-text reason — strip unbalanced `*` `_` `` ` ``, collapse
whitespace. Never include secrets, wallet addresses, or token-bearing URLs.
