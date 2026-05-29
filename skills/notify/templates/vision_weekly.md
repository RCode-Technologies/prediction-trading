# `vision_weekly`

Sent by `daily-close` step 10 on Sundays after the deep `envision` pass (alongside `weekly_recap`).
Date-deduped. This is the week's defining reflection — the agent stepping back across the whole
system and the mission.

Visual-first synthesis. ≤14 short lines.

```
🌅 *Weekly Vision* `<YYYY-Www>` · `<mode>`

🧭 *Theme* <one-line synthesis of the week, ≤120 chars>

⚡️ *Challenge* <the assumption challenged this week, ≤120 chars>

✅ *Self-approved* `<id>` — <title, ≤80 chars>
   ⚙️ <enact_line>

🧫 *Open* <the live open question carried forward, ≤100 chars>

📄 `proposals/VISION.md` · open proposals: *<ledger_open_n>*
```

**Values & rules:**
- `<YYYY-Www>` = ISO week. `<mode>` = `config/mode.json.network`.
- `*Theme*` / `*Challenge*` / `*Open*` summarized from the Sunday `VISION.md` revision + `vision`
  event (`deep:true`). The `⚡️ *Challenge*` line is mandatory (surprise mandate); never omit it.
- `✅ *Self-approved*` block: present only if a proposal was set `self_approved` this Sunday.
  - `<enact_line>`: if `skills/enact` ran this cycle → `Enacted \`<sha>\` — veto with \`git revert\`.`
    else → `Enacts next — veto anytime before then.`
  - No self-approval → drop the whole `✅` block.
- `<ledger_open_n>` from the `vision` event.

## Markdown safety

Per § Markdown safety in `SKILL.md`. Backtick-wrap `<id>`, week tag, sha, paths, mode tag. Sanitize
every free-text line — strip unbalanced `*` `_` `` ` ``, collapse whitespace. No raw URLs / tokens.
