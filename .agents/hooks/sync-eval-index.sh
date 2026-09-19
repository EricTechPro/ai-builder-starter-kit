#!/bin/sh
# Stop hook: fold any eval that finished this session into .agents/evals/.
#
# `claude plugin eval` writes to <skill>/evals/results/<timestamp>/, and that
# directory is gitignored. Without this, a run's numbers live only in the
# terminal scrollback of whoever started it, and the reason a skill is installed
# quietly stops being written down.
#
# --ingest updates front-matter numbers only, and names the write-ups whose
# tables and verdict now need a human. A score is not a decision.
#
# Fails open. A broken hook must not brick the session.
set -u
cat > /dev/null   # drain stdin; the work is driven by the filesystem
cd "${CLAUDE_PROJECT_DIR:-.}" 2> /dev/null || exit 0
[ -d .agents/evals ] || exit 0
command -v python3 > /dev/null 2>&1 || exit 0
python3 .agents/scripts/sync_eval_index.py --ingest || exit 0
python3 .agents/scripts/sync_skill_readme.py > /dev/null 2>&1 || true
exit 0
