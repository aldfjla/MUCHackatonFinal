# Schools of thought in negotiation (blueprint for our player agents)

Purpose: a plain-language guide to the main schools of negotiation thinking, written so each one can be turned into a **player agent** like the kit's `naive.py` (a class with `decide(case, threads)`). Facts come from general knowledge of the field (marked **[general]**) and from the sources we collected (marked **[S#]** or by name; see `RESEARCH.md`, Part A, for the source table). Everything is in our own words and is a **hypothesis to test**, not a proven recipe: none of the sources tested an agent against Tacto's bots.

**Evidence tags used below:** [general] = our background knowledge, not checked against a source in this repo. [PON] = Harvard Program on Negotiation articles (read in full). [Princeton] = the Handbook of Social Psychology chapter (read in full). [S1]-[S9] = the nine newly found sources (`RESEARCH.md`, Part A). [Herold] = Herold et al. 2025 (read in full). [Kelly] = Kelly and Chicksand 2024 (read mostly). [Heunis] = Heunis et al. 2025 (read the body).

## 0. What an agent has to work with (from `naive.py` and the kit)

`decide(case, threads)` returns one message per turn: either an e-mail with up to 3 term sheets, or an action (`accept` a standing term sheet, or `walk_away`). Helpers the kit already gives us: `live_threads` (suppliers still talking), `standing` (a supplier's current term sheet), `latest` (its last event, with a `status` of `open`, `final_offer`, `agreed`, `walked_away` or `no_bid`), `moves_left` (rounds left), `total_cost` (prices any term sheet; this is the score's basis), `complete_offer` (fills the unstated fields), `standard_terms` (what a supplier's quote PDF closes on if we leave a field out). The case holds our alternative (`case["buyer"]["alternative"]`) and its goal label (`stabilise`, `secure_supply`, `quality_first`, `leverage` or `routine`).

The naive agent anchors 10% low, offers the midpoint each round, and accepts when the gap is 1% or less. It only negotiates **unit price** and never uses the data. Every school below changes one or more of: what we open with, how we concede, how many issues we put on the table, what we learn about the supplier, and when we accept or leave.

## 1. Game theory and economic bargaining

**Core idea.** Negotiation is a strategic game. Each side has a **reservation value** (the worst deal it would accept) and an **outside option**. A deal is only possible inside the zone where both reservation values overlap (the zone of possible agreement, ZOPA). Offers also **signal**: what you concede reveals what you can afford. [general]

**Key thinkers and ideas** [general]: Nash (1950) and the Nash bargaining solution; Rubinstein's alternating-offers model (1982), where patience and outside options set the split; Raiffa's decision-analytic view, which treats negotiation as an "asymmetric prescriptive" problem (give the best advice to one side, without assuming the other is perfectly rational); auction theory, including the result that adding one more bidder can beat clever bargaining.

**What it says about behaviour.**
- The party with the stronger alternative and more patience gets more.
- Information is power; hidden limits are the core difficulty.
- A credible alternative is worth more than negotiating skill. [S1] agrees: bringing in competing suppliers **early** is worth more than late bargaining skill.

**Evidence from our files.** [PON] and [S1] support the alternative-centred view. Fugger et al. 2019 (reverse auctions cut price but reduce cooperation) is an economics-style result. [S8]: the "buyer advantage" is small in B2B, which fits the idea that outside options, not role, decide the split.

**Strengths:** precise, easy to compute, ties directly to our scoring (total cost vs `C_best`).
**Limits:** needs estimates of the supplier's reservation value; real people and LLM suppliers are not perfectly rational; the formal models mostly cover a single price. [S7]: methods for learning reservation value and deadline exist **only for single-issue** negotiation.

**Agent blueprint: "Rational Bargainer".**
- Compute our own reservation as the total cost of the best alternative (`case["buyer"]["alternative"]`, or the best competing quote); never accept anything worse.
- Run RFQ threads in parallel and let suppliers compete; accept the cheapest standing term sheet by `total_cost`.
- Concede along a planned schedule toward our reservation; estimate the supplier's floor from its concession pattern.
- Close when the next expected improvement is smaller than the risk of losing the deal.

## 2. Principled, interest-based negotiation (Harvard school)

**Core idea.** Don't haggle over positions. Separate the people from the problem, find the **interests** behind the demands, invent options for mutual gain, and decide by objective standards. Know your **BATNA**. [PON, general: Fisher, Ury and Patton, *Getting to Yes*]

**What it says about behaviour.**
- Ask why a demand matters; the underlying need is often cheaper to meet than the demand. [PON]
- Compare offers on equal terms, because a cheap headline price can hide worse coverage. [PON]
- Don't mirror hard tactics; answer with questions and options. [PON]
- A BATNA is a course of action turned into a reservation value, can itself be another deal, and should be re-estimated as information changes. [S1]
- Prepare three kinds of "no": tactical, re-set and final. [S1]

**Evidence.** Mostly practitioner framework and lab studies; the Princeton chapter supports multi-issue trade-offs and alternatives as the main power source (strong) but warns that warmth and thanks can **reduce** concessions. Evidence for "separate people from the problem" as a rule is thinner than for BATNA.

**Agent blueprint: "Interest Explorer".**
- Early turns: ask what matters most (cost drivers, payment timing, volume, delivery); read the supplier's notes and letters from the data package to guess priorities.
- Send 2-3 equivalent term sheets that trade price against payment days, volume or contract length, and log which one the supplier picks.
- Back every claim with real data IDs (indices, should-cost); never invent figures.
- Tone: polite and neutral; thank once at the close, not for each concession.
- Accept the best package that beats the BATNA.

## 3. Behavioural and psychological school

**Core idea.** People negotiate with predictable biases. Beat them in yourself and use them (honestly) in the other side. [general: Bazerman, Neale, Thompson]

**Key effects and sources.**
- **Fixed-pie bias:** assuming the other side's gain is your loss, so missing trades. [S3, Tsay and Bazerman]
- **Anchoring:** the first number shapes the outcome. Meta-analytic evidence (Orr and Guthrie 2006; Petrowsky et al., reported at conference level) supports a first-mover advantage with high variation; extreme offers raise the risk of impasse. [Princeton, S3]
- **Precision:** more precise first offers anchor amateurs more; experts see very precise numbers as incompetence, unless a plausible reason is attached. [S6, Loschelder et al. 2016]
- **Reactive devaluation:** people discount concessions the other side makes; **self-serving fairness**; reading ambiguous behaviour as hostile; written negotiation had more impasse. [S3]
- **Emotion and anxiety:** anxiety lowers expectations and first offers, speeds replies, and leads to early exits and lower profit (7.19 vs 8.04 in a three-issue chat). [S2, Brooks and Schweitzer]
- **Anger** can extract concessions only from low-power targets and risks retaliation; **gratitude** can invite tougher behaviour. [emotion notes; Princeton]
- **Deception** destroys trust and is not fully repaired. [Kong, Dirks and Ferrin 2014, Schweitzer et al. 2006, Princeton]

**Replication caution.** Anchoring is the best-supported finding; power-posing and similar power-priming effects did not replicate; anger effects range from fragile to moderate. [replication notes]

**Strengths:** most experimental evidence in the field sits here, and it describes failure modes we must also avoid.
**Limits:** almost all lab studies with people; LLM suppliers may or may not share these biases (see school 5).

**Agent blueprint: "Anchor-and-Frame".**
- Open with a specific, ambitious but defensible number with a stated rationale (data ID); test round vs precise numbers.
- Frame our concessions as costly and give a reason each time; make reciprocal asks.
- Neutral, explicit e-mail wording; no threats, no anger, no bluffing.
- Never reveal the walk-away price; enforce this with an outbound check in code.
- Don't reply instantly; don't exit early (minimum rounds before leaving).

## 4. The negotiator's dilemma and dual-concern school (create value vs claim value)

**Core idea.** Every negotiator faces a tension: sharing information and cooperating **creates** value but exposes you to exploitation; hard tactics **claim** value but destroy trust and shrink the pie. Good negotiators mix both and switch with the situation. [general: Walton and McKersie; Pruitt and Rubin's dual-concern model; Lax and Sebenius]

**What our sources add.**
- Hard lines win economically while soft lines win on the relationship; reciprocating the other side's concessions helps. [Hüffmeier et al. 2014, meta-analysis of 34 studies, abstract-level]
- Practitioners mix distributive and integrative moves; a firm stance is often needed near the end. [Kelly]
- **Strategic adaptability:** switch tactic on cues (content, opponent behaviour, deadlock, outside context); fixed "collaborate first, then compete" phases don't match real behaviour. [Heunis]
- In simulated multi-issue contracts, slow single-term concession reached only about 94% of the best outcome; agents that sometimes accept a slightly worse bundle reached 98-99%; an unconditional conceder gets exploited. [S4, Klein et al.]
- A competitive buyer bot won bigger discounts, but a collaborative one earned more trust; the competitive prompts included threats, so the two effects are confounded. [Herold]
- Style by item type is contested: Kang et al. 2018 suggest competitive for leverage items, collaborative for strategic, accommodating for bottleneck; Hesping and Schiele 2016 found all levers used in all quadrants. [procurement notes]

**Strengths:** matches real practice; supports adaptive agents.
**Limits:** "when to switch" is hard to define; most evidence is from training or lab designs, not outcomes.

**Agent blueprint: "Adaptive Switcher".**
- Start collaborative and information-seeking; hold a **reciprocity gate** (only concede after the supplier moves).
- Switch to firm on cues: stall for two rounds, supplier shows `final_offer`, rounds running low.
- Accept-slightly-worse rule: near the end, take a bundle within x% of the best known total cost instead of continuing.
- Soften on cues: supplier concedes, or reveals constraints.

## 5. Computational school (automated negotiation and AI agents)

**Core idea.** Design software agents with explicit strategies. Standard building blocks [general: Faratin, Sierra and Jennings; the ANAC agent competition; Baarslag et al.]:
- **Time-dependent tactics:** concession as a function of elapsed time, with "Boulware" (concede late, hold firm) and "Conceder" (concede early) families.
- **Behaviour-based tactics:** respond to the opponent's last move (tit-for-tat style).
- **Opponent modelling:** learn the other side's deadline, issue preferences, and bidding and acceptance behaviour. [S7]
- **Acceptance strategies:** accept when the offer beats our next planned bid or a threshold that falls with time.

**Evidence on LLM agents.**
- LLM agents anchor on the first price (Spearman 0.716 in a toy game) and split the difference by reflex, even when irrational; prompts like "desperate" or "cunning" shift outcomes. [S5, Bianchi et al.; 2023-era models]
- In a large AI-vs-AI study, warm prompts did better; dominance helped claim value but long conversations ended in impasse (Vaccaro et al., reported as PNAS; abstract-level).
- The fastest-conceding AI buyer got the worst surplus and deal rate in a 15,000-negotiation preprint; the best-supported mitigation is a **hard-coded offer schedule with the LLM writing only the wording**.
- Disclosing AI identity reduced perceived fairness and trust in one experiment (preprint). [AI notes]
- The supplier bots may themselves be LLMs, so these biases may apply to them, not just to us. (inference)
- A survey of negotiation dialogue systems exists but covers procurement little. [S9]

**Strengths:** directly implementable; clear separation of "decide the numbers in code" from "write the e-mail with the model".
**Limits:** most results are simulations, toy games, older models, or preprints; the real suppliers are described as reacting like people.

**Agent blueprint: "Boulware Bot".**
- A code-level concession function over rounds (hold firm early, concede late), tied to `moves_left`.
- A simple supplier model: track which package it picks and how fast its price moves; estimate its floor.
- The LLM (optional) writes e-mail text only; code computes all terms with `total_cost`; add a guard that blocks any message revealing our limit.
- Fall back to the naive move if the model fails or times out (60 s limit per message).

## 6. Procurement overlay (Kraljic and buyer-supplier power)

**Core idea.** Buyers segment what they buy and match the approach. Kraljic's 1983 portfolio splits items by profit impact and supply risk into leverage, strategic, bottleneck and routine items (only the teaser was readable for us; the rest is [general]). The arena's goal labels (`leverage`, `routine`, `secure_supply`, `stabilise`) resemble these categories (our inference).

**What our sources say.** Power use on suppliers tends to harm relationship quality (a study of 102 outsourcing pairs); reverse auctions cut price but reduce cooperation (Fugger et al.); a buyer's "role advantage" is small in B2B and for experienced negotiators, with power and information doing the work [S8]; professional buyers pushed back harder than students, with discounts of only 1-5.5% against about 10% for students [Herold].

**Agent blueprint: "Portfolio Router".** A thin wrapper that reads `case["category_goal"]` and picks one of the archetypes above (for example competitive Anchor-and-Frame for `leverage`, collaborative Interest Explorer for `stabilise`, accommodating for `secure_supply`), then logs which archetype ran. Strategic and bottleneck goals also charge for leaving the supplier below a sustainable margin, so avoid squeezing those.

## 7. Shared safety layer for every agent

These rules come from all schools and the scoring rules; put them in code, not in the prompt:
1. **Never accept** a term sheet whose `total_cost` is worse than our alternative or worse than the opening quote; walk away instead (a deal worse than the opening scores 0).
2. **Hard-code** the walk-away limit and a per-round concession cap; people and models drift past limits mid-talk. [Princeton, S5]
3. **Never reveal** the walk-away price, budget or urgency; block outgoing messages that contain them.
4. **Never lie or invent** figures or IDs; the arena marks wrong citations `contradicted` and it costs trust.
5. **Read the quote PDF** (`standard_terms`) before accepting; unstated terms default to the supplier's standard terms.
6. **Check full coverage**: a shorter contract can score 0 even at a lower price.
7. **Stay inside 60 seconds** per message; fall back to the naive move on failure.
8. We always want a deal when one beats the alternative; walk away only when none does.

## 8. Strategy-to-agent table

| School | Agent name | What changes vs `naive.py` | Main knob to test | Main risk |
|---|---|---|---|---|
| Game theory | Rational Bargainer | Reservation from alternative, parallel RFQ threads, planned schedule | Concession schedule; thread count | Bad supplier-floor estimates |
| Principled | Interest Explorer | Questions, 2-3 packages, data-backed claims | Package count; price-only vs multi-issue | Packages ignored or misread |
| Behavioural | Anchor-and-Frame | Ambitious precise opener with rationale, framed concessions | Opening depth, precision, rationale on/off | Impasse from extreme openers |
| Dual-concern | Adaptive Switcher | Cue-based switching, reciprocity gate, accept-slightly-worse | Cue thresholds; gate on/off | Switching too early or late |
| Computational | Boulware Bot | Time-based concession curve, simple supplier model, LLM for wording only | Curve shape; model on/off | Overfitting to the simulator |
| Procurement | Portfolio Router | Picks an archetype per `category_goal` | Mapping goal to archetype | Mapping is weakly supported |

## 9. How to build them (next steps)

1. Create one class per archetype under `agent/arena_kit/agents/` (same `decide(case, threads)` shape as `naive.py`); reuse the safety layer from section 7 in a shared helper.
2. Register each in `agent_factory` and the `--agent` choices in `cli.py` (two places).
3. Test in the offline simulator (S01-S03), then on the real practice cases that are beatable (P05, P10, P11, P18) with P01 as a control; spend real sessions carefully (200 per 24 hours).
4. Log every run in `backlog.csv` with the version column as `v<N> - <name>` (for example `v2 - niko`) and a note naming the archetype and the knob changed.
5. Change one knob per version so score changes can be explained in the pitch.

## 10. Gaps and honesty notes

- Sections marked [general] come from background knowledge and were not verified against a source in this repo.
- Kraljic (1983), Malhotra and Bazerman (2007) and the Raiffa book were not read; Voss's tactics have no peer-reviewed test.
- The Vaccaro and several LLM-negotiation findings were read at abstract or summary level.
- None of this has been run against Tacto's suppliers.
