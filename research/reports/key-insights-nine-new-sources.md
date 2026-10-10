# Key insights from nine new sources (input for building negotiation strategies)

Facts distilled from the second research round, in our own words. Each fact is tagged with its source (S1-S9), an evidence strength (strong / moderate / weak, our judgement) and the **knob** it gives us, meaning a parameter that different strategies can set differently. Full notes per source: `research/notes/` (`07-new-sources-harvard.md`, `08-new-sources-princeton-mit-etc.md`, `09-new-sources-open-textbooks.md`). Companion report: [negotiation-research-reading-list.md](negotiation-research-reading-list.md).

**Caveats first.** Several sources are lab studies with people, simulations or toy games on 2023-era models, and none tested an agent against Tacto's bots. Every item is a hypothesis for `backlog.csv` runs. The agents read S1, S2, S3, S4 (IEEE version), S5 (pp. 1-8) and S8 in full or nearly; S6 about half; S7 and S9 partly.

## 1. The nine sources

| ID | Source | Type | Free legal copy |
|---|---|---|---|
| S1 | Sebenius (2017), "BATNAs in Negotiation: Common Errors and Three Kinds of 'No'", HBS WP 17-055 | Working paper, 12 pp | hbs.edu author copy |
| S2 | Brooks and Schweitzer (2011), "Can Nervous Nelly negotiate?", OBHDP | Experiments | hbs.edu author copy |
| S3 | Tsay and Bazerman (2009), "A Decision-making Perspective to Negotiation", HBS WP 10-002 | Review, 29 pp | hbs.edu author copy |
| S4 | Klein, Faratin, Sayama, Bar-Yam (2001/2003), "Negotiating Complex Contracts" | Simulations | DSpace@MIT (hdl 1721.1/48585) |
| S5 | Bianchi et al. (2024), "How Well Can LLMs Negotiate? NegotiationArena", ICML | LLM experiments, toy games | arXiv 2402.05863 |
| S6 | Loschelder, Friese, Schaerer, Galinsky (2016), "The Too-Much-Precision Effect", Psychological Science | 5 experiments, N = 1,320 | SMU repository, open data on OSF |
| S7 | Baarslag, Hendrikx, Hindriks, Jonker (2016), survey of opponent modelling, AAMAS journal | Survey (CC BY) | author copy at CWI |
| S8 | Geiger, Salmen, Zerres (2024), meta-analysis of buyer advantage, Industrial Marketing Management | 196 studies, 669 effect sizes (CC BY) | UvA repository |
| S9 | Zhan et al. (2024), "Let's Negotiate! A Survey of Negotiation Dialogue Systems", Findings of EACL | Survey | arXiv 2402.01097 |

## 2. Important facts, grouped by lever

### A. Alternatives and the walk-away line
- A BATNA is a *course of action turned into a reservation value*, and it can itself be another deal, not only a last resort. Re-estimate it every time new information arrives. [S1, moderate] Knob: how often we recompute the reservation total cost.
- Bringing competing suppliers in **early** is worth more than late bargaining skill. [S1, moderate] Knob: RFQ-style parallel threads from round 1.
- Separate three kinds of "no": a tactical no (a move), a re-set no (reopens terms) and a final no (walk away). [S1, moderate] Knob: when to treat a supplier's `final_offer` as real.

### B. Opening offer
- Early anchors shape the outcome, and negotiators anchor on whatever number comes first. [S3, moderate; S5 for LLMs, moderate]
- **Precision matters:** more precise first offers anchored amateurs more, in a straight line. Experts penalised very precise prices as a sign of incompetence (an inverted U). A plausible reason attached to the number removed the backfire. [S6, moderate to strong, lab-based] Knob: round vs precise opening numbers, with or without a stated rationale.
- A buyer's first offer *amplifies* the small buyer advantage. [S8, moderate]
- Anxiety lowers first offers, so open ambitious and complete. [S2, moderate]

