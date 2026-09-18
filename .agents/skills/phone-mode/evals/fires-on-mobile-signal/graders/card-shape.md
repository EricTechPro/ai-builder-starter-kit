---
type: llm
focus: last_message
weight: 2
---

PASS if the reply is a phone card:

- The answer or outcome is on the first line. No preamble, no restating the question.
- Roughly 15 lines or fewer.
- Sections, if any, are an emoji header plus bullets. Between one and four of them.
- No em dashes, no tables, no code block unless a command was asked for.
- At most one file path.
- It ends with a single next action for the reader.

FAIL if it opens with a preamble, runs long, uses a table, or asks the reader to make more
than one decision.

Judge the shape, not whether the answer about the commit is correct.
