# Negotiation tips and tricks for our buyer agent

Analysis of the sources we could read, tied to the Tacto Negotiation Arena rules ([CHALLENGE.md](CHALLENGE.md)). Per-source notes are in [raw-files/](raw-files/) (own-words summaries, with links and how much was read). How to run and edit the agent: [SETUP.md](SETUP.md). Log every experiment in [backlog.csv](backlog.csv).

**How much to trust this:** the sources are popular Harvard write-ups, one AI-vs-human experiment, one literature review and one teaching study. None tests an agent against Tacto's bots. Treat every tip as a **hypothesis to test in practice runs**, not a fact. Three sources could not be read (see [raw-files/05-not-read.md](raw-files/05-not-read.md)).

## The short version

1. Know your walk-away and never go below it. 2. Be informed before the first message. 3. Be firm on numbers, warm in tone, no threats. 4. Ask why, then trade across issues. 5. Let code hold the limits, not the model.

## Tips and tricks

### A. Prepare (before opening a session; no 60 s clock yet)

| Tip | Why | Arena link | Evidence |
|---|---|---|---|
| Build a **dossier per supplier** from notes, letters, news, scorecards and indices | Informed buyers pay less; know the realistic discount range early | Brief: what moves a supplier is in the data, some only in notes; cache the dossier | Kelly review (moderate) |
| Know your **BATNA** (the case's `alternative`) and price it with `total_cost` | It sets your walk-away and your leverage | No deal scores your alternative; a deal worse than opening scores 0 | PON (strong as principle) |
| Compare offers on **total cost, not headline price** | A cheaper price can hide worse terms | Score is total cost C: payment, freight, lead time, quality, uncovered need | PON (strong) |
| Guess the supplier's **interests** (cash-short, full order book, group approval ladder) | The demand is not the need | Brief: a cash-short supplier may value payment days over price | PON (strong), brief |
| Pick a **goal-based plan** (`leverage`, `routine`, `secure_supply`, `stabilise`, `quality_first`) | Different goals reward different moves | Strategic cases charge for leaving the supplier below a sustainable margin | Kraljic idea (weak: article not read) |

### B. Open

| Tip | Why | Arena link | Evidence |
|---|---|---|---|
| **Anchor with a specific, defensible number**, not a vague ask | Firm numbers drove bigger discounts in the AI experiment | Cite real data IDs; a wrong figure is `contradicted` and costs trust | Herold (moderate) |
| **Open polite and appreciative**; acknowledge the supplier's situation | Collaborative tone gave more trust and wish to deal again | Suppliers react to tone and relationship "as people do" | Herold, PON (moderate) |
| **No threats or ultimatums** | Hard stances get mirrored; threats were confounded with the "competitive" result | P01 replay: the same index argument sent as an ultimatum scored about EUR 13,700 a year worse | PON (strong), arena FAQ |
| **Send 2-3 term sheets** as alternative packages | Shows what the supplier values; multi-issue offers create value | Max 3 term sheets per message; only term sheets bind | PON, Heunis (moderate) |
| **Don't leak** urgency, budget or a missing alternative | It hands over your leverage | Brief tips | Brief |

### C. Middle game

| Tip | Why | Arena link | Evidence |
|---|---|---|---|
| **Ask why** before pushing price (deadline, volume, cash, inventory) | Interests, not positions, open trades | Roles (engineering, finance, quality) answer their topics | PON (strong) |
| **Trade across issues**: price vs payment days, volume, contract length, start date | Value creation beats haggling one number | Faster payment was a trade in the P01 replay (score 0.76) | PON, Heunis (moderate) |
| **Use objective standards** (indices, should-cost, past prices, competing quotes) | Cuts friction; arena checks every cited ID | `verified` claims can disarm a supplier; `contradicted` costs trust | PON (strong), arena FAQ |
| **Mirror the supplier's role**: finance for payment, quality for 8D, logistics for delivery | The right person answers the right topic | Brief: roles behind each supplier | Brief |
| **Switch tactics on cues**: deadlock, supplier softening, new issue, supplier says `final_offer` | Fixed phases don't match real negotiation | Statuses: `open`, `final_offer`, `agreed`, `walked_away` | Heunis, Kelly (moderate) |
| **Use RFQ parallelism**: keep 2-3 threads alive, let them compete | Alternatives are power | RFQ cases run suppliers in parallel; accepting one ends the case | PON, Kelly (moderate) |

### D. Close

| Tip | Why | Arena link | Evidence |
|---|---|---|---|
| **Hold the line near the end**; firm is normal at close | Avoiding conflict at the end leaves value on the table | `final_offer` means more pushing may make it walk | Kelly (moderate) |
| **Read the quote PDF before accepting** | Unstated terms default to the supplier's standard terms | Kit helper `standard_terms` | Brief |
| **Never accept worse than the BATNA**; walk away if needed | A bad deal is worse than none | `guard()` in `agents/llm.py` already refuses bad accepts | PON (strong) |
| **Check the need is fully covered** | A shorter contract can score 0 even at a lower price | FAQ trap example: 12 months covers half the need | Arena FAQ |

### E. Engineering rules for the agent

- **Math in code, wording from the model.** Compute C for every term sheet with `total_cost`.
- **Hard-code limits** (walk-away price, maximum concession per round). The AI experiment authors note the model tended to concede under pushback.
- **Remove unknown or wrong data IDs** before sending (the kit's `guard()` does this).
- **Stay inside 60 seconds** per message; fall back to the naive move if the model fails.
- **Never bluff about alternatives**: citing a competing quote that does not exist is both unethical and risky if checked.
- **Log everything** in `backlog.csv`, one row per run, with the version and what changed.

## Where the sources seem to disagree, and how we use it

- **Competitive vs collaborative:** the experiment found competitive prompts won bigger discounts but collaborative ones built trust. Our reading: be **firm on numbers and options, warm in tone, no threats**. Sources mix these (Kelly and Heunis both describe switching), so this is a hypothesis to test.
- **Students vs professionals:** professional suppliers resisted much harder (savings about 1-5.5% vs near 10%). Assume Tacto's bots are closer to the professionals.
- **Single shot vs relationship:** the experiment had no repeat relationship. Tacto bots remember only within a case, so the relationship value is within-case: tone, appreciation and trades.

## Experiments to run (use `backlog.csv`)

Change one thing per version, run the same cases, compare scores. Start with practice cases where the house agent is beatable (P05, P10, P11, P18) and one solved case (P01) as control.

| Version | Change | Hypothesis |
|---|---|---|
| v1 | Add the per-supplier dossier to `prepare()` | Better data use raises scores on price-increase and raw-material cases |
| v2 | Always send 2-3 term sheets (price vs payment trade) | Supplier reveals what it values; higher score |
| v3 | Tone: appreciation + firm numbers, no threats | Fewer `final_offer` and `walked_away` outcomes |
| v4 | Hard-coded walk-away and concession caps | Fewer bad accepts and fewer late caves |
| v5 | Cue-based switching (deadlock, `final_offer`, softening) | Better closing on RFQ and capacity cases |

## What would make this better

- Read the three missing sources (Kraljic, Malhotra and Bazerman, the Princeton chapter) and the books through your own library access; add short notes under `raw-files/`.
- Read the full replays of practice cases: they show how the real bots respond, which no paper does.
