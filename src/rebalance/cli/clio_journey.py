"""`rebalance clio-journey-replay` — opt-in GH-230 historical CLIO journey replay.

Thin passthrough to `ingest.clio_journey.main`, which owns the argparse surface, so
`--help` and every option are forwarded verbatim (GH-249: relocated out of `utils/`
under the GH-241 script-inventory ratchet).
"""

from __future__ import annotations

import typer

from rebalance.cli._core import app


@app.command(
    "clio-journey-replay",
    add_help_option=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def clio_journey_replay_cmd(ctx: typer.Context) -> None:
    """Replay a frozen CLIO export into a private journey directory (no ingestion, no model calls)."""
    from rebalance.ingest.clio_journey import main

    main(ctx.args)
