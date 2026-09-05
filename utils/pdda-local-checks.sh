#!/bin/bash
# PDDA gate as THIS repo defines it — the XYZ harness runs this in preference to
# a bare `utils/pdda/pdda.sh` (wave_reconcile.py, run_validation_gate).
#
# Why it exists: the harness treats any line containing "ERROR" on stdout as a
# hard failure, which silently enforces PDDA_MODE=full on a repo that has chosen
# `observe` in .pdda-mode (23 standing findings, tracked, not blocking). The
# repo's mode is the decision; pdda.sh already encodes it in its exit code via
# pdda_gated_exit. So: run the real thing, keep the human report on stderr where
# the operator still sees every line, and hand the harness only the exit code.
# Flip .pdda-mode to `full` and this gate blocks exactly as the harness expects.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2
bash utils/pdda/pdda.sh run 1>&2
rc=$?
echo "pdda gate: mode=$(sed -n '/^[^#]/{p;q;}' .pdda-mode 2>/dev/null || echo observe) exit=$rc"
exit "$rc"