### C. Concessions and closing
- In multi-issue contracts with interdependent terms (price, payment days, contract length), conceding slowly reached only about 94% of the best outcome in simulation. Agents that sometimes accept a **slightly worse bundle** reached 98-99%. [S4, moderate, simulation] Knob: willingness to accept slightly worse bundles to end the search.
- An unconditional conceder gets exploited by a tough opponent, so keep concessions **reciprocal**. The "concede early and often" advice came from a cooperative, mediated setting. [S4, moderate] Knob: reciprocity rule before each concession.
- People discount concessions from the other side (reactive devaluation), so label your own concessions as costly and explain the reason. [S3, moderate]
- LLM agents split the difference by reflex even when it is irrational. [S5, moderate for LLMs, 2023 models] Knob: forbid auto-midpoint; compute the step from total cost.
- Anxious negotiators exit early and earn less (7.19 against 8.04 in a three-issue chat). [S2, moderate] Knob: minimum number of rounds before accepting or walking.

### D. Issues, packages and information
- Negotiators assume a fixed pie. Add issues and trade across them. [S3, moderate]
- Slow, single-term concessions miss value that cross-term packages find. [S4, moderate] Knob: price-only vs multi-issue packages; number of packages (see the companion report for 2-3 equivalent packages).
- Opponent modelling (learning the other side's deadline, issue preferences, bidding and acceptance behaviour) is a well-developed field. Methods for the reservation value and deadline exist **only for single-issue negotiation**. [S7, moderate] Knob: lightweight model of the supplier's preference weights from which package it picks.
- Datasets and metrics for negotiation dialogue split into integrative and distributive. Little procurement coverage. [S9, weak for our use] Knob: evaluation split into value created vs value claimed.

### E. Power, role and context
- The "buyer advantage" in sales negotiation is **small**, nearly vanishes in B2B and for experienced negotiators; power and information matter most; the number of issues did not matter. All lab data. [S8, moderate] Knob: do not rely on being "the buyer"; invest in information and alternatives instead.
- Ambiguous behaviour is read as hostile, and written negotiation had more impasses in earlier work. [S3, weak to moderate] Knob: neutral, explicit e-mail wording; state intent clearly.
- Fairness judgements are self-serving on both sides, so do not expect the other side to be fair by default. [S3, moderate]

### F. Tone and pace
- Anxiety lowers expectations and speeds replies. High self-efficacy removed the early-exit effect. [S2, moderate; human emotion, may not transfer to a bot] Knob: fixed aspiration set before the talk; deliberate reply pacing within the 60-second limit.
- Prompts that make an LLM "desperate" or "cunning" shift outcomes. [S5, moderate for LLMs] Knob: persona and tone of the system prompt, tested as a variable.

### G. The supplier may be an LLM
- Supplier bots are probably LLM-based, so S5's findings (anchoring, reflexive split-the-difference, prompt-driven shifts) apply to *them* as well as to our agent. [S5, moderate, inference] Knob: exploit predictable biases ethically (well-grounded anchors, packages) and never rely on tricks that need deception.

## 3. Knobs available for strategies (summary)

| Knob | Values to vary | Source |
|---|---|---|
| Opening depth and precision | 5/10/15 percent under the opening quote; round vs precise number; with/without rationale | S3, S6, S8 |
| Rationale attached to the opener | none / data ID / cost breakdown | S6 |
| Concession schedule | constant, shrinking, none until reciprocated | S4 |
| Reciprocity gate | concede only after the supplier moves | S4, S3 |
| Package count | price-only, 1, 2-3 packages | S3, S4 |
| Accept-slightly-worse rule | strict best, or accept within x percent of best known bundle | S4 |
| Alternatives timing | RFQ threads from round 1 vs later | S1 |
| Reservation update | every round, or only on new information | S1 |
| Minimum rounds before exit | 0 / 3 / 5 | S2 |
| Supplier preference model | none / pick-based inference | S7 |
| Tone and persona | neutral / warm / firm / "cunning" | S2, S5 |
| Anti-reflex rule | no auto-midpoint; step size from total cost | S5 |

## 4. Gaps this list cannot fill

- No source here tests e-mail negotiation against supplier bots, so all strengths describe human labs, simulations or toy LLM games.
- S6 and S7 were read only partly; S9 has little procurement content.
- No verified Harvard source on supplier or e-mail negotiation specifically; no usable Princeton, Wharton or MIT OpenCourseWare full text was found.

## 5. Next step

Combine these knobs with the first report's 17 testable rules into 3-5 named **strategy variants** (for example "anchor-and-package", "competitive-alternatives", "reciprocal-collaborative"), implement each as a version in our agent, and log every run in `backlog.csv`.
