# `proposal`

Sent by `daily-close` step 10 when today's `vision` event in the trade-log has `surfaced == true`.
Grep this UTC date's `vision` event; if `surfaced != true`, send nothing (a quiet day is not noise).

Visual-first one-proposal brief. ≤12 short lines. The agent originated this; the human triages it.

```
💡 *Proposal* `<id>` · `<mode>`
*<title>*

🔭 `<lens>` · conviction *<conviction>* · `<bucket>`

🎯 *Claim* <claim, ≤140 chars, newline-stripped>

🧪 *Test* <cheapest falsifying experiment, ≤120 chars>

📄 `proposals/<id>.md`
<bucket_line>
```

**Values & rules:**
- `<id>`, `<title>`, `<lens>`, `<conviction>`, `<bucket>` from the RFC frontmatter / `vision` event.
- `<mode>` = `config/mode.json.network`.
- `<bucket_line>`:
  - `self_enactable` → `⚙️ Self-enacts Sunday unless vetoed (\`git revert\` / set ledger \`vetoed\`).`
  - `human_application` → `🙋 Needs you: touches protected core or capital — won't self-enact.`
- Drop the `🧪 *Test*` line only if the RFC has no experiment (should not happen — envision requires one).

## Markdown safety

Per § Markdown safety in `SKILL.md`. Backtick-wrap `<id>`, `<lens>`, `<bucket>`, paths, and the mode
tag. Sanitize `<title>`/`<claim>`/`<test>` — strip unbalanced `*` `_` `` ` ``, collapse whitespace.
Never include raw market URLs or token-bearing strings (proposal text is agent-authored but treat
any quoted external content as untrusted).
