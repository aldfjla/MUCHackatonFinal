# Submission text (ehl.gg form)

**Repo:** https://github.com/aldfjla/MUCHackatonFinal — branch `v1-niko`, commit tagged `submission`
(agent code = tag `better-verified-v35`, `005862b`). README has setup, env var names and the run command.

**Agent:** `better`, rules only, no language model.

**Short description.**
Prepares: loads the Tacto data package and the Sunday release, and builds verifiable, cited claims for
the supplier at hand (cost-driver indices, our purchase history, should-cost, scorecard, competing bids,
contract notice periods).
Reads: the supplier's standing term sheets and status, which asks it refused or repriced, and cash-shortage
signals in its text.
Decides: prices every package with the arena's total-cost function; anchors at 0.80 of the ask (0.90 when
supplier health matters), matches the supplier's visible concessions with a minimum step, sends one to
three equal-cost sheets that trade levers (payment, contract length, index clause, latest effective
date), enforces must-haves on every sheet, and in strategic categories prices against a supplier-specific
health estimate with an uncertainty band.
Closes: accepts when the complete package beats the opening quote and the best alternative in the
pessimistic world; accepts a passing final offer at once; never walks while a supplier is alive and
counters at the supplier's price on the last move. Every decision is logged with its reason and cost
breakdown.

**Result:** practice mean 0.72 over the ten hosted cases, 10/10 deals, reproduced in 100 consecutive
sessions. Full run log in `backlog.csv`; replays linked per row.
