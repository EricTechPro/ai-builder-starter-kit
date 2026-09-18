---
type: regex
pattern: "👉"
match: "count:1"
target: last_message
weight: 2
---

The hard rule the format lives or dies on: every reply ends with exactly one 👉 and exactly
one decision. Two means the reader has to hold state while one-handed on a phone.

This is a regex rather than a rubric on purpose. A judge model will forgive a second
decision if the prose reads well. A count will not.
