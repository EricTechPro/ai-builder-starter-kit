---
name: phone-mode
description: Switch replies to phone-friendly card format for when Eric is away from the desk. Use when he says he is on the go, mobile, on his phone, outside, walking, driving, in the car, going remote, telegram mode, tg mode, or runs /phone-mode. Turn it off with /phone-mode off, "back at desk", "desktop mode", "normal mode", or "give me the long version".
---

> [!IMPORTANT]
> ## 🚨 RULE ONE: PLAIN WORDS
>
> **Write so the meaning lands on the first read. Every time.**
>
> This covers everything this skill produces: chat replies, tickets, status notes, emails.
>
> - Short sentences. One idea each.
> - Put the answer or the decision first.
> - Prefer the direct word when both are accurate. "pay" not "remit", "help" not "facilitate".
> - Keep the correct technical term when it is the clearest word. API, token, deployment and
>   exact product names stay.
> - Two lines per paragraph, at most.
> - Cut any line the reader did not ask for and does not need in order to act.
> - Never make it simpler by making it less true.
>
> This is a clarity filter. It is not a flattened voice and not an age level.
>
> Full policy, including the direct-words table: [`PLAIN-WORDS.md`](PLAIN-WORDS.md). Read it.

# Phone Mode

Reply **formatting** mode. Not Claude Code's built-in Remote Control (`/remote-control`,
alias `/rc`), which attaches the session to the Claude mobile app. That is transport,
this is style. They compose: Remote Control puts Eric on his phone, Phone Mode makes
the replies readable once he is there.

Enter on any plain-language signal that he is away from the desk. Do not ask him to
confirm, do not tell him to run a command. Switch, confirm in one line, stay in it for
the rest of the session.

Exit on `off`, `stop`, `desk`, `normal`, "back at desk", "give me the long version".

## Reply format

Answer or outcome on line 1, always. Never open with a preamble.

Pick the shape by how messy the thing is:

**Short card** (confirmations, simple answers):
```
✅ Committed. 4 files, message "fix dip ranking"

👉 Push to main?
```

**Sectioned card** (multi-part results, anything with a caveat):
```
✅ Test suite green after the refactor

📊 What changed:
• 3 modules moved under lib/core
• 41 tests passing, 0 skipped
• Bundle down 12 KB

⚠️ Heads up:
• Two snapshots needed updating

👉 Commit this, or keep going?
```

**Failure card** (something broke):
```
❌ Build failed on the typecheck step

🔍 Why:
• Missing type export in lib/models.ts
• Everything else compiled clean

🔧 Options:
• Add the export and rerun
• Roll back the last commit

👉 Which one?
```

**Answer card** (he asked a question):
```
💡 Yes, but only in production builds.

• Dev server reads the env file directly
• Production needs the value at build time
• So the deploy config has to set it too

👉 Want me to add it there?
```

## Hard rules

- Max ~15 lines. Detail goes in a file, not the reply. Say which file.
- 2 to 4 sections max, each an emoji header plus bullets.
- Bold sparingly, on key terms and outcomes only.
- No em dashes. Use a period, comma, colon, or parens.
- No tables. No code blocks unless he asked for code or a command to run.
- No file path dumps. Name at most one path, and only if he needs it.
- End every message with `👉` and exactly **one** decision or next action for him.
- One decision per message. If there are three things to decide, ask the most blocking one and hold the rest.
- No MarkdownV2 backslash escaping. This renders in a terminal, not the Telegram API. Only escape when actually calling `mcp__plugin_telegram_telegram__reply`.

## Caveman layer

Phone Mode controls the **shape** of a reply. Caveman controls the **words** inside it.
Run both: the card structure below stays, the prose inside each bullet gets compressed.

Style borrowed from [juliusbrussee/caveman](https://github.com/juliusbrussee/caveman)
(MIT). Install the real thing for the full mode, hooks and `/caveman` levels. This
section is only the word-level rules Phone Mode needs.

Inside bullets and the line-1 outcome:

- Drop articles (a/an/the), filler (just, really, basically, actually, simply),
  pleasantries (sure, certainly, happy to), hedging. Fragments are fine.
- Short synonyms. "big" not "extensive". "fix" not "implement a solution for".
- Never invent abbreviations (cfg, impl, req, fn). Tokenizer splits them the same as
  the full word, so they save nothing and cost him a decode. Standard acronyms
  (API, DB, HTTP) are fine.
- No causal arrows (→). Own token, saves nothing.
- Technical terms, file names, commands, error strings: verbatim, never compressed.

Where Caveman and Phone Mode disagree, Phone Mode wins:

| Caveman says | Here |
|---|---|
| No decorative emoji | Keep them. The emoji headers are the scan structure on a small screen |
| Never name the mode | One-line confirm on entry is fine, he asked for it |

Drop the compression entirely for security warnings, destructive-action confirms, and
any multi-step sequence where dropped conjunctions could flip the order. Resume after.

## Working style while in this mode

- Bias to doing rather than asking. He is one-handed on a phone, so a plan he has to read is worse than a result he can approve.
- Pick the option you would recommend and proceed. Do not present option menus.
- Run long jobs in the background and report the outcome, not the play by play.
- Do not narrate tool calls, do not paste command output, do not show diffs. Report what changed and the count.
- If you need a decision mid-task, finish everything that does not depend on it first.

## Writing things he has to read or send

Short sentences, ordinary words, one idea per line. No stacked bullets, no nested headers,
no dense tables, no internal file paths or IDs unless he needs them to act.

Hand over **the finished words in a copy-paste block**, never a description of what to say.
*"One thing to tell them so it isn't missed: X"* is homework, not a result.

Never ship a placeholder or an unverified number in front of him. Fill it or cut the line.

When an output has two or more separate blocks he must copy, put a labeled divider around
each one. Format is in [`PLAIN-WORDS.md`](PLAIN-WORDS.md).
