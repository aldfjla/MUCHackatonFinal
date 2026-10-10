# Negotiation research (one file)

Everything we collected on negotiation theory and procurement negotiation for the Tacto buyer agent, merged into one file on 2026-10-10. All text is a summary in our own words; no copyrighted text is stored. Working rules and tips live in `RESOURCES.md`; challenge facts in `CHALLENGE.md`.

**How to read this file**
- **Part A** has the two syntheses: a ranked reading list with 17 testable rules, and nine new verified sources grouped by strategy lever.
- **Part B** holds the notes on sources we read at full-text level (Harvard PON articles, Herold 2025, Kelly and Chicksand 2024, Heunis 2025, the Princeton Handbook chapter) plus what we could not read.
- **Part C** holds the raw notes from the deep-research agents. Only notes 07-09 reached full-text level for their sources; the others rely on abstracts and search snippets, as each note says.

**Caveat:** none of these sources tested an agent against Tacto's bots, so every rule is a hypothesis for the experiments logged in `backlog.csv`.

## Contents

- Part A. Syntheses (start here)
  - Anchor high, trade widely, never lie: negotiation evidence for our buyer agent (`negotiation-research-reading-list.md`)
  - Key insights from nine new sources (input for building negotiation strategies) (`key-insights-nine-new-sources.md`)
- Part B. Full-text reading notes (sources we read in full or mostly)
  - Harvard Program on Negotiation: 4 articles (read in full, 330-900 words each) (`01-pon-getting-to-yes.md`)
  - Herold, Heller, Rozemeijer, Mahr (2025): "Brave new procurement deals" (`02-herold-2025-ai-buyer.md`)
  - Kelly and Chicksand (2024): bargaining in purchasing and supply management (systematic review) (`03-kelly-chicksand-2024-bargaining-review.md`)
  - Heunis et al. (2025): strategic adaptability negotiation training in purchasing (`04-heunis-2025-strategic-adaptability.md`)
  - Sources we could not read (honest gaps) (`05-not-read.md`)
  - Notes: "Negotiation" chapter, Handbook of Social Psychology (6th ed.) (`06-princeton-handbook-negotiation-chapter.md`)
- Part C. Search notes (deep-research output, mostly abstract level)
  - Books and handbooks on negotiation theory and procurement negotiation (for an AI buyer agent) (`01-books-and-handbooks.md`)
  - Core experimental findings on bargaining behaviour (for an e-mail buyer agent with multi-issue term sheets) (`02-core-bargaining-evidence.md`)
  - Social-psychology of negotiation: emotion, deception/trust, e-mail, language style, tone (for an AI buyer agent e-mailing supplier bots) (`03-emotion-trust-email.md`)
  - Procurement and buyer-supplier negotiation (Kraljic, power, price negotiation) (`04-procurement-buyer-supplier.md`)
  - AI/LLM Agent Negotiation Experiments: Evidence for an LLM Buyer Agent (`05-ai-negotiation-experiments.md`)
  - Replication status and robustness of classic negotiation/judgment findings (`06-replication-and-robustness.md`)
  - New Harvard-hosted negotiation sources (3 verified) (`07-new-sources-harvard.md`)
  - New negotiation sources: MIT, Stanford, Columbia/SMU (3 verified) (`08-new-sources-princeton-mit-etc.md`)
  - New open-access textbooks, surveys and chapters on negotiation (for an AI buyer agent) (`09-new-sources-open-textbooks.md`)

---

# Part A. Syntheses (start here)


<!-- source file: research/reports/negotiation-research-reading-list.md -->
## Anchor high, trade widely, never lie: negotiation evidence for our buyer agent

**Bottom line:** The human-negotiation evidence supports a short, stable playbook for our e-mail buyer agent: open with a specific, ambitious but defensible number; never reveal the walk-away price; send two or three equivalent multi-issue packages and read which one the supplier prefers; concede slowly, in shrinking steps and with reasons; stay polite and firm without threats; and never lie or invent figures. The strongest support comes from meta-analyses of first offers and anchoring and from a recent handbook chapter we read in full. Concession-pattern, emotion-tone and Kraljic-style rules are moderate or weak. The AI/LLM experiments are mostly 2025-26 preprints on older or single models and carry the lowest confidence, so we treat them last. **Read status is the main caveat.** Apart from five sources we read in full or in large part (the Princeton Handbook chapter, Herold et al. 2025, Heunis et al. 2025, Kelly and Chicksand 2024, four Harvard PON articles), almost every source in this report was seen only at abstract or search-snippet level. We state that per source and do not upgrade any claim beyond it. No source here tested an agent against Tacto's bots, so every rule is a hypothesis for our `backlog.csv` runs.

**Evidence-strength labels.** *Strong* means several independent sources agree, including a meta-analysis, a large replication or a handbook-level synthesis. *Moderate* means a few lab studies or one meta-analysis with high heterogeneity. *Weak* means a single study, a practitioner claim, a theory without direct test, or an unverified secondary report. Every label describes the human lab literature unless marked AI. None of them has been confirmed at full-text level except where the read-status column says so.

### Ranked reading list: what to read first, how much we have read, how to get it legally

Ranking reflects usefulness for a scored multi-issue buyer agent, not fame. "Read" values: **Full** (read to the end in our own notes), **Most/Body** (read the main text, not tables or references), **Abstract** (abstract, repository record or search snippet only), **Catalogue** (publisher or library record only), **Memory** (model background knowledge, not verified, so treated as a candidate and not as evidence).

| # | Source | Edition / venue | Why it matters | Read | Legal access |
|---|---|---|---|---|---|
| 1 | Schweitzer, Krueger, Boothby, Cooney (2025), "Negotiation", *Handbook of Social Psychology*, 6th ed., Situational Press, doi 10.70400/NUZE7621 | Handbook chapter, 92 pages | Best single synthesis of lab evidence by phase (prepare, communicate, close, after). No AI-agent section | **Full body**; reference list not read; primary studies not checked | Access route not recorded in our notes; check the DOI and the publisher before sharing copies |
| 2 | Herold, Heller, Rozemeijer, Mahr (2025), "Brave new procurement deals", *J. Purchasing & Supply Management* 31(4), 101012, doi 10.1016/j.pursup.2025.101012 | Peer-reviewed, 3 experiments | Closest to our setting: GPT buyer bot vs human suppliers, with students and professionals | **Full** (open access, CC BY) | [ScienceDirect open access](https://www.sciencedirect.com/science/article/pii/S1478409225000214); [Maastricht record](https://cris.maastrichtuniversity.nl/en/publications/brave-new-procurement-deals-an-experimental-study-of-how-generati/) |
| 3 | Petrowsky, Loschelder et al. (2025), first-offer meta-analysis, *OBHDP*, doi 10.1016/j.obhdp.2025.104448 (journal status per one note; a second note found only the 2023 IACM conference abstract) | Preregistered meta-analysis, about 90 studies, plus experiments N = 2,121 | Quantifies first-offer advantage and impasse cost | **Abstract** | Parallel open copy at [Leuphana PubData](https://pubdata.leuphana.de/entities/publication/29dc7e5d-01eb-420a-b73d-66e0be7cd440); [conference abstract](https://fis.leuphana.de/en/activities/a-threefold-meta-analysis-of-economic-first-offer-effects-in-nego/) |
| 4 | Kelly and Chicksand (2024), "A Critical Exploration of Bargaining in Purchasing and Supply Management", *Group Decision and Negotiation* 33(3), 617-646, doi 10.1007/s10726-024-09879-9 | Systematic review, 427 papers | Only PSM-specific bargaining review | **Most** (abstract to section 3.3 plus 4.2; not Table 4 or Fig. 4) | Springer via TUM eAccess; [accepted manuscript at Salford](https://salford-repository.worktribe.com/output/2470173/a-critical-exploration-of-bargaining-in-purchasing-and-supply-management-a-systematic-literature-review) (blocked when we fetched it); [Springer](https://link.springer.com/article/10.1007/s10726-024-09879-9) |
| 5 | Hüffmeier, Freund, Zerres, Backhaus, Hertel (2014), *J. Management* 40(3), 866-892, doi 10.1177/0149206311423788 | Meta-analysis, 34 studies | Hardline vs softline strategy in **distributive** negotiation (not about training) | **Abstract** | TUM (paywalled); [UvA DARE record](https://dare.uva.nl/id/801197e8-e374-4128-aeb3-c66c06cb8812) |
| 6 | Leonardelli, Gu, McRuer, Medvec, Galinsky (2019), *OBHDP* 152, 64-83 | 6 experiments | Multiple equivalent simultaneous offers (MESOs) | **Abstract** | TUM; [Macquarie record](https://researchers.mq.edu.au/en/publications/multiple-equivalent-simultaneous-offers-mesos-reduce-the-negotiat/) |
| 7 | Tey, Schaerer, Madan, Swaab (2021), *OBHDP* 165, 153-166, doi 10.1016/j.obhdp.2021.05.003 | 7 studies, N = 2,311 | Shrinking concession steps leak the limit | **Abstract** | TUM; [INSEAD record](https://www.insead.edu/faculty-research/publications/journal-articles/impact-concession-patterns-negotiations-when-and-why) |
| 8 | Orr and Guthrie (2006), *Ohio State J. on Dispute Resolution* 21, 597 | Meta-analysis of simulated negotiations | Anchoring in negotiation, with experience and information moderators | **Abstract** | Open: [Vanderbilt repository](https://ir.vanderbilt.edu/handle/1803/7415), [bepress](https://works.bepress.com/chris-guthrie/18) |
| 9 | Kong, Dirks, Ferrin (2014), *Acad. Management J.* 57(5), 1235-1255, doi 10.5465/amj.2012.0461 | Meta-analysis, 38 studies | Trust in negotiation | **Abstract** | TUM; [SMU record](https://ink.library.smu.edu.sg/lkcsb_research/3530) |
| 10 | Kang, Hong, Bartnik, Park, Ko (2018), *Management Decision*, doi 10.1108/MD-09-2016-0662 | Case plus experiment, 77 sourcing professionals | Only direct test of Kraljic quadrant to negotiation style | **Abstract** | TUM/Emerald; [Emerald](https://www.emeraldinsight.com/insight/content/doi/10.1108/MD-09-2016-0662/full/html) |
| 11 | Heunis et al. (2025), strategic adaptability training, *J. Purchasing & Supply Management* 31(2) | Teaching design, satisfaction data only | Cue-based switching between integrative and distributive moves | **Body** (sections 1-7; no references) | [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1478409224000773) |
| 12 | Gunia, Swaab, Sivanathan, Galinsky (2013), *PSPB* 39, 1547-1558 | Lab experiments | First-offer effect holds across culture, power and multiple issues | **Abstract** | TUM; [LBS record](https://www.london.edu/faculty-and-research/academic-research/t/the-remarkable-robustness-of-the-first-offer-effect-across-culture-power-and-issues) |
| 13 | Morris et al. (2002), "Schmooze or lose", *Group Dynamics* 6(1), 89-100 | 2 lab studies | E-mail negotiation and pre-contact | **Abstract** | TUM; [Stanford working paper](https://www.gsb.stanford.edu/faculty-research/working-papers/schmooze-or-lose-social-friction-lubrication-e-mail-negotiations) |
| 14 | Van Kleef and Côté (2022), *Annual Review of Psychology* 73, 629-658 | Narrative review (not a meta-analysis) | Anger and emotion in negotiation | **Abstract** | [Open PDF](https://annualreviews.org/doi/pdf/10.1146/annurev-psych-020821-010855) |
| 15 | Schweitzer, Hershey, Bradlow (2006), "Promises and lies", *OBHDP* 101(1), 1-19 | Lab | Trust repair after deception | **Abstract** | [Open PDF at Wharton](https://faculty.wharton.upenn.edu/wp-content/uploads/2014/06/Promises-and-Lies.pdf) |
| 16 | Fugger, Katok, Wambach (2019), "Trust in procurement interactions", *Management Science*, doi 10.1287/mnsc.2018.3196 | Experiments | Reverse auctions cut price but reduce cooperation | **Abstract** (author PDF abstract-level) | [Author PDF](https://personal.utdallas.edu/~ekatok/trust-procurement-interactions.pdf) |
| 17 | Raiffa, Richardson, Metcalfe, *Negotiation Analysis*, Harvard UP, 2002 | Book | Formal decision-analytic treatment, most relevant to a quantitative agent | **Memory**; edition not verified | Library loan or purchase; search the TUM catalogue first |
| 18 | Thompson, *The Mind and Heart of the Negotiator*, 7th ed., Pearson, 2020 (ISBN 9780135197998) | Research-based textbook | Evidence on integrative tactics, emotion, trust, virtual negotiation | **Catalogue** | [Pearson](https://www.pearson.com/store/p/the-mind-and-heart-of-the-negotiator/P100002680893/9780135197998); eTextbook is DRM-locked rental; otherwise loan or buy |
| 19 | Lewicki, Barry, Saunders, *Negotiation*, 8th ed., McGraw-Hill, 2020 (ISBN 9781260565591) | Standard syllabus textbook | Broad coverage | **Catalogue** | [MIT Press Bookstore listing](https://mitpressbookstore.mit.edu/book/9781260479157); loan or buy |
| 20 | Malhotra and Bazerman, *Negotiation Genius*, Bantam, 2007 | Research-informed trade book | Bias-focused; their HBR 2007 "Investigative Negotiation" page failed to load | **Catalogue/summary only** | Loan or buy |
| 21 | van Weele and Rozemeijer, *Procurement and Supply Chain Management*, 8th ed., Cengage, 2022 (ISBN 9781473779112) | Procurement textbook | Business context for term-sheet issues; weaker on negotiation evidence | **Catalogue** | [Cengage UK](https://www.cengage.uk/c/procurement-and-supply-chain-management-8e-van-weele-rozemeijer/9781473779112); loan or buy |
| 22 | Handfield, Giunipero, Monczka, Patterson, *Purchasing and Supply Chain Management*, 8th ed., Cengage (copyright 2026; dates vary by site) | Procurement textbook | AI-in-procurement chapter | **Catalogue** | [Cengage](https://cengage.com/c/purchasing-and-supply-chain-management-8e-handfield-giunipero-monczka-patterson/9798214042039) |
| 23 | Olekalns and Adair (eds.), *Handbook of Research on Negotiation*, Edward Elgar, 2013 | Research handbook | Cognition, emotion, communication, complex negotiation | **Catalogue** | [Elgar](https://www.e-elgar.com/shop/handbook-of-research-on-negotiation) (eBook for purchase); loan |
| 24 | Fisher, Ury, Patton, *Getting to Yes*, 3rd ed., Penguin, 2011 (ISBN 9780143118756) | Practitioner framework | BATNA, interests, objective criteria; a revised anniversary edition was announced, release unconfirmed | **Four Harvard PON write-ups read in full, not the book** | [PON pieces, free](https://www.pon.harvard.edu/daily/batna/translate-your-batna-to-the-current-deal/); book via loan or purchase |
| 25 | Kraljic (1983), "Purchasing must become supply management", *Harvard Business Review* 61(5), 109-117 | Article | Origin of the matrix | **Not read** (about 70-word teaser only) | [HBR, paid](https://hbr.org/1983/09/purchasing-must-become-supply-management); library copy via TUM if licensed; do not use circulating unverified PDFs |
| 26 | Voss and Raz, *Never Split the Difference*, Harper Business, 2016 | Practitioner opinion | Reviews found no academic test of the packaged tactics | **Memory plus blog reviews** | Loan or buy; low priority |

**How to get these without piracy.** The TUM library catalogue is at search.ub.tum.de, access is by TUM ID through eAccess, and the licence forbids systematic downloading ([UB TUM](https://www.ub.tum.de/en/node/5558)). The same page lists about 300,000 e-books and an older news item mentions about 70,000 Springer titles, so Springer items (Kelly and Chicksand) are the likeliest to be free through TUM; Wiley, Sage, Taylor & Francis and, since January 2024, Oxford journals are licensed as e-journals. The notes did not check holdings for any individual title, so run the catalogue search before buying. Most textbooks come from Pearson, Cengage, McGraw-Hill and Penguin and will need loan or purchase. Open copies exist for Herold, Petrowsky (parallel publication), Orr and Guthrie, Van Kleef and Côté, Schweitzer et al. 2006, Fugger et al., Kopelman et al. 2006 ([Michigan Deep Blue](https://deepblue.lib.umich.edu/bitstream/handle/2027.42/49354/1064-Kopelman.pdf;sequence=1)), Curhan et al. 2006 ([MIT DSpace](https://dspace.mit.edu/handle/1721.1/18234)) and Huang et al. 2017 ([Harvard DASH](https://dash.harvard.edu/entities/publication/73120379-2eb6-6bd4-e053-0100007fdf3b)). A "Cambridge Handbook of Negotiation" named in the original brief was not found and probably is a mix-up with the Elgar handbook.

### Testable rules for the agent: rule, strength, source, how to test it

Test protocol for every row: change one thing per version, run the same case set (the beatable practice cases P05, P10, P11, P18, plus solved case P01 as control, plus simulator S01-S03), and log one row per run in `backlog.csv` with the version name, `deal`, `c_open`, `c_deal`, `c_best`, `score`, `replay` and a note naming the changed rule. The existing log shows the naive kit baseline already scores 0.51-0.68 on S01-S03, so the comparison unit is score against that baseline on the same case. Because the simulator is deterministic (S01 gave identical results twice), a single run per case suffices there; repeat practice-arena runs because the real bots may vary.

| # | Rule | Strength | Source | How to test in `backlog.csv` |
|---|---|---|---|---|
| 1 | Open with a specific, ambitious but defensible number on the price-like issue, backed by a real data ID | Strong for anchoring; moderate for "go first" | [Orr and Guthrie 2006](https://ir.vanderbilt.edu/handle/1803/7415); [Petrowsky et al.](https://pubdata.leuphana.de/entities/publication/29dc7e5d-01eb-420a-b73d-66e0be7cd440); Princeton chapter | Vary opening depth (for example 5 percent vs 10 percent vs 15 percent under `c_open`) on the same cases; compare score and the no-deal rate. Expect an impasse penalty at the extreme |
| 2 | Never disclose the walk-away price, budget or urgency; enforce this in code | Strong as a principle | Princeton chapter; AI leak rates in [SovereignNegotiation-Bench](https://arxiv.org/abs/2607.02814) (abstract only) | Add an outbound check that blocks messages containing the limit; count blocked messages and compare scores before and after |
| 3 | Store the walk-away limit and per-round concession cap in code, not in the prompt | Moderate | Princeton chapter (people drift past limits when aroused, as reported); [Xia et al.](https://arxiv.org/abs/2402.15813) (AI, old models) | v4: code caps on and off; count accepts worse than `c_best` and late caves |
| 4 | Send 2-3 equivalent packages (price vs payment days vs volume vs contract length) per message | Moderate | [Leonardelli et al. 2019](https://researchers.mq.edu.au/en/publications/multiple-equivalent-simultaneous-offers-mesos-reduce-the-negotiat/); Princeton chapter | v2: one package vs three; also log which package the supplier picks to confirm it reveals priorities |
| 5 | Add issues and trade across them; ask for the supplier's priorities before settling; verify claimed priorities | Strong in principle; effect size unknown | [Thompson 1991](https://www.kellogg.northwestern.edu/academics-research/research/detail/1991/information-exchange-in-negotiation); [De Dreu, Weingart, Kwon 2000](https://dare.uva.nl/id/403ebedc-c455-47a0-8a00-803afaed87b3); Princeton chapter | Price-only vs price-plus-terms strategy on the cash-short and strategic cases; compare `c_deal` on total cost |
| 6 | Ask direct questions, using a presumed-problem form | Moderate (Minson 2018 reported only via the chapter) | Princeton chapter | Add one question per early turn; compare the number of supplier-revealed constraints and the score |
| 7 | Concede in shrinking steps, low-priority issues first, each with a reason; expect reciprocity | Weak to moderate | [Tey et al. 2021](https://www.insead.edu/faculty-research/publications/journal-articles/impact-concession-patterns-negotiations-when-and-why); [Hüffmeier et al. 2014](https://dare.uva.nl/id/801197e8-e374-4128-aeb3-c66c06cb8812) | Three schedules: constant, linear, shrinking. Expect shrinking steps to leak the limit to a bot that models them; compare final price and rounds to close |
| 8 | Firm on numbers, polite in tone, no threats and no anger | Moderate | [Herold et al. 2025](https://www.sciencedirect.com/science/article/pii/S1478409225000214); [Kong et al. 2014](https://ink.library.smu.edu.sg/lkcsb_research/3530) | v3: threat-free firm vs threat-laden firm vs warm-only; count `final_offer` and `walked_away` statuses as well as score |
| 9 | Never lie, palter or invent figures; deflect with a question instead of refusing to answer | Strong | [Boles, Croson, Murnighan 2000](https://ideas.repec.org/a/eee/jobhdp/v83y2000i2p235-259.html); [Schweitzer et al. 2006](https://faculty.wharton.upenn.edu/wp-content/uploads/2014/06/Promises-and-Lies.pdf); Princeton chapter | Not worth an A/B test; log any `contradicted` claim flagged by the arena as a defect |
| 10 | Do not thank for each concession before price is settled; thank at close | Weak (abstract-level, authors unverified) | [Yip et al. working summary](https://hbswk.hbs.edu/item/thanks-for-nothing-expressing-gratitude-invites-exploitation-by-competitors?cid=wk-rss); Princeton chapter | Template with and without per-turn thanks; compare price movement per turn |
| 11 | Open with one short relational or process line before numbers | Moderate for humans; untested for bots | [Morris et al. 2002](https://www.gsb.stanford.edu/faculty-research/working-papers/schmooze-or-lose-social-friction-lubrication-e-mail-negotiations); Princeton chapter | Opening line on or off; compare supplier cooperation signals and score. Treat a null result as likely for scripted suppliers |
| 12 | Keep the best alternative in reserve; cite competing quotes only if real; in RFQ cases keep 2-3 threads alive | Strong as principle | Princeton chapter; [PON](https://www.pon.harvard.edu/daily/batna/translate-your-batna-to-the-current-deal/) | RFQ cases S02 and P-series: parallel threads vs sequential; score difference |
| 13 | Map goal to style: leverage competitive, secure_supply accommodative, stabilise and strategic collaborative with firm anchors | Weak to moderate | [Kang et al. 2018](https://www.emeraldinsight.com/insight/content/doi/10.1108/MD-09-2016-0662/full/html); contested by [Hesping and Schiele 2016](https://research.utwente.nl/en/publications/matching-tactical-sourcing-levers-with-the-kralji%C4%8D-matrix-empiric/) | Run each goal type under one global style vs the mapped style; tag cases by goal in `notes` |
| 14 | Switch between integrative and distributive moves on cues (deadlock, supplier softening, new issue, `final_offer`) | Weak | Heunis et al. 2025 (teaching design, satisfaction only); Kelly and Chicksand 2024 (descriptive) | v5: fixed-phase script vs cue-switching; score and rounds on RFQ and capacity cases |
| 15 | Before accepting, re-check final terms against the thread and the quote PDF; treat instant acceptance as a sign we opened soft | Weak | Princeton chapter | Audit log: count accepts with unstated-terms surprises; compare opening depth when the supplier accepted immediately |
| 16 | Mirror the supplier's register early, but do not over-match | Weak | [Ireland and Henderson 2014](https://scholars.ttu.edu/en/publications/language-style-matching-engagement-and-impasse-in-negotiations-5) (more matching went with more impasse in 64 IM dyads); [Maddux et al. 2008](https://www.ssoar.info/ssoar/bitstream/document/21568/1/ssoar-jexpsocpsychol-2008-2-maddux_et_al-chameleons_bake_bigger_pies_and.pdf) (behavioural mimicry, not verbal repetition) | Low priority; skip unless time remains |
| 17 | AI-specific (lower confidence): compute total cost and arithmetic in code; send offers as structured term sheets; block prompt-injection text from supplier messages | Weak to moderate, AI preprints | [PieArena](https://arxiv.org/abs/2602.05302); [Vaccaro et al.](https://arxiv.org/abs/2503.06416) | Already partly in the kit (`total_cost`, `guard()`); log any injected-instruction event |

Rules 1, 2, 5, 9 and 12 are the ones to build first; rules 7, 13, 14 and 16 are the ones most likely to waste time.

### What replicates, what is contested, and what is untested

**Anchoring and first offers are the best-supported finding, with a cost.** Many Labs 1 reportedly replicated classic anchoring, but our note rests on secondary summaries and a commentator who warns the original effect-size metric is not comparable ([Gelman](https://statmodeling.stat.columbia.edu/2014/02/27/can-learn-many-labs-replication-project/)). The negotiation-specific evidence is two meta-analyses: Orr and Guthrie 2006 found anchors significantly affect outcomes in simulated negotiations ([Vanderbilt](https://ir.vanderbilt.edu/handle/1803/7415)), and the Petrowsky et al. preregistered meta-analysis reports a first-mover advantage of **g about 0.49**, a first-offer magnitude effect of **g about 1.30** and an offer-outcome correlation of **r about 0.53**, with high heterogeneity and a rising impasse risk for ambitious offers ([Leuphana](https://fis.leuphana.de/en/activities/a-threefold-meta-analysis-of-economic-first-offer-effects-in-nego/)). Those numbers come from the conference abstract; one note linked a journal DOI and the other found none, so do not quote them as final. The same work finds effects shrink as issues multiply, and Gunia et al. found the first-offer effect operates through the distributive issues ([LBS](https://www.london.edu/faculty-and-research/academic-research/t/the-remarkable-robustness-of-the-first-offer-effect-across-culture-power-and-issues)). The underlying psychological account (selective accessibility) has a failed replication of a key result ([Harris et al. 2019, UCL preprint](https://discovery-pp.ucl.ac.uk/id/eprint/10074759/1/HarrisEtAl_2019_anchoring.pdf)), so the effect is solid while the mechanism is contested. Extreme offers still anchor but offend recipients and raise walk-away risk, mainly among low-power recipients ([Schweinsberg et al. 2012](https://www.london.edu/faculty-and-research/academic-research/s/starting-high-and-ending-with-nothing-the-role-of-anchors-and-power-in-negotiations)).

**Hard versus soft bargaining trades money against relationship, and our AI-versus-human result agrees.** Hüffmeier et al. 2014 is a meta-analysis of 34 studies of distributive negotiation (not of training, which one note wrongly claimed): hardline strategies gave better economic outcomes and softline better socioemotional ones, with softliners doing best when they reciprocated concessions accurately ([UvA](https://dare.uva.nl/id/801197e8-e374-4128-aeb3-c66c06cb8812)). Herold et al. 2025 shows the same split with a chatbot buyer: the competitive prompt won larger discounts in all three studies, near 10 percent with students but only about 1-5.5 percent with professional negotiators, while the collaborative prompt earned more supplier trust, satisfaction and willingness to deal again ([Herold et al., read in full](https://www.sciencedirect.com/science/article/pii/S1478409225000214)). The authors flag that the competitive prompts included threats, so "competitive" is confounded with threats, and that the model tended to concede under pushback. We should assume Tacto's bots resemble the professionals, not the students.

**Emotion is the most context-dependent area.** Anger drew bigger concessions than happiness in Van Kleef, De Dreu and Manstead 2004 and in a Dutch direct replication ([Pollmann 2017](https://research.tilburguniversity.edu/en/publications/boosheid-en-blijdschap-in-onderhandelingen-een-replicatie-van-van/)), but a Many Labs 5 replication of a related design found an effect about one ninth of the original ([Skorb et al. 2020](https://www.psychologicalscience.org/journals/ampps/2515245920927643/)), and the effect depends on power, intensity, sincerity and the expresser. Anger also invited covert retaliation ([Wang, Northcraft, Van Kleef 2012](https://researchportalplus.anu.edu.au/en/publications/beyond-negotiated-outcomes-the-hidden-costs-of-anger-expression-i/)). The review by Van Kleef and Côté is narrative, and the notes found no meta-analysis of anger in negotiation. Gratitude inviting tougher counteroffers rests on one summarised paper with unverified authorship. We therefore label emotion-as-tactic moderate to weak and keep the "no threats, polite" rule on the safer side.

**Mostly untested or thin.** Power priming and power poses failed to replicate in the notes' secondary sources, though the notes did not find a replication-grade test of BATNA as structural power either. Gender effects are small and moderated (Mazei et al. 2015, 123 effect sizes, about d 0.20 per a secondary report), culture effects rest on single studies, and the popular Voss tactics (mirroring, labelling, calibrated questions) have no controlled test we found. Fixed-pie bias is well documented but varies in size, and the training literature is sparse. Most effect sizes come from student role-plays; one note suggests trained students rarely differ from professionals, but its source page returned 403, so it is unconfirmed, and Herold's own professional-versus-student gap argues the opposite for price effects.

### Procurement evidence is thinner than the bargaining evidence

Kelly and Chicksand 2024 reviewed 427 papers and found that practitioners mix distributive and integrative moves, a firm stance is often needed at the end, informed buyers pay less, bargaining power comes from spend volume, bundling and alternatives, and fewer than 13 percent of papers use a theory ([Springer](https://link.springer.com/article/10.1007/s10726-024-09879-9)). The Kraljic matrix is a heuristic more than a law. Kang et al. 2018 found with 77 sourcing professionals that effective buyers chose competitive, collaborative or accommodative styles by quadrant ([Emerald](https://www.emeraldinsight.com/insight/content/doi/10.1108/MD-09-2016-0662/full/html)), yet a survey of 107 sourcing projects found the full range of levers used in all four quadrants ([Hesping and Schiele](https://research.utwente.nl/en/publications/matching-tactical-sourcing-levers-with-the-kralji%C4%8D-matrix-empiric/)), and an interview study found hard bargaining present even in strategic relationships ([Lambrechts et al., IPSERA](https://research.ou.nl/en/publications/how-do-buyers-actually-negotiate-with-their-leverage-and-strategi/)). Power research says coercive and mediated power lowers relationship quality ([Leonidou et al. meta-analysis of 120 studies, abstract](https://www.springerprofessional.de/a-meta-analysis-of-power-in-buyer-seller-relationships-an-abstra/16589268)), and reverse auctions cut price while eroding cooperation ([Fugger et al. 2019](https://personal.utdallas.edu/~ekatok/trust-procurement-interactions.pdf)). The Princeton chapter adds that relationships matter economically mostly where value is created after signing (services), much less for plain goods purchases, which matters because Tacto bots remember only within a case. Payment-term and index-clause material came only from vendor blogs and is low quality; no peer-reviewed source was found for should-cost, dual sourcing or supplier development.

### AI and LLM negotiation experiments (lower confidence, read last)

Treat this section as hypotheses. Most items are arXiv preprints, many from 2026, unreplicated, tied to specific models, and several were read only at abstract level; the notes record that some 2026 identifiers were returned by a paper index and not independently confirmed outside it. Findings on 2023-24 models (GPT-4, Llama-2) probably do not describe 2026 frontier models.

The pattern most relevant to us is that accommodating buyers lose. In 15,000 negotiations among five frontier models, the buyer with the highest concession rate and fewest rounds had the worst buyer surplus share (24.3 percent) and deal rate (86.4 percent), while winners anchored aggressively and stayed patient ([Li, Bergemann et al.](https://arxiv.org/abs/2604.16472), partial read). LLMs anchor and split the difference: final prices correlated 0.716 with the initial proposal in one GPT-4 game ([Bianchi et al., NegotiationArena](https://arxiv.org/abs/2402.05863), partial read), and buyers were weaker than sellers across 14 models, with a deterministic offer generator (LLM writes only the wording) lifting the buyer deal rate from 26.67 percent to 88.88 percent on 2023-era models against an LLM seller ([Xia et al.](https://arxiv.org/abs/2402.15813), partial read). Scaffolding helped mid-tier models but not the top ones, and arithmetic accuracy jumped by model generation (GPT-4.1 5.4 percent against GPT-5.2 100 percent) ([PieArena](https://arxiv.org/abs/2602.05302), partial read). The only large warmth result is AI-to-AI: warm prompts did better across 180,000+ negotiations, dominance claimed more value in closed deals, and long conversations went with impasse ([Vaccaro et al., PNAS](https://arxiv.org/abs/2503.06416), partial read; one model, GPT-4o-mini). That conflicts in emphasis with Herold's human-supplier result, which is why the human-evidence rule 8 stays "firm numbers, polite tone". Human-AI studies are thin: fairness and trust dropped when an AI partner was disclosed (N = 3,552, [preprint abstract](https://arxiv.org/abs/2401.12773)), and prompt injection that works on AI counterparts does not work on humans, so the threat depends on whether the Tacto supplier is an LLM or a script, which we do not know. One preprint claims negotiation ability does not improve with better models, while PieArena shows large generational gains; the notes attribute this to different metrics and leave it unresolved. The supportive design implication is modest: let the LLM write and let code decide limits, arithmetic and concession schedule, as in the Cicero precedent that the notes describe from memory only.

### What we still have not read in full

Everything else was read at abstract or snippet level at best, and these items need a full read before any number is hard-coded:

1. **Never read at all, or only a teaser:** Kraljic 1983 (HBR); Malhotra and Bazerman 2007 "Investigative Negotiation"; all books (we hold only PON write-ups of *Getting to Yes*, plus catalogue records for Thompson, Lewicki, Raiffa, van Weele and Rozemeijer, Handfield et al., Olekalns and Adair).
2. **Read in part:** Kelly and Chicksand 2024 (not Table 4, Fig. 4 or a separate conclusion); Heunis et al. 2025 (no references; satisfaction data only, so it is not outcome evidence); the Princeton chapter's reference list and every primary study it cites (Minson 2018, Tey 2021, Ames and Mason 2015, Schaerer 2015-16, Tasa 2013, Bitterly and Schweitzer 2020, Rogers 2017) are "as reported in the chapter".
3. **Abstract only, with effect sizes unretrieved:** Petrowsky et al. (final journal version, k and impasse numbers); Orr and Guthrie (the r = .497 figure is secondary); Hüffmeier 2014; Galinsky and Mussweiler 2001; Gunia et al. 2013; Schweinsberg et al. 2012; Loschelder et al. 2017 (precise anchors); Leonardelli et al. 2019; Tey et al. 2021; Magee et al. 2007; Kim and Fragale 2005; Kong et al. 2014; De Dreu et al. 2000; Thompson 1991; Mazei et al. 2015; Many Labs 1 and 2 (the anchoring rows were not confirmed); Van Kleef et al. 2004, Overbeck et al. 2010, Wang et al. 2012; Brooks and Schweitzer 2011; Kopelman et al. 2006; Morris et al. 2002; Naquin and Paulson 2003; Curhan et al. 2006; Kang et al. 2018; Hesping and Schiele 2016; Cox et al. 2004; Leonidou et al.; Fugger et al. 2019.
4. **Seen only via titles or secondary summaries:** Schaerer et al. "no BATNA beats weak BATNA" (unverified); Adam and Brett 2015 and 2018 (titles only); the gratitude study (authors unverified); the MIT slide claim that schmoozing dyads were about four times likelier to reach agreement; the "How valid is negotiation research based on student samples" paper; Gelderman and Van Weele, Caniëls and Gelderman (citations only); Kern et al. 2020 on fixed-pie perceptions; Movius 2008 and the training meta-analyses.
5. **AI section:** only Vaccaro, Xia, Bianchi, PieArena and Li et al. were read in passages; Fu, Davidson and about a dozen 2025-26 preprints are abstract-only; Cicero and Abdelnabi et al. are memory only; legal points on AI disclosure (EU AI Act, California BOT Act) were not verified.
6. **Corrections to earlier notes:** one research note said it could not find a Herold 2025 student-versus-professional comparison or Heunis 2025. Both exist and were read by us (Herold: 385 and 216 students, 163 professional negotiators; Heunis: JPSM 31(2)). The same note's claim that Hüffmeier 2014 concerns training is wrong: it is a distributive-strategy meta-analysis. A "Gino"-authored honesty finding should be checked for data-integrity concerns before use, as the notes themselves flag from memory.

### Conclusion

The research does not support a clever tactic; it supports discipline. The best-evidenced moves (ambitious specific anchor, hidden limit, multiple packages, honesty) are cheap, and the failure modes in both human and LLM studies are the reverse: conceding early, leaking the limit, and drifting past it under pressure. That argues for making the agent's limits and arithmetic structurally unbreakable in code, then spending experiment time on the open questions: how deep the opening can go before Tacto's bots walk, whether shrinking concession steps leak the limit to a bot, and whether a Kraljic-style goal mapping beats a single firm-but-polite style.

The sharper insight is that the literature's tidy "competitive wins price, collaborative wins trust" split has a confound that matters to us. Herold's competitive prompts bundled threats with firmness, professionals gave far smaller discounts than students, and Tacto scores total cost within one case, so the trust benefit may earn nothing there, while threats may cost real money, as the earlier P01 replay in `RESOURCES.md` suggests. Our `backlog.csv` can separate firmness from threat in one version, which no published study has done for a buyer bot against professionals.


<!-- source file: research/reports/key-insights-nine-new-sources.md -->
## Key insights from nine new sources (input for building negotiation strategies)

Facts distilled from the second research round, in our own words. Each fact is tagged with its source (S1-S9), an evidence strength (strong / moderate / weak, our judgement) and the **knob** it gives us, meaning a parameter that different strategies can set differently. Full notes per source: `research/notes/` (`07-new-sources-harvard.md`, `08-new-sources-princeton-mit-etc.md`, `09-new-sources-open-textbooks.md`). Companion report: negotiation-research-reading-list.md.

**Caveats first.** Several sources are lab studies with people, simulations or toy games on 2023-era models, and none tested an agent against Tacto's bots. Every item is a hypothesis for `backlog.csv` runs. The agents read S1, S2, S3, S4 (IEEE version), S5 (pp. 1-8) and S8 in full or nearly; S6 about half; S7 and S9 partly.

### 1. The nine sources

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

### 2. Important facts, grouped by lever

#### A. Alternatives and the walk-away line
- A BATNA is a *course of action turned into a reservation value*, and it can itself be another deal, not only a last resort. Re-estimate it every time new information arrives. [S1, moderate] Knob: how often we recompute the reservation total cost.
- Bringing competing suppliers in **early** is worth more than late bargaining skill. [S1, moderate] Knob: RFQ-style parallel threads from round 1.
- Separate three kinds of "no": a tactical no (a move), a re-set no (reopens terms) and a final no (walk away). [S1, moderate] Knob: when to treat a supplier's `final_offer` as real.

#### B. Opening offer
- Early anchors shape the outcome, and negotiators anchor on whatever number comes first. [S3, moderate; S5 for LLMs, moderate]
- **Precision matters:** more precise first offers anchored amateurs more, in a straight line. Experts penalised very precise prices as a sign of incompetence (an inverted U). A plausible reason attached to the number removed the backfire. [S6, moderate to strong, lab-based] Knob: round vs precise opening numbers, with or without a stated rationale.
- A buyer's first offer *amplifies* the small buyer advantage. [S8, moderate]
- Anxiety lowers first offers, so open ambitious and complete. [S2, moderate]

#### C. Concessions and closing
- In multi-issue contracts with interdependent terms (price, payment days, contract length), conceding slowly reached only about 94% of the best outcome in simulation. Agents that sometimes accept a **slightly worse bundle** reached 98-99%. [S4, moderate, simulation] Knob: willingness to accept slightly worse bundles to end the search.
- An unconditional conceder gets exploited by a tough opponent, so keep concessions **reciprocal**. The "concede early and often" advice came from a cooperative, mediated setting. [S4, moderate] Knob: reciprocity rule before each concession.
- People discount concessions from the other side (reactive devaluation), so label your own concessions as costly and explain the reason. [S3, moderate]
- LLM agents split the difference by reflex even when it is irrational. [S5, moderate for LLMs, 2023 models] Knob: forbid auto-midpoint; compute the step from total cost.
- Anxious negotiators exit early and earn less (7.19 against 8.04 in a three-issue chat). [S2, moderate] Knob: minimum number of rounds before accepting or walking.

#### D. Issues, packages and information
- Negotiators assume a fixed pie. Add issues and trade across them. [S3, moderate]
- Slow, single-term concessions miss value that cross-term packages find. [S4, moderate] Knob: price-only vs multi-issue packages; number of packages (see the companion report for 2-3 equivalent packages).
- Opponent modelling (learning the other side's deadline, issue preferences, bidding and acceptance behaviour) is a well-developed field. Methods for the reservation value and deadline exist **only for single-issue negotiation**. [S7, moderate] Knob: lightweight model of the supplier's preference weights from which package it picks.
- Datasets and metrics for negotiation dialogue split into integrative and distributive. Little procurement coverage. [S9, weak for our use] Knob: evaluation split into value created vs value claimed.

#### E. Power, role and context
- The "buyer advantage" in sales negotiation is **small**, nearly vanishes in B2B and for experienced negotiators; power and information matter most; the number of issues did not matter. All lab data. [S8, moderate] Knob: do not rely on being "the buyer"; invest in information and alternatives instead.
- Ambiguous behaviour is read as hostile, and written negotiation had more impasses in earlier work. [S3, weak to moderate] Knob: neutral, explicit e-mail wording; state intent clearly.
- Fairness judgements are self-serving on both sides, so do not expect the other side to be fair by default. [S3, moderate]

#### F. Tone and pace
- Anxiety lowers expectations and speeds replies. High self-efficacy removed the early-exit effect. [S2, moderate; human emotion, may not transfer to a bot] Knob: fixed aspiration set before the talk; deliberate reply pacing within the 60-second limit.
- Prompts that make an LLM "desperate" or "cunning" shift outcomes. [S5, moderate for LLMs] Knob: persona and tone of the system prompt, tested as a variable.

#### G. The supplier may be an LLM
- Supplier bots are probably LLM-based, so S5's findings (anchoring, reflexive split-the-difference, prompt-driven shifts) apply to *them* as well as to our agent. [S5, moderate, inference] Knob: exploit predictable biases ethically (well-grounded anchors, packages) and never rely on tricks that need deception.

### 3. Knobs available for strategies (summary)

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

### 4. Gaps this list cannot fill

- No source here tests e-mail negotiation against supplier bots, so all strengths describe human labs, simulations or toy LLM games.
- S6 and S7 were read only partly; S9 has little procurement content.
- No verified Harvard source on supplier or e-mail negotiation specifically; no usable Princeton, Wharton or MIT OpenCourseWare full text was found.

### 5. Next step

Combine these knobs with the first report's 17 testable rules into 3-5 named **strategy variants** (for example "anchor-and-package", "competitive-alternatives", "reciprocal-collaborative"), implement each as a version in our agent, and log every run in `backlog.csv`.


---

# Part B. Full-text reading notes (sources we read in full or mostly)


<!-- source file: raw-files/01-pon-getting-to-yes.md -->
## Harvard Program on Negotiation: 4 articles (read in full, 330-900 words each)

Links: [BATNA](https://www.pon.harvard.edu/daily/batna/translate-your-batna-to-the-current-deal/) · [Six guidelines](https://www.pon.harvard.edu/daily/negotiation-skills-daily/six-guidelines-for-getting-to-yes/) · [Principled negotiation](https://www.pon.harvard.edu/daily/negotiation-skills-daily/principled-negotiation-focus-interests-create-value/) · [Sources of power](https://www.pon.harvard.edu/daily/batna/negotiation-skills-three-sources-of-power-at-the-bargaining-table/)

Popular write-ups of *Getting to Yes* (Fisher, Ury, Patton), not the book.

- BATNA = what you do if no deal happens. It sets your leverage and your walk-away point. People fixate on the offer in front of them and forget alternatives.
- Compare like for like: translate both options into comparable terms. One cited example: an insurance quote that looked 30% cheaper was worse once the fine print was compared.
- Update the BATNA as information arrives; use realistic, not hypothetical, alternatives.
- Positions are surface demands; interests are the needs behind them. Ask why, and share your own interests so trades appear.
- Separate people from the problem: listen, name emotions calmly, show appreciation without agreeing, phrase things in your own voice, avoid blame.
- Do not mirror hard tactics; answer with questions, interests, mutual-gain options and objective standards.
- Invent options before committing: contingencies, timing, conditions, performance incentives. Agree on neutral standards (market value, benchmarks).
- The goal is a deal better than the BATNA, not any deal.
- Power has three sources: strong BATNA, role/position, psychological confidence (Galinsky and Magee research as summarised by PON). Against a powerful counterpart, raise yours on all three.


<!-- source file: raw-files/02-herold-2025-ai-buyer.md -->
## Herold, Heller, Rozemeijer, Mahr (2025): "Brave new procurement deals"

Journal of Purchasing and Supply Management 31(4). [Link](https://www.sciencedirect.com/science/article/pii/S1478409225000214), open access (CC BY). Read in full (~9,000 words).

- Design: three experiments, 2x2 (collaborative vs competitive buyer bot x non-critical vs bottleneck item). A human played the supplier against a GPT-3.5 buyer bot told to get 10% off and 10-day payment. Chats up to 15 minutes.
- Samples: 385 and 216 students, 163 professional negotiators (agreements: 279, 168, 99).
- Competitive bot got a bigger discount in all three studies: near 10% with students, only about 1-5.5% with professionals. Faster deals with students; better payment terms with professionals.
- Collaborative bot: more supplier trust, satisfaction and wish to deal again, in all three studies.
- Item type made no difference to the effect.
- Competitive prompts made suppliers copy the bot's harsh language. Professionals pushed back with arguments such as inflation; students gave in more easily.
- The authors note the LLM tended to concede when challenged.
- Caveats: short single-shot chats, no ongoing relationship, Western student sample. The competitive prompts included threats ("competitors are cheaper, we will switch"), so "competitive" is confounded with threats.


<!-- source file: raw-files/03-kelly-chicksand-2024-bargaining-review.md -->
## Kelly and Chicksand (2024): bargaining in purchasing and supply management (systematic review)

Group Decision and Negotiation 33(3), pp. 617-646. [Link](https://link.springer.com/article/10.1007/s10726-024-09879-9). Read most (abstract to section 3.3, plus 4.2); not Table 4, Fig. 4 or a separate conclusion.

- 427 papers reviewed (from 2,796 hits across five databases).
- "Bargaining" means three things: adversarial haggling, back-and-forth over narrow issues (often price), and a stage of the process.
- Practitioners mix distributive and integrative moves. A firm stance is often needed at the end; avoiding conflict there tends to leave value on the table.
- Informed buyers pay less: knowing the realistic discount range early gives leverage.
- Bargaining power comes from spend volume, bundling and alternative suppliers; effects of firm size are contradictory.
- Supplier trust in the buyer and visible buyer effort affect outcomes.
- Timing, who makes the first offer, and the order of approaching suppliers matter.
- Outcomes go beyond price: time cost and the long-term relationship count.
- Fewer than 13% of the papers use a theory; most are mathematical models, which capture social behaviour poorly.


<!-- source file: raw-files/04-heunis-2025-strategic-adaptability.md -->
## Heunis et al. (2025): strategic adaptability negotiation training in purchasing

Journal of Purchasing and Supply Management 31(2). [Link](https://www.sciencedirect.com/science/article/pii/S1478409224000773). Read the body (sections 1-7), not the references (~7,500 words).

- A teaching design, not an outcome experiment. Only evidence: student satisfaction (93 undergraduates 7.34/10; 34 extracurricular students 8.03/10).
- Strategic adaptability = switching between integrative and distributive tactics when cues appear: content (issue or priority changes), opponent (behaviour changes or resistance), process (deadlock), context (external change).
- Integrative moves: ask about interests across all issues, paraphrase, make multi-issue package offers, use relationship statements.
- Distributive moves: one issue at a time, single-issue offers, justify a position, ultimatums or deadline pressure.
- Fixed phases ("collaborate first, then compete") do not match real behaviour; negotiators switch often.
- Beginners miss cues and keep haggling when it is counterproductive.
- Distributive tactics are tolerated in low-interdependence relationships but hurt knowledge sharing in close ones. Deception and opportunism spill over and reduce information sharing.
- Worked examples with debriefs teach better than principles alone.


<!-- source file: raw-files/05-not-read.md -->
## Sources we could not read (honest gaps)

- **Kraljic (1983), "Purchasing Must Become Supply Management", HBR.** [Link](https://hbr.org/1983/09/purchasing-must-become-supply-management). Paywalled; only a ~70-word teaser was visible (purchasing is stuck in routine while supply conditions shift; calls for strategic supply management). The matrix itself was not in what we read.
- **Malhotra and Bazerman, "Investigative Negotiation", HBR 2007.** [Link](https://www.hbs.edu/faculty/Pages/item.aspx?num=23670). The page failed to load; only a snippet (every piece of information helps you understand the other side's constraints).
- **Princeton chapter "Negotiation".** Now read: see 06-princeton-handbook-negotiation-chapter.md.
- Books (*Getting to Yes*, *Never Split the Difference*, *Negotiation Genius*): not stored. Borrow or buy a copy and add your own notes.


<!-- source file: raw-files/06-princeton-handbook-negotiation-chapter.md -->
## Notes: "Negotiation" chapter, Handbook of Social Psychology (6th ed.)

**Source:** Schweitzer, Krueger, Boothby and Cooney (2025). Negotiation. In Gilbert, Fiske, Finkel and Mendes (Eds.), The Handbook of Social Psychology, 6th ed. Situational Press. doi 10.70400/NUZE7621

**Read status:** All 92 pages read, but NOT with the PDF page renderer (it failed: poppler missing). I extracted the full text with macOS PDFKit and read the body to its end (conclusion, author note); the reference list was not read. No primary studies were checked: every claim below is "as reported in the chapter". The chapter has no dedicated AI-negotiation section, only a short technology section.

### Overview
- Four phases: setting the stage, communicating, closing, post-negotiation. Most research covers communicating (first offers especially); the other three are thinly studied, and the evidence comes mostly from lab role-plays.

### Phase 1: Setting the stage
- Prepared negotiators do better (Fisher and Ury, 1981; Thompson et al., 2010, as reported in the chapter).
- A strong outside option is the biggest power source. A clearly weak one can anchor a negotiator below having no stated option at all (Schaerer et al., 2015). With several options, people anchor on their average, not their best (Schaerer et al., 2016).
- Walk-away point and outside option are different things. People are bad at sticking to limits once the exchange heats up (competitive arousal, Malhotra, 2010).
- High, specific aspirations raise outcomes (Zetik and Stuhlmacher, 2002). Performance goals help in single-issue haggling but raise impasse rates and cut integrative deals (Tasa et al., 2013); learning goals suit multi-issue talks.
- Adding issues (bulk volume, delivery time) turns a price fight into a trade; most multi-issue deals still keep one dominant price-like issue. Trade-offs need real information on the other side's priorities.
- Prepare answers to awkward questions ("Do you have other offers?"). Deflecting with a question works, but refusing to answer still leaks information and lowers trust (Bitterly and Schweitzer, 2020; John et al., 2016).
- Loss framing makes people less cooperative and more impasse-prone (Bazerman et al., 1982).
- Insincere negotiators exist (stalling, fishing for information; Kang et al., 2020).

### Phase 2: Communicating
- Small talk before business built trust, widened the range of outcomes considered and cut impasses (Morris et al., 2002, as reported).
- Ask direct questions, even sensitive ones; people usually answer truthfully and take little offence (Minson et al., 2018). Presume-a-problem wording ("What problems has it had?") draws more honest answers than "no problems, right?". Even a non-answer is informative.
- Do not reveal your reservation point (the buyer's maximum), since deals then land near it; disclosure helps only to avoid an impasse. Show priorities by offering several packages at once (Leonardelli et al., 2019).
- Assertive first offers anchor outcomes (Galinsky and Mussweiler, 2001; Gunia et al., 2013, as reported), even across cultures. But the chapter says "never go first" advice is wrong when you know the bargaining zone, and that most evidence comes from labs where walking away is hard. Overly aggressive offers can end talks; generous ones can build trust (Jeong et al., 2020).
- Ranges: a precise number signals competence but can seem inflexible; ranges help when the zone is unknown. A range whose aggressive end is the low point (bolstering) paid off; one centred on it did not (Ames and Mason, 2015).
- Concessions: concede on low-priority issues, in shrinking steps, avoid quick ones, justify them, expect reciprocity (mostly practitioner advice; little empirical support, per the chapter). Shrinking steps signal you near your limit (Tey et al., 2021).
- Deception is common and, once caught, costs trust and triggers retaliation. Misstating a bottom line is near-expected; misstating a material fact may be fraud. Paltering (true but misleading statements) is judged as blameworthy as lying (Rogers et al., 2017).
- Anger can extract concessions, but not from someone with a strong alternative or who doubts it is sincere; it also hurts trust, future dealings and implementation. Gratitude and warmth can invite tougher or more deceptive behaviour (Yip et al., 2018). Positive emotion builds trust and cooperation.

### Phase 3: Closing
- Check the signed terms match what was discussed; altered wording and last-minute "nibbling" for extras damage deals. Contracts are incomplete, so expect renegotiation.
- Subjective value (fairness, respect, wish to deal again) predicts later outcomes (Curhan et al., 2006).
- An impasse is not always failure: it can be wanted by both or one side, and walking to the alternative can be best.

### Phase 4: Post-negotiation
- Where value is created after signing (services), relationships matter economically ("ERRO", Hart and Schweitzer, 2022); for plain goods purchases, much less so.
- Accepted first offers leave people dissatisfied (Galinsky et al., 2002). A satisfied counterpart is more committed. Aggressive reputations make later counterparts tougher; trustworthy ones draw more information.

### Technology
- Email versus face-to-face shows few consistent differences; face-to-face is faster and builds more trust (Geiger, 2020). Text suits asynchronous work. AI appears only as a training tool and research instrument; nothing on AI agents negotiating.

### Apply to our buyer agent
1. Open with a firm, specific, ambitious but defensible first offer, with a stored walk-away point. (Communicating: first offers; strong)
2. Never disclose our walk-away price; steer talks away from a bare price. (Communicating: information; moderate)
3. Send up to 3 packages at once and read which the supplier favours to infer priorities. (Communicating: information; moderate)
4. Ask direct questions with a presumed-problem form ("Which terms cost you most?"). (Communicating: questions; moderate)
5. Concede in shrinking steps, on low-priority terms first, never early, each with a stated reason, and ask for something in return. (Concessions; weak to moderate)
6. Add issues (volume, payment days, contract length, delivery) and trade across them. (Setting the stage: issues; strong)
7. Keep tone polite and neutral. No anger, no threats, no repeated gratitude. (Emotion; moderate)
8. Never lie, palter or invent figures; avoid dodging by silence. Deflect with a question if needed. (Deception; strong)
9. Hold the best alternative offer in reserve and don't let a weak one anchor us. (BATNA; strong)
10. Before accepting, re-check final terms against the thread. Treat a price accepted at once as a signal we opened too soft. (Closing, post-negotiation; weak)

### Qualifies or contradicts our existing rules
- Rule 1 (close vs walk away): the chapter supports walking when the alternative beats the offer, and notes impasses can be fine. It also warns people drift past their limits mid-talk, so hard-code the limit.
- Rule 2 (firm numbers, warm tone): partly qualified. Warmth builds trust, but gratitude and positive emotion can reduce concessions. Anger or threats sometimes won concessions, but only against weak-alternative counterparts, and with relational costs.
- Rule 3 (ask why, then trade): supported. One caveat: counterparts may feign interest in an issue to extract trades, so verify priorities.
- Rule 4 (first offers): supported, though the chapter says the evidence is lab-based and extreme offers can drive a counterpart to other suppliers.
- Rule 5 (no bluffing): supported by trust and retaliation findings. The chapter calls bottom-line bluffing nearly expected, but detection is costly; no automated-agent case is tested.


---

# Part C. Search notes (deep-research output, mostly abstract level)


<!-- source file: research/notes/01-books-and-handbooks.md -->
## Books and handbooks on negotiation theory and procurement negotiation (for an AI buyer agent)

Verification legend: [V] = verified on a publisher/catalogue page in this session; [M] = from memory/secondary knowledge, NOT verified. No Google Scholar counts could be fetched, so all citation/reputation signals are [M] and qualitative or order-of-magnitude only. No pirated sources were used; several search hits were PDF-download spam pages for textbooks (e.g. Lewicki, Voss) and were ignored.

### Which books are the research-based negotiation canon, and what are their current editions?

#### Takeaway
The canon is Raiffa (decision-analytic), Thompson, Lewicki et al., Bazerman and Neale / Malhotra and Bazerman (behavioural), Lax and Sebenius (deal design), Fisher/Ury/Patton and Shell (practitioner frameworks), plus research handbooks (Elgar, Oxford, Culture). Verified current editions: Lewicki 8th (2020), Thompson 7th (2020), Getting to Yes 3rd (2011). A 30th-anniversary revised Getting to Yes was announced; release not confirmed.

#### Cited Findings
- Lewicki, Barry, Saunders, *Negotiation*, 8th ed., McGraw-Hill Education, 2020 (previous edition 2015 McGraw-Hill/Irwin); ISBNs 9781260565591 (paperback), 9781260479157 (loose-leaf) — [CiNii](https://ci.nii.ac.jp/ncid/BD14942231), [MIT Press Bookstore](https://mitpressbookstore.mit.edu/book/9781260479157). [V via catalogue]
- Thompson, *The Mind and Heart of the Negotiator*, 7th ed., Pearson, 2020 (print ISBN 9780135197998, eTextbook 9780135641262; Global Edition listed 2021). Pearson dates conflict (2019 vs 2020), so check the ISBN. Structure: essentials (preparation, distributive and integrative bargaining), skills (emotion, trust, power, ethics, creativity), complex negotiation (multiparty, cross-cultural, virtual). — [Pearson](https://www.pearson.com/store/p/the-mind-and-heart-of-the-negotiator/P100002680893/9780135197998). [V]
- Fisher, Ury, Patton, *Getting to Yes*, 3rd ed., Penguin, 2011, ISBN 9780143118756; a revised 30th-anniversary edition was announced but I did not confirm release — [Wake County catalogue](https://catalog.wake.gov/Record/687953), [WorldCat](https://search.worldcat.org/title/609540048). [V via catalogue; edition-announcement unconfirmed]
- Lax and Sebenius, *3-D Negotiation*, Harvard Business School Press / HBR Press, 2006. Three dimensions: tactics, deal design, setup (right parties, right sequence). — [Harvard PON review page](https://www.pon.harvard.edu/resources/book-reviews/3-d-negotiation-powerful-tools-to-change-the-game-in-your-most-important-deals/). [V on content; publisher naming varies by source]
- Raiffa, *The Art and Science of Negotiation*, Harvard University Press (Belknap), 1982; described as bridging popular and scholarly writing, with cases and diagrams — [retailer listing](https://bol.com/nl/nl/p/art-science-of-negotiation/1001004000980094/). Publisher not confirmed in my search. [partly V]
- Malhotra and Bazerman, *Negotiation Genius*, Bantam, 2007; both Harvard Business School; focuses on psychological biases and overcoming them — [getAbstract summary](https://www.getabstract.com/en/summary/negotiation-genius/8909). [partly V; publisher/year M]
- Handbook of Research on Negotiation, eds. Olekalns and Adair, Edward Elgar, 2013; four perspectives: cognition/emotion, social processes, communication, complex negotiations; paperback list £52.95, eBook available — [Elgar](https://www.e-elgar.com/shop/handbook-of-research-on-negotiation), [Melbourne record](https://findanexpert.unimelb.edu.au/scholarlywork/739953-handbook-of-research-on-negotiation). [V]
- Gelfand and Brett (eds.), *The Handbook of Negotiation and Culture*, Stanford University Press, 2004 — [SUP](https://sup.org/books/business/handbook-negotiation-and-culture). [V]
- Croson and Bolton (eds.), *The Oxford Handbook of Economic Conflict Resolution*, OUP (economics/psychology/OB contributors, bargaining experiments) — [OUP](https://academic.oup.com/edited-volume/34464). [V; year M, about 2012]
- The "Cambridge Handbook of Negotiation" named in the brief: I found NO evidence it exists as such. Treat as unverified/likely a mix-up with the Elgar handbook.
- Not searched, from memory [M]: Bazerman and Neale, *Negotiating Rationally* (Free Press, 1992; older); Bazerman and Moore, *Judgment in Managerial Decision Making* (Wiley, 9th ed. believed, verify); Shell, *Bargaining for Advantage* (Penguin, 2nd ed. 2006, a 3rd ed. may exist; verify); Thompson (ed.) *Handbook of Negotiation Research* / Bazerman et al. "Negotiation" (Annual Review of Psychology, 2000) as a short literature review; Brett, *Negotiating Globally* (Jossey-Bass, 3rd ed. 2014); Sebenius, Lax, Raiffa, *Negotiation Analysis* (Raiffa, Richardson, Metcalfe, *Negotiation Analysis: The Science and Art of Collaborative Decision Making*, Harvard UP 2002) is the most formal, decision/game-theory treatment and arguably the most relevant to a quantitative agent.

#### Inferences
- For a scored multi-issue agent, the most directly useful research-based works are Raiffa et al. *Negotiation Analysis* (formal, utility and trade-off modelling), Thompson (evidence on integrative tactics, e.g. multi-issue offers and logrolling), and Lewicki (broad textbook, standard syllabus text). Getting to Yes and Shell are frameworks, not tested prescriptions.
- Lewicki 8th and Thompson 7th are both 2020 editions; as of Oct 2026 I did not confirm newer editions. Check publisher sites before citing.

#### Gaps
- No Google Scholar counts were retrievable; reputation signals above are memory only. A follow-up fetch of Scholar or Semantic Scholar per title is needed.
- Editions of Shell, Bazerman and Moore, Raiffa et al., and Brett not verified here.
- Monthly status of the Getting to Yes 30th-anniversary edition unknown.

### Which procurement/supply-management textbooks cover supplier negotiation?

#### Takeaway
Verified current editions: van Weele and Rozemeijer, *Procurement and Supply Chain Management*, 8th ed. (Cengage, 2022); Handfield, Giunipero, Monczka, Patterson, *Purchasing and Supply Chain Management*, 8th ed. (Cengage, copyright 2026). Chopra's 7th ed. is 2018/2019 and covers sourcing/pricing but little negotiation tactics.

#### Cited Findings
- van Weele and Rozemeijer, *Procurement and Supply Chain Management*, 8th ed., Cengage, 2022, ISBN 9781473779112; adds "Theory snapshots". NOT Springer (earlier editions titled *Purchasing and Supply Chain Management*, Cengage, 5th ed. 2010) — [Cengage UK](https://www.cengage.uk/c/procurement-and-supply-chain-management-8e-van-weele-rozemeijer/9781473779112). [V]
- Handfield, Giunipero, Monczka, Patterson, *Purchasing and Supply Chain Management*, 8th ed., Cengage; hardback ISBN 9798214042039, eBook 9798214042084; copyright 2026, availability April 2025 (dates vary by site); new coverage of AI in procurement, resilience, counterfeit mitigation; 7th ed. was 2021 — [Cengage](https://cengage.com/c/purchasing-and-supply-chain-management-8e-handfield-giunipero-monczka-patterson/9798214042039). [V]
- Chopra, *Supply Chain Management: Strategy, Planning, and Operation*, 7th ed., Pearson, 2018 (© 2019), ISBN 9780134731889; Global Edition 2020. Co-author Meindl credited on earlier editions; not confirmed for 7th. Covers sourcing, pricing, facilities, inventory — [Pearson](https://www.pearson.com/store/en-us/p/supply-chain-management-strategy-planning-and-operation/P200000005863). [V]
- Not verified here [M]: Kraljic (1983) "Purchasing must become supply management", *Harvard Business Review* (the original article, a short read, not a book); Gelderman and van Weele on Kraljic-matrix applications (journal papers, *J. Purchasing & Supply Management*); Cousins, Lamming, Lawson, Squire, *Strategic Supply Management: Principles, Theories and Practice* (FT Prentice Hall, 2008); Lysons and Farrington, *Procurement and Supply Chain Management* (Pearson, 9th ed. believed, verify); Cox's power-regime and Schuh et al., *The Purchasing Value Chain* are other cites. Procurement-specific negotiation texts such as Reck and Long, or Kolb and Williams, not researched.

#### Inferences
- Procurement textbooks give the business context (total cost of ownership, payment terms, contract length, supplier segmentation) that maps directly to the term-sheet issues; they are weaker than the negotiation canon on tactics and evidence.
- The Kraljic matrix literature supports adapting strategy to supplier leverage: bottleneck and strategic items warrant more cooperative, longer-contract deals; leverage items warrant more competitive stances. This is [M]-level reasoning.

#### Gaps
- Kraljic, Cousins et al., Lysons and Farrington not searched; no citation counts or reviews found.
- No Journal of Purchasing and Supply Management book reviews found.

### Which popular books are practitioner opinion with weaker evidence, and how do experts rate them?

#### Takeaway
Voss (*Never Split the Difference*) is practitioner opinion built on hostage-negotiation experience; I found no systematic academic evaluation. Treat tactics (labels, calibrated questions, "no"-oriented questions) as hypotheses, not tested findings. Getting to Yes and Shell are influential but also framework/practitioner books.

#### Cited Findings
- Reviews note that Voss's fairness claims are not put in the context of the academic literature, and that he says where field experience and academic advice conflicted he sided with experience — [Gorelik review](https://gorelik.net/2020/04/25/book-review-never-split-the-difference-by-chris-voss), [SQL Server Central review](https://www.sqlservercentral.com/blogs/bks-bookshelf-never-split-the-difference). Blog-level sources; weak.
- Inside Higher Ed frames the book's message as most conventional advice being wrong; opinion, not evidence — [Inside Higher Ed](https://www.insidehighered.com/node/11954).
- Several search hits claiming the book is "significant empirical scholarship" were templated filler and disregarded.
- Voss, Raz, *Never Split the Difference*, Harper Business, 2016. [M]. It is a bestseller; academic negotiation scholars commonly view it as engaging but not research-based [M, unverified].
- Fisher/Ury/Patton and Shell: widely adopted (Harvard PON, Program on Negotiation, associated with the Harvard Negotiation Project) but criticised by scholars for limited empirical testing and for underplaying distributive bargaining [M].

#### Inferences
- For a bot-vs-bot, scored setting, popular emotional tactics (mirroring, labels) have little direct value; the numeric principles (anchoring, concession patterns, BATNA, trade-offs across issues) matter more.

#### Gaps
- No peer-reviewed or Negotiation Journal review of Voss found; a targeted search of *Negotiation Journal* is needed.

### Which are available via the TUM library or open access?

#### Takeaway
TUM runs a catalogue at search.ub.tum.de (VuFind) and offers 300,000+ e-books incl. about 70,000 Springer titles via eAccess; I found no evidence of Oxford/Cambridge e-book packages. I could not verify holdings for any individual title.

#### Cited Findings
- TUM University Library licensed Springer Book Archives subject areas, giving about 70,000 Springer eBooks (2015 news item); other page says over 300,000 scientific e-books — [UB TUM news](https://ub.tum.de/en/news?page=105), [UB TUM](https://www.ub.tum.de/en/node/5558). Dated; recheck.
- Access is via TUM ID (eAccess); licence terms forbid systematic downloading — [UB TUM](https://www.ub.tum.de/en/node/5558).
- Oxford University Press mentioned only for e-journals since January 2024; Wiley, Sage, T&F as e-journals — [UB TUM](https://www.ub.tum.de/en/node/5558).
- The TUM catalogue does index at least the Elgar *Research Handbook on Gender and Negotiation* (a record exists at [search.ub.tum.de](https://search.ub.tum.de/vufind/Record/DE-604.BV047089845?lng=en)); this shows the catalogue is searchable but not that it holds the other titles.
- Elgar offers the Olekalns/Adair handbook as eBook for purchase — [Elgar](https://www.e-elgar.com/shop/handbook-of-research-on-negotiation).
- Pearson offers an eTextbook (subscription/rental, DRM-locked platform) for Thompson; Cengage sells eTextbook for Handfield et al. — links above. DRM status presumed [M].

#### Inferences
- Springer-published titles (none of the headline books above) would be most likely to be free via TUM. Most listed books are from Pearson, Cengage, McGraw-Hill, Penguin, HBR Press: expect physical library loan (search.ub.tum.de, Bayerische Staatsbibliothek) or purchase. Check via TUM catalogue before buying.
- No open-access full text of the main textbooks found; none should be sought via unauthorised copies.

#### Gaps
- Per-title TUM holdings unchecked (catalogue search not executed); Primo use at TUM unconfirmed (TUM appears to use VuFind/OPAC).
- Oxford/Cambridge e-book access at TUM unconfirmed.

### Ranked reading list (summary; ranking is my judgement for an AI buyer agent)

| # | Book | Edition / year | Evidence type | Access |
|---|------|----------------|---------------|--------|
| 1 | Raiffa, Richardson, Metcalfe, *Negotiation Analysis* [M] | Harvard UP, 2002 | Research, formal | Buy/loan; unverified |
| 2 | Thompson, *Mind and Heart of the Negotiator* [V] | 7th, Pearson 2020 | Research-based textbook | Buy / eText (DRM) / loan |
| 3 | Lewicki, Barry, Saunders, *Negotiation* [V] | 8th, McGraw-Hill 2020 | Research-based textbook | Buy/loan |
| 4 | Malhotra and Bazerman, *Negotiation Genius* [partly V] | Bantam 2007 | Research-informed, practitioner-friendly | Buy/loan |
| 5 | Bazerman and Moore, *Judgment in Managerial Decision Making* [M] | Wiley, recent ed. | Research | Buy/loan |
| 6 | Lax and Sebenius, *3-D Negotiation* [V on content] | HBS Press 2006 | Practitioner plus academic | Buy/loan |
| 7 | Raiffa, *Art and Science of Negotiation* [partly V] | Harvard UP 1982 | Research/analytic classic | Buy/loan |
| 8 | Fisher, Ury, Patton, *Getting to Yes* [V] | 3rd, Penguin 2011 | Practitioner framework | Buy/loan |
| 9 | Olekalns and Adair (eds.), *Handbook of Research on Negotiation* [V] | Elgar 2013 | Research handbook | Elgar eBook; library |
| 10 | Gelfand and Brett (eds.), *Handbook of Negotiation and Culture* [V] | SUP 2004 | Research handbook | Buy/loan |
| 11 | Croson and Bolton (eds.), *Oxford Handbook of Economic Conflict Resolution* [V] | OUP | Research (experimental economics) | OUP Academic; library |
| 12 | Shell, *Bargaining for Advantage* [M] | Penguin | Practitioner | Buy/loan |
| 13 | van Weele and Rozemeijer, *Procurement and SCM* [V] | 8th, Cengage 2022 | Textbook | Buy/loan |
| 14 | Handfield et al., *Purchasing and SCM* [V] | 8th, Cengage 2026 | Textbook | Buy/eText/loan |
| 15 | Cousins et al., *Strategic Supply Management* [M] | FT Prentice Hall 2008 | Textbook/theory | Buy/loan |
| 16 | Chopra, *Supply Chain Management* [V] | 7th, Pearson 2018 | Textbook (limited negotiation) | Buy/loan |
| 17 | Voss and Raz, *Never Split the Difference* [M] | Harper Business 2016 | Practitioner opinion | Buy/loan |
| 18 | Kraljic (1983) HBR article, Gelderman and van Weele papers [M] | Journal articles | Research (segmentation) | HBR purchase; library |

Many [M] entries need a follow-up verification pass (editions, publishers, Scholar counts).


<!-- source file: research/notes/02-core-bargaining-evidence.md -->
## Core experimental findings on bargaining behaviour (for an e-mail buyer agent with multi-issue term sheets)

Method note: web research only (about 15 search/fetch calls), no Tacto API. Everything below comes from search-result abstracts and publisher/repository pages. I read NO full texts. "Access" is my guess unless stated. Items marked [UNVERIFIED] came from my memory or a single secondary page and need a DOI check. Nearly all studies are lab or online experiments with students or panel participants, not field data.

### 1. First offers and anchoring

#### Takeaway
The first-offer effect is large and robust in simple, single-issue, price-type bargaining, and it holds across power, culture and multi-issue settings. Its costs are impasse risk and lower benefit as complexity rises. Extreme offers anchor but can offend and cause walk-aways, especially from low-power recipients. Effect sizes come from one 2025 meta-analysis and are not final-paper verified.

#### Cited Findings
- Meta-analysis of 90 studies (Petrowsky, Loschelder et al., OBHDP 2025, preregistered, robust variance estimation) plus experiments (Studies 2a-2b, N = 2,121). Making the first offer gives an advantage and ambitious first offers give economic gains, but ambitious offers raise impasse odds. Effects shrink as the number and type of issues increase, and the mechanisms change. Conference abstract values: first-mover g = 0.49, first-offer magnitude g = 1.30, offer-outcome r = 0.53 (pre-publication figures, check against the final paper). Heterogeneity is high. DOI 10.1016/j.obhdp.2025.104448. Access: the journal is paywalled, but a Leuphana PubData parallel publication (DOI 10.48548/pubdata-3207) appears open access. Abstract level only. — [Leuphana PubData](https://pubdata.leuphana.de/entities/publication/29dc7e5d-01eb-420a-b73d-66e0be7cd440); [FIS Leuphana summary](https://fis.leuphana.de/en/publications/the-power-and-peril-of-first-offers-in-negotiations-a-conceptual-/)
- Galinsky & Mussweiler (2001), JPSP 81(4), 657-669. Three lab experiments: first offers anchor outcomes, and the effect is reduced when the counterpart takes perspective or focuses on their own target/BATNA information. DOI 10.1037/0022-3514.81.4.657 [UNVERIFIED, from memory]. APA/library access (TUM). Abstract only. — [Kellogg record](https://www.kellogg.northwestern.edu/faculty/research/detail/2001/first-offers-as-anchors-the-role-of-perspective-taking)
- Orr & Guthrie (2006), Ohio State J. on Dispute Resolution 21, 597; meta-analysis of simulated negotiations. Anchoring has a significant effect on deals, tested against experience and information environment. A secondary blog gives r about 0.50 (0.37 adjusted for experience); verify before use. Open access on bepress. Abstract only. — [bepress](https://works.bepress.com/chris-guthrie/18); [Vanderbilt IR](https://ir.vanderbilt.edu/handle/1803/7415); secondary: [Miles Mediation](https://milesmediation.com/blog/make-the-first-move-and-drop-the-anchor-miles-mediation/)
- Gunia, Swaab, Sivanathan & Galinsky (2013), PSPB 39, 1547-1558, "Remarkable robustness of the first-offer effect: across culture, power, and issues". The effect held across cultures and in multi-issue negotiations, and low-power negotiators gained from moving first. The first offer works through the distributive issues, not the integrative or compatible ones. DOI not retrieved. Abstract only. Lab. — [LBS record](https://www.london.edu/faculty-and-research/academic-research/t/the-remarkable-robustness-of-the-first-offer-effect-across-culture-power-and-issues)
- Extreme offers: Schweinsberg, Ku, Wang & Pillutla (2012), JESP 48(1), 226-231, "Starting high and ending with nothing". Two experiments. Extreme first offers still anchor counteroffers and outcomes, but they offend recipients and risk impasse. Low-power and high-power recipients were equally offended, but low-power ones walked away. Abstract only. (A search note said the Kellogg subtitle differs; I did not check author order or the DOI.) — [LBS](https://www.london.edu/faculty-and-research/academic-research/s/starting-high-and-ending-with-nothing-the-role-of-anchors-and-power-in-negotiations); [ISB](https://eprints.exchange.isb.edu/id/eprint/1559/)
- Precision: Loschelder, Friese & Trötschel (2017), JESP 70, 164-176, three experiments. Precise anchors (e.g. 4,970 vs 5,000) anchor recipients more strongly, via an attribution of competence. Senders who use precise numbers choose less extreme (less ambitious) offers. Abstract level only; no effect sizes retrieved. — [Saarland repository](https://publikationen.sulb.uni-saarland.de/handle/20.500.11880/27829); [PON summary](https://www.pon.harvard.edu/daily/dealmaking-daily/negotiation-research-can-use-effective-first-offer-strive-precision-nb/?amp)
- Mussweiler & Strack (1999), JESP 35, 136-164, is the selective accessibility account of anchoring (anchor-consistent knowledge becomes more accessible). Harris et al. (2019) report failures to replicate a key result of that theory (UCL preprint; not read). I did not find a direct Many Labs anchoring replication via search; my memory says Many Labs 1 replicated classic anchoring, but this is unverified. — [LBS record](https://www.london.edu/faculty-and-research/academic-research/a/anchoring-accessibility-as-a-cause-of-judgmental-assimilation); [UCL](https://discovery-pp.ucl.ac.uk/id/eprint/10074759/1/HarrisEtAl_2019_anchoring.pdf)
- Brooks & Schweitzer (2011), OBHDP 115, 43-54: incidental anxiety lowered expectations and opening offers and worsened outcomes (four studies; HBS summary says $6.60 vs $7.94 in one study). Relevant only as evidence that low aspirations lower first offers. — [IDEAS](https://ideas.repec.org/a/eee/jobhdp/v115y2011i1p43-54.html); [HBS](https://hbswk.hbs.edu/item/overcoming-nervous-nelly)

#### Inferences
- For a buyer agent, anchor first with an ambitious but defensible opening, and keep it believable; reserve extreme offers for situations where walking away is not costly. This is an inference from Petrowsky, Schweinsberg and the Leonardelli entries below.
- With a precise (non-round) opening figure, the recipient may be anchored more strongly, but the agent should not shrink its ambition because of it. This is my inference from Loschelder et al.
- In a multi-issue term sheet the anchor effect is concentrated in the price (distributive) issue (Gunia 2013) and weakens as issues multiply (Petrowsky 2025).

#### Gaps
- Final effect sizes, moderator tables and the exact impasse increase from Petrowsky 2025 were not read.
- No direct evidence on anchoring in e-mail or LLM-vs-LLM negotiation was found.
- Replication status of the negotiation-specific effects: no failed replication of the first-offer effect found; the replication of the cognitive mechanism is contested (Harris 2019).

### 2. Concession patterns

#### Takeaway
Hard bargaining wins more money but costs relationship and, in some conditions, impasses. Reciprocating concessions is the best soft strategy. Shrinking concession steps signal a nearing limit and make recipients less ambitious; the evidence is a single 2021 lab paper plus older work.

#### Cited Findings
- Hüffmeier, Freund, Zerres, Backhaus & Hertel (2014), J. Management 40(3), 866-892. Meta-analysis of 34 studies of distributive negotiation (135 economic and 30 socioemotional effect sizes). Hardline strategies gave higher economic outcomes and softline gave higher socioemotional outcomes. Hardliners gained most with visual contact, knowledge of the bargaining zone and a maximize-own-outcome instruction. Softliners did best when they accurately reciprocated concessions, and softline did not win even when impasse risk and cost were high (contrary to prediction). DOI 10.1177/0149206311423788. Likely paywalled (TUM). Abstract only; no d/r values retrieved. — [UvA DARE](https://dare.uva.nl/id/801197e8-e374-4128-aeb3-c66c06cb8812)
- Tey, Schaerer, Madan & Swaab (2021), OBHDP 165, 153-166. Seven studies, N = 2,311. Decreasing concession sequences (e.g. 1,500, 1,210, 1,180, 1,170) lead recipients to make less ambitious counteroffers and reach worse deals, mediated by an inflated estimate of the counterpart's reservation price. The effect is strongest for moderate decline rates and for declines over more rounds; setting a target in advance partly protects recipients. DOI 10.1016/j.obhdp.2021.05.003. Abstract only. Lab/online. — [INSEAD](https://www.insead.edu/faculty-research/publications/journal-articles/impact-concession-patterns-negotiations-when-and-why)
- Lawler & MacMurray (1980), a programmed-opponent study cited in a search snippet: the best response depended on the opponent's opening stance, and prior deadlock reduced concessions. Single secondary snippet, not verified. — [Leuphana snippet](https://fis.leuphana.de/en/publications/concession-patterns-in-dyadic-negotiations-empirically-contrastin/)
- A separate study (found via the same search, authors not retrieved) reports that distributive concession making raises impasse rates, driven by loss of conceded value and not by reciprocity-norm violation. — [TU Dortmund](https://eldorado.tu-dortmund.de/items/f909800c-1d5e-4cb0-9fa9-9745ab154670/full)

#### Inferences
- A seller-facing buyer agent should avoid showing a clear shrinking-step pattern if it wants to hide its limit, and should expect a seller using one to be signalling a limit (but it may be a bluff).
- Reciprocate counterpart concessions in kind; start tough and concede on a pattern that does not leak the limit.

#### Gaps
- No meta-analysis on concession timing found; no evidence tied specifically to e-mail asynchronous bargaining.
- Effect sizes of Hüffmeier 2014 not retrieved.

### 3. BATNA, reservation prices and power

#### Takeaway
Better alternatives raise outcomes and the propensity to move first, but the first-offer anchor can outweigh BATNA effects and, per one study, having no BATNA can beat a weak one. Evidence on disclosing information is weak in my findings.

#### Cited Findings
- Kim & Fragale (2005), J. Applied Psychology 90(2), 373-381. BATNA advantage mattered more when the bargaining zone was small, contribution advantage when it was large. DOI 10.1037/0021-9010.90.2.373 (as found by search; not opened). Abstract level. — [summary page](https://academicnewsletter.sufe.edu.cn/info/372348)
- Magee, Galinsky & Gruenfeld (2007), PSPB 33(2), 200-212. Five experiments. Higher power increased propensity to negotiate and to move first; negotiators with strong BATNAs were over three times as likely to intend to open (as reported by the abstract summary); making the first offer gave a bargaining edge. Abstract only. — [Kellogg](https://www.kellogg.northwestern.edu/academics-research/research/detail/2007/power-propensity-to-negotiate-and-moving-first-in-competitive/?p=1)
- Pinkley, Neale & Bennett (1994), OBHDP 57(1), 97-116, "The impact of alternatives to settlement in dyadic negotiation". Content not retrieved; only the citation. A 1995 Pinkley OBHDP paper on BATNA knowledge was not confirmed. — [IDEAS](https://ideas.repec.org/a/eee/jobhdp/v57y1994i1p97-116.html)
- Schaerer, Swaab & Galinsky, Psychological Science (about 2015; year and title unconfirmed): negotiators with no BATNA did better than those with weak BATNAs, because they made higher first offers (anchors weigh more than power). Seen only in a search note; [UNVERIFIED]. — [APS](https://www.psychologicalscience.org/news/minds-business/negotiating-with-nothing-holds-surprise-benefits.html)
- Schweinsberg et al. 2012 (section 1): power moderates whether extreme anchors lead to walk-aways.
- Gunia, Brett, Nandkeolyar & Kamdar (2011), J. Applied Psychology 96(4), 774-789, three studies: lower interpersonal trust in Indian negotiators went with less information-sharing and lower joint gains than for US negotiators. Relevant to information exchange, not BATNA. — [Kellogg](https://www.kellogg.northwestern.edu/faculty/research/detail/2011/paying-a-price-culture-trust-and-negotiation-consequences/?p=1)
- Kong, Dirks & Ferrin (2014), Acad. Management J. 57(5), 1235-1255. Meta-analysis of 38 independent studies on trust within negotiations, with three contingencies. Effect sizes not retrieved. — [MetaTOC](https://metatoc.com/papers/23303-interpersonal-trust-within-negotiations-meta-analytic-evidence-critical-contingencies-and-directions-for-future-research)

#### Inferences
- A buyer agent should have its BATNA/reservation value internally and may move first when its BATNA is good, but should not reveal the reservation price (no direct evidence retrieved on disclosure; this is a design judgment). Evidence is largely lab.

#### Gaps
- Evidence on disclosing versus hiding BATNA/reservation price (Pinkley 1995, Morris/Larrick/Su, Gunia et al. alternatives) was not retrieved. Treat as open.
- Replication status of the weak-BATNA result is unknown.

### 4. Multi-issue offers, MESOs, logrolling, questions, information

#### Takeaway
MESOs, information exchange and question-asking raise joint gains and rapport in lab studies; the fixed-pie bias is the main obstacle. A buyer agent sending packages with several equivalent options should gain both anchoring and integrative benefits. The evidence is lab-based.

#### Cited Findings
- Leonardelli, Gu, McRuer, Medvec & Galinsky (2019), OBHDP 152, 64-83, six experiments. MESOs (multiple equivalent simultaneous offers) vs a single package: stronger anchors and better outcomes for the offerer (recipients saw them as more sincere), greater joint outcomes, and a more cooperative climate. DOI 10.1016/j.obhdp.2019.01.007. Abstract only; participant numbers not retrieved. — [Macquarie](https://researchers.mq.edu.au/en/publications/multiple-equivalent-simultaneous-offers-mesos-reduce-the-negotiat/)
- Thompson (1991), JESP 27(2)? (a search result said 40(2), 161-179; volume/pages inconsistent, check) "Information exchange in negotiation". Giving and seeking information both improved accuracy of judgment and produced more integrative agreements, even when only one side did so. Abstract only. — [Kellogg](https://www.kellogg.northwestern.edu/academics-research/research/detail/1991/information-exchange-in-negotiation)
- Thompson & Hastie (1990), Org. Behav. Human Decis. Processes, "Judgment tasks and biases in negotiation" (my memory for the title; the page said "Social perception in negotiation"-type content; check): fixed-sum assumption is widespread; people who missed integrative potential got lower individual and joint profit; many learn through negotiation. Abstract level. — [Kellogg](https://www.kellogg.northwestern.edu/academics-research/research/detail/1990/judgment-tasks-and-biases-in-negotiation/)
- Bazerman & Neale (1983) is the origin of the biases framework (secondary source only). A 2002 JBDM study on initial perceptions found logrolling offers were not judged more attractive, did not dispel the fixed-pie assumption, but still gave the initiator and the pair higher profit. — [CRIS HUJI](https://cris.huji.ac.il/en/publications/initial-perceptions-in-negotiations-evaluation-and-response-to-lo-2/)
- Huang, Yeomans, Brooks, Minson & Gino (2017), JPSP 113(3), 430-452. Question-asking, especially follow-up questions, increased liking via perceived responsiveness; people do not predict this. This is about liking in conversation (including speed dating), not negotiation outcomes. DOI 10.1037/pspi0000097. Open author copy at Harvard DASH. Abstract only. — [DASH](https://dash.harvard.edu/entities/publication/73120379-2eb6-6bd4-e053-0100007fdf3b)
- De Dreu, Weingart & Kwon (2000), JPSP 78, 889-905. Meta-analysis of 28 studies: prosocial negotiators were less contentious, solved problems more and got higher joint outcomes, but only when resistance to yielding was high or unknown. No effect size retrieved. — [UvA DARE](https://dare.uva.nl/id/403ebedc-c455-47a0-8a00-803afaed87b3)
- Thompson, Wang & Gunia (2010), Annual Review of Psychology 61, 491-515, "Negotiation": review at five levels (intrapersonal, interpersonal, group, organizational, virtual) on value creation and claiming. Contents not read. — [Kellogg](https://www.kellogg.northwestern.edu/academics-research/research/detail/2010/negotiation/)
- Petrowsky 2025 and Gunia 2013 (section 1): first-offer effects shrink with more issues and act through distributive issues.

#### Inferences
- Offering 2-3 equivalent packages that vary price, payment days, contract length and delivery should combine anchoring with logrolling; ask about counterpart priorities (questions plus sharing own preferences) before settling.
- Question-asking effects on liking may carry to rapport in e-mail, but there is no direct negotiation-outcome evidence in what I retrieved.

#### Gaps
- A Huang et al.-style test of question-asking in negotiation outcomes (e.g. Minson/Brooks work) was not retrieved.
- Fixed-pie quantitative effect sizes, Loewenstein/Thompson/Bazerman details, and replication status of MESO and logrolling studies are unknown.
- Whether MESOs work in written/e-mail or agent settings: not found.

### Source access summary
Open or likely open: Orr & Guthrie (bepress), Petrowsky 2025 via Leuphana parallel publication, Huang 2017 (DASH). Likely TUM/library: Galinsky & Mussweiler, Leonardelli, Hüffmeier, Kong, De Dreu et al., Tey et al., Thompson/Wang/Gunia, Kim & Fragale, Magee et al., Gunia et al.


<!-- source file: research/notes/03-emotion-trust-email.md -->
## Social-psychology of negotiation: emotion, deception/trust, e-mail, language style, tone (for an AI buyer agent e-mailing supplier bots)

Method note: web search only (no Tacto API). Search tool returns abstract-level snippets. NO full texts were read; every source below is "abstract/record only" unless stated. Sample sizes and effect sizes were NOT retrievable from abstracts, so none are given (listed as Gaps). Access: "OA?" = open copy seen in search results; otherwise library (TUM) access likely needed. Items marked [memory] come from my background knowledge, not verified in this session.

### Emotion: anger, happiness, gratitude, apologies, disappointment

#### Takeaway
Anger from the counterpart usually extracts concessions when the target is low-power, has little alternative, and is motivated to read the emotion; but it costs relationship, trust and invites covert retaliation, and its effect flips with context, intensity, and expresser. Positive emotion buys goodwill and future deals; gratitude and excess friendliness can be exploited in distributive (price) bargaining.

#### Cited Findings
- Three experiments: negotiators conceded more to an angry than a happy opponent; they infer the opponent's limit from emotion and lower their demands; effect vanishes if the opponent already conceded a lot; anger induces fear that mediates it. Lab, JPSP 2004, DOI 10.1037/0022-3514.86.1.57; abstract only; library access (a UvA/Cardiff repository copy appeared) — [Van Kleef, De Dreu & Manstead 2004](https://orca.cardiff.ac.uk/id/eprint/3368/)
- Companion paper: effect of opponent emotion appears mainly when negotiators have low need for closure / are motivated and able to process (JPSP 87(4):510-528, 2004); the 2006 EJSP follow-up: low-power negotiators influenced by opponent emotions, high-power ones not. Abstract only — via search summary of [ORCA record](https://orca.cardiff.ac.uk/id/eprint/3368/)
- Replication status: the search summary mentions an independent direct replication finding "almost the same pattern" as the original, but I could not identify its authors or venue; treat as unverified — [ORCA record](https://orca.cardiff.ac.uk/id/eprint/3368/)
- Power moderates: anger helped powerful negotiators (their emotion mainly shaped own behaviour); low-power negotiators were more affected by powerful counterpart's emotion; anger in the dyad, especially from the powerful party, supported more value creation. Lab, OBHDP 2010, DOI 10.1016/j.obhdp.2010.02.004; abstract only; OA copy (Minerva Access) — [Overbeck, Neale & Govan 2010](https://ideas.repec.org/a/eee/jobhdp/v112y2010i2p126-139.html)
- Hidden costs: opponent anger yielded overt concessions but also covert sabotage; low-power negotiators conceded more to angry high-power opponents yet retaliated covertly; mediated by feeling mistreated. Lab, OBHDP 2012, DOI 10.1016/j.obhdp.2012.05.002; abstract only — [Wang, Northcraft & Van Kleef 2012](https://researchportalplus.anu.edu.au/en/publications/beyond-negotiated-outcomes-the-hidden-costs-of-anger-expression-i/)
- Context moderates anger: "Context matters: social effects of anger in cooperative, balanced, and competitive negotiation situations" (Adam & Brett, JESP 61:44-58, 2015). I could not see the abstract; the title implies anger's effect depends on situation. Details unverified — [record](https://researchportal.bath.ac.uk/en/publications/context-matters-the-social-effects-of-anger-in-cooperative-balanc/fingerprints/)
- Adam & Brett 2018 JESP 76:12-18: "Everything in moderation: social effects of anger depend on perceived intensity" (title from CV only; content not read) — [Adam CV](https://business.rice.edu/sites/default/files/uploads/cv/Hajo-Adam-CV-June-2018.pdf)
- Expresser's culture: anger by East Asian expressers backfired (seen as tougher/threatening) when stereotype of inexpressiveness held (Adam, Shirako & Maddux 2010 Psych Sci; Adam & Shirako 2013 J Appl Psychol). Abstract-level summary only — [APS release](https://www.psychologicalscience.org/news/releases/cultural-reactions-to-anger-expression-can-affect-negotiation-outcomes.html)
- Anxiety: anxious negotiators expected less, made lower first offers, exited earlier, got worse outcomes; moderated by self-efficacy. 4 studies, lab, OBHDP 115:43-54, 2011; abstract only — [Brooks & Schweitzer 2011](https://ideas.repec.org/a/eee/jobhdp/v115y2011i1p43-54.html)
- Positive emotion: positive display raised likelihood of writing a future relationship into the contract, extracted more concessions in a distributive setting and increased deal closing in an ultimatum setting; negative display provoked more extreme demands. Lab, OBHDP 99:81-101, 2006; abstract-level; OA copy in Michigan Deep Blue — [Kopelman, Rosette & Thompson 2006](https://deepblue.lib.umich.edu/bitstream/handle/2027.42/49354/1064-Kopelman.pdf;sequence=1)
- Gratitude: five studies reported that grateful messages invited more aggressive counteroffers in single-issue distributive negotiation, via the sender seeming more agreeable/forgiving; gratitude also triggered self-serving deception; omitting "thank you" did not change impasse. Authors per search summary: Yip, Chan, Brooks (unverified). Abstract only — [HBS Working Knowledge item](https://hbswk.hbs.edu/item/thanks-for-nothing-expressing-gratitude-invites-exploitation-by-competitors?cid=wk-rss)
- Gratitude contrast: Harvard PON briefing notes experts commonly advise thanking for concessions to induce reciprocation (practitioner source, not a study) — [PON](https://www.pon.harvard.edu/publication/negotiation-briefings/march-2017/)
- Review: anger can promote collaboration/performance when observers are motivated and able to process and see anger as appropriate. Narrative review, NOT a meta-analysis (my brief assumed one; I found none on negotiation anger). Annu Rev Psychol 73:629-658, DOI 10.1146/annurev-psych-020821-010855; OA PDF at link — [Van Kleef & Côté 2022](https://annualreviews.org/doi/pdf/10.1146/annurev-psych-020821-010855)

#### Inferences
- A buyer bot should not rely on feigned anger: it works mainly against low-power, motivated-to-process, no-fallback counterparts, and bots "reacting like people" may also retaliate (delay, withhold discounts, worse terms later). Mild, targeted dissatisfaction ("this price is above what we can accept") is safer than hostile tone.
- If the supplier is the weaker party, a firm-but-polite stance plus a credible limit signal captures most of the anger effect without the retaliation cost.
- Avoid effusive thanks for each concession before the price is settled; thank at close / for process.

#### Gaps
- No sample sizes or effect sizes retrieved (abstract-only). Effect-size meta-analysis of emotion in negotiation not found. Disappointment and apology effects in negotiation not searched/retrieved. Wang et al. on gratitude/positive emotion not identified. Replication status of Adam & Brett 2015 unknown.

### Deception, bluffing, trust and reputation

#### Takeaway
Deception is common where information is private and stakes are high, and exposed lies rarely change the liar's behaviour but do cause rejections; trust broken by deception is hard to repair. Trust in negotiation has reliable positive effects on cooperation and outcomes (meta-analysis).

#### Cited Findings
- Meta-analysis of 38 independent studies on interpersonal trust within negotiations, supporting a social-exchange model with three contingencies. AMJ 57(5):1235-1255, DOI 10.5465/amj.2012.0461; abstract only; library access — [Kong, Dirks & Ferrin 2014](https://ink.library.smu.edu.sg/lkcsb_research/3530)
- Follow-up meta-analysis of 25 studies on determinants of trust in dyadic negotiation (Lu, Kong, Ferrin & Dirks 2017, J Trust Research) — [search summary](https://ink.library.smu.edu.sg/lkcsb_research/3750)
- Repeated ultimatum bargaining with chat: proposers and responders both used deception, proposers lied more outright, deception peaked with hidden information and large potential profit; exposed lies led responders to reject later offers more but barely changed proposers' behaviour. Lab; OBHDP 83(2):235-259, 2000, DOI 10.1006/obhd.2000.2908; abstract only; a PDF copy of unclear legitimacy appeared in search, not used — [Boles, Croson & Murnighan 2000](https://ideas.repec.org/a/eee/jobhdp/v83y2000i2p235-259.html)
- Trust repair: trust broken by untrustworthy acts can be rebuilt by a consistent run of trustworthy actions; deception-based violations never fully recover; promises help less after deception; apologies alone do little. Lab, OBHDP 101(1):1-19, 2006, DOI 10.1016/j.obhdp.2006.05.005; OA PDF on Wharton site — [Schweitzer, Hershey & Bradlow 2006](https://faculty.wharton.upenn.edu/wp-content/uploads/2014/06/Promises-and-Lies.pdf)
- Envy increases deception toward the counterpart; emotion shapes the decision to lie (Gino & Pierce; Gino & Shea 2012 chapter "Deception in Negotiation: The Influence of Emotion"). Attribution partly unverified — [UPenn repository](https://repository.upenn.edu/mgmt_papers/316)
- Note: a Gino-coauthored line of honesty research has had data-integrity controversy in the field [memory]; verify before relying on any Gino-authored finding.

#### Inferences
- Truthful, verifiable statements are the safer default for a repeated buyer-supplier game: a detected lie is costly and nearly unrepairable, and exposure does not make the liar change, so reputation is the main deterrent.
- Bluffs about alternatives or limits should be limited to ones that are true or unfalsifiable; never assert false facts.

#### Gaps
- Schweitzer's work on strategic lying consequences (e.g. "sins of omission/commission"), Gino & Shea full text, field evidence on long-run honesty payoffs, and sample sizes: not retrieved.

### E-mail and text negotiation

#### Takeaway
Text media reduce rapport and trust; a brief personal exchange (a phone call or small talk) before e-mailing improves rapport, trust and outcomes; online bargaining lowers trust and desire to deal again even when economic outcomes are similar.

#### Cited Findings
- Study 1: e-mail enabled more complex multi-issue offers but reduced rapport-building and clarifying questions. Study 2: a short non-business phone call before e-mail negotiation raised rapport and trust and improved economic and social outcomes (strongest in mixed-gender dyads per working-paper abstract). Lab, Group Dynamics 6(1):89-100, 2002; abstract only; library access — [Morris et al. 2002](https://www.gsb.stanford.edu/faculty-research/working-papers/schmooze-or-lose-social-friction-lubrication-e-mail-negotiations)
- Unverified: lecture slides claim schmoozing dyads were ~4x more likely to reach agreement in a car-sale case; not found in paper abstracts — [MIT OCW](https://ocw.mit.edu/courses/15-067-competitive-decision-making-and-negotiation-spring-2011/33e23c6847d142924edf209482a23caf_MIT15_067S11_lec05.pdf)
- Online negotiators began with lower trust, ended with lower trust, were less satisfied and less keen to deal again; economic outcomes did not differ. Lab, J Appl Psychol 88(1):113-120, 2003; abstract only — [Naquin & Paulson 2003](https://ngdc.cncb.ac.cn:443/openlb/publication/OLB-PM-12675399)
- Chapter arguing the medium itself shapes negotiation ("faceless other"); only the opening read — [Nadler & Shestowsky 2006](https://wwws.law.northwestern.edu/faculty/fulltime/nadler/nadler_shestowsky.pdf)
- Not found: Geiger 2020 review; findings on response time and message length (no sourced evidence).

#### Inferences
- A bot cannot make a phone call, but can open with a short personal/process-oriented line (acknowledge relationship, shared goal) before numbers, and ask clarifying questions; this imitates the schmoozing mechanism, though transfer of the effect from humans to bots is untested.

#### Gaps
- Response time, message length, impasse-rate magnitudes, Geiger 2020, replication status of schmoozing: not retrieved.

### Language style, framing, subjective value

#### Takeaway
Language style matching (LSM) is linked to rapport and success, but more is not always better: in instant-message negotiations high LSM went with more engagement but also more impasse. Subjective value (relationship, process, self, outcome feelings) predicts future dealings better than economic outcome.

#### Cited Findings
- 64 instant-messenger dyads with self-interested goals: higher LSM overall meant more social engagement, less task focus and more impasse; early (not late) matching predicted more positive interaction. NCMR, Ireland & Henderson 2014; abstract only — [Texas Tech record](https://scholars.ttu.edu/en/publications/language-style-matching-engagement-and-impasse-in-negotiations-5)
- Nine hostage negotiations (field, small n): successful ones had higher and steadier LSM. NCMR 2008; abstract only — [Taylor & Thomas 2008](https://eprints.lancs.ac.uk/id/eprint/26912)
- Subjective Value Inventory: four factors (instrumental outcome, self, process, relationship); 16 items; subjective value predicted future negotiation decisions better than economic outcome; in a role-play, outcome alone did not predict wish to work together again. JPSP 2006 (DOI from memory: 10.1037/0022-3514.91.3.493, unverified); OA MIT working-paper version; abstract/summary only — [Curhan, Elfenbein & Xu 2006](https://dspace.mit.edu/handle/1721.1/18234)
- Ireland et al. 2011 (LSM and relationship initiation/stability) found only through citations; not verified. Jeong et al. and fairness-norm literature not retrieved.

#### Inferences
- Mirror the supplier's register early, then stay on task; do not over-mirror. Design message endings that leave the supplier feeling heard (process) and respected (self) since those drive repeat business.

#### Gaps
- Politeness effects, demand-framing and fairness-norm studies, Jeong et al.: not retrieved.

### Collaborative vs competitive tone in buyer-supplier setting

#### Takeaway
No buyer-supplier-specific study was retrieved. Indirect evidence: trust meta-analysis, emotion studies, and subjective-value work favour a collaborative tone with firm substance; anger is a high-variance tactic.

#### Cited Findings
- See sections above (Kong et al. 2014; Wang et al. 2012; Curhan et al. 2006; Kopelman et al. 2006).

#### Inferences
- Recommended default: warm, concise, truthful, firm on numbers; reserve mild dissatisfaction for lowballing suppliers; keep the same register across turns (stable LSM rather than swings).

#### Gaps
- Field studies in procurement and bot-specific evidence on tone effects: not searched.


<!-- source file: research/notes/04-procurement-buyer-supplier.md -->
## Procurement and buyer-supplier negotiation (Kraljic, power, price negotiation)

Access key: every item below was seen via web search snippets/abstract pages only (full-text fetches of Springer, ScienceDirect, Salford, preprints.org returned 403 or redirect). No full text was read for any source. TUM access status not checked. No Tacto arena API was used.

### Kraljic and portfolio models: negotiation strategy per quadrant

#### Takeaway
Portfolio models suggest differentiated negotiation styles (competitive for leverage, collaborative for strategic, accommodative for bottleneck), and one experiment supports this. But empirical work shows buyers use all tactics in all quadrants, and critics say the matrix can mislead. Treat the quadrant to style mapping as a heuristic, not a law.

#### Cited Findings
- Kraljic, P. (1983), "Purchasing must become supply management", Harvard Business Review 61(5), 109-117; HBR page hbr.org/1983/09/purchasing-must-become-supply-management. Paid at HBR; a circulating university copy exists but its provenance is unverified, so I did not use it. Citation only, abstract-level — [Wikipedia: Kraljic matrix](https://en.wikipedia.org/wiki/Kraljic_matrix)
- Kang, Hong, Bartnik, Park, Ko (2018), "Aligning purchasing portfolio management with sourcing negotiation styles", Management Decision, DOI 10.1108/MD-09-2016-0662 (paywalled; abstract only). Case study plus experiment with 77 sourcing professionals; competitive style for leverage items, collaborative for strategic, accommodative for bottleneck; effective buyers choose style by switching costs, dependence and availability of alternatives — [Emerald](https://www.emeraldinsight.com/insight/content/doi/10.1108/MD-09-2016-0662/full/html); [UToledo record](https://scholars.utoledo.edu/display/n2537)
- Lambrechts, Gelderman, Weelink, Semeijn (IPSERA 2019 conference paper), "How do buyers actually negotiate with their leverage and strategic suppliers? Analysis of negotiation topics, tactics and outcomes". Interviews with professional purchasers; both integrative and distributive tactics appear in every relationship type, contradicting the belief that hard bargaining is absent in strategic partnerships. Only the portal page and a search summary seen; year inferred from the summary, not verified — [Open Universiteit portal](https://research.ou.nl/en/publications/how-do-buyers-actually-negotiate-with-their-leverage-and-strategi/)
- Hesping and Schiele (2016), International Journal of Production Economics. Survey of 107 sourcing projects: the full range of tactical sourcing levers is used in all four Kraljic quadrants; authors suggest the matrix works better as a discussion tool than as exclusive prescriptions. Secondary summary only — [Twente record](https://research.utwente.nl/en/publications/matching-tactical-sourcing-levers-with-the-kralji%C4%8D-matrix-empiric/)
- Gelderman and Van Weele (2005), "Purchasing portfolio models: a critique and update", Journal of Supply Chain Management 41(3), 19-28: argues portfolio models can mislead managers. Gelderman and Van Weele (2003), JPSM 9(5), 207-216, on measurement issues and strategic directions in Kraljic's model. Citations from secondary summaries; not read — [IMP paper](https://impgroup.org/wp-content/uploads/wpallimport/files/papers/170.pdf)
- Caniëls and Gelderman (2005), "Purchasing strategies in the Kraljic matrix: a power and dependence perspective", JPSM. Exists per search summary; ScienceDirect returned 403, so no findings verified — [search summary source](https://impgroup.org/wp-content/uploads/wpallimport/files/papers/170.pdf)

#### Inferences
- For a bot with goals stabilise/secure_supply/quality_first/leverage/routine, mapping goal to style (leverage: competitive with alternatives; secure_supply/bottleneck: accommodative; stabilise/strategic: collaborative with firm anchors) is supported by one experiment, but expect mixed tactics rather than pure styles.

#### Gaps
- Pagell, Nellore and Söderquist, and Cox quadrant-specific prescriptions: searches did not retrieve them. Not verified.
- Kraljic 1983 article content (quadrant strategies in original wording): not read.

### Power, dependence and relationship effects

#### Takeaway
Power in buyer-supplier dyads depends on dependence and alternatives; use of coercive or mediated power tends to harm relationship quality and supplier cooperation, while perceptions of power are often subjective.

#### Cited Findings
- Cox, Watson, Lonsdale, Sanderson (2004), "Managing appropriately in power regimes: relationship and performance management in 12 supply chain cases", Supply Chain Management: An International Journal 9(5), 357-371. Found a link between ability to improve supplier performance and the power circumstances; managers often misperceive their available sourcing choices — [Emerald](https://www.emerald.com/scm/article/9/5/357/349869/Managing-appropriately-in-power-regimes); [Emerald DOI page](https://emeraldinsight.com/insight/content/doi/10.1108/13598540410560748/full/html) (summary-level, not full text)
- Cox power regimes framework: looks beyond single dyads to the network of relationships — [IMP Group](https://impgroup.org/?p=3519)
- Mediated power (reward/coercion) in outsourcing relationships, 102 dyads, Journal of Operations Management (2012): mediated power use lowers relationship quality; buyers use it less when they are more dependent on the provider. Authors/DOI not captured — [IAOR record](https://ftp.iaorifors.com/paper/80709)
- Leonidou and colleagues, meta-analysis of exercised power (120 studies, 103 articles): coercive power expected to weaken trust, commitment, cooperation. Venue not confirmed — [Springer Professional abstract](https://www.springerprofessional.de/a-meta-analysis-of-power-in-buyer-seller-relationships-an-abstra/16589268)
- Dependence and use of power raise opportunism (240 Chinese firms), IJOPM, DOI 10.1108/IJOPM-07-2017-0383 — [Emerald](https://emerald.com/insight/content/doi/10.1108/IJOPM-07-2017-0383/full/html)
- Chae, Choi, Hur (2017), Journal of Supply Chain Management: reward and coercive power are mediated powers; supplier response ranges from compliance to deeper commitment — [search summary](https://wrap.warwick.ac.uk/179641)

#### Inferences
- A buyer bot should invoke power implicitly (credible alternatives, volume) rather than coercively when it needs future cooperation (secure_supply, quality_first).

#### Gaps
- Emerson (1962), Hingley, Kim, supplier-initiated bonding: not found this session.

### Negotiation practice: RFQs, e-auctions, payment terms, indexation

#### Takeaway
Competitive auctions cut price but erode trust; payment-term and index clauses are mainly documented by practitioner/vendor sources, not peer-reviewed work found here.

#### Cited Findings
- Fugger, Katok, Wambach (2019), "Trust in procurement interactions", Management Science, DOI 10.1287/mnsc.2018.3196: standard reverse auctions give lower prices but reduce cooperation; buyer-determined auctions can do better for both sides — [Katok PDF](https://personal.utdallas.edu/~ekatok/trust-procurement-interactions.pdf); [INFORMS](https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2018.3196) (open PDF author copy; abstract-level read)
- Jap's work: open-bid reverse auctions save cost but suppliers see buyers as more opportunistic than in sealed-bid; buyers struggle to dispel this. Secondary summary — [NCSU SCM](https://scm.ncsu.edu/scm-articles/article/perils-of-reverse-auctions)
- Herold, Heller, Rozemeijer, Mahr (2025), "Brave new procurement deals", JPSM art. 101012, DOI 10.1016/j.pursup.2025.101012. Three experiments; supplier humans versus ChatGPT-based buyer chatbot. Competitive prompt: bigger discount, better payment terms, faster deal. Collaborative prompt: more supplier trust, satisfaction, wish for future dealings. Abstract only — [Maastricht CRIS](https://cris.maastrichtuniversity.nl/en/publications/brave-new-procurement-deals-an-experimental-study-of-how-generati/)
- Practitioner: supply chain finance (reverse factoring) lets suppliers be paid early at the buyer's credit cost; vendor example says a 60-to-90-day extension helps the supplier if its cost of capital exceeds about 2.4% with SCF at about 1.5% — [PrimeRevenue](https://primerevenue.com/resources/blog/fair/) (vendor, low evidence quality); caution that extended terms can hurt supplier health — [Shumaker newsletter](https://www.shumaker.com/Templates/media/files/pdf/news/publications/-insights-supply-chain-finance.pdf)
- Practitioner: index-linked clauses need reference index, formula, review interval, caps/floors; example 5% trigger with 60% pass-through; 3-5% thresholds cited without source — [Tacto glossary](https://www.tacto.ai/en/procurement-glossary/raw-material-price-adjustment-clause) (vendor, low evidence quality)

#### Inferences
- Giving a shared-index, capped pass-through is a defensible middle route for raw-material surcharge requests; a competitive prompt wins price but costs trust, so match to goal.

#### Gaps
- No peer-reviewed source found for should-cost, dual sourcing, supplier development after quality problems, or payment-terms trade-offs.

### Reviews and training evidence

#### Takeaway
Kelly and Chicksand 2024 is the main systematic review of bargaining in PSM; the AI-in-negotiation review is newer. I could not locate "Heunis et al. 2025".

#### Cited Findings
- Kelly and Chicksand (2024), "A Critical Exploration of Bargaining in Purchasing and Supply Management: A Systematic Literature Review", Group Decision and Negotiation 33(3), 617-646, DOI 10.1007/s10726-024-09879-9. 427 papers from five databases; model and recommendations by bargaining stage; flagged gap: contradictory findings on volume/size effect on bargaining power. Accepted manuscript at Salford repository (403 on fetch). Abstract-level — [Salford](https://salford-repository.worktribe.com/output/2470173/a-critical-exploration-of-bargaining-in-purchasing-and-supply-management-a-systematic-literature-review); [IDEAS](https://ideas.repec.org/a/spr/grdene/v33y2024i3d10.1007_s10726-024-09879-9.html)
- Kelly and colleagues, systematic review of AI in PSM negotiation (63 papers, IPSERA 2025); journal status unconfirmed — [Salford](https://salford-repository.worktribe.com/output/3938707/a-systematic-literature-review-of-the-use-of-ai-in-negotiation-activities)
- Practitioner book: O'Brien, Negotiation for Procurement and Supply Chain Professionals, Kogan Page, 4th ed. 2025 (Red Sheet method); not peer-reviewed — [Kogan Page](https://www.koganpage.com/logistics-supplychain-operations/negotiation-for-procurement-and-supply-chain-professionals-9781398620964)

#### Gaps
- Heunis et al. 2025: not found in two searches; may be misspelled.
- Negotiation-training effectiveness evidence in purchasing: none found.
- CIPS, ISM, McKinsey/BCG/Gartner, ISO 20400: not searched (tool budget); no claims made.
- Open-access status of most papers unverified; check TUM library for Elsevier/Emerald items.


<!-- source file: research/notes/05-ai-negotiation-experiments.md -->
## AI/LLM Agent Negotiation Experiments: Evidence for an LLM Buyer Agent

Scope note: lower-priority section. Reading depth is stated per source: FULL = passages from full text read via the paper-reading tool (retrieved passages, not necessarily the whole paper); ABS = abstract/search snippet only; MEM = from model memory or a secondary mention, NOT verified in this session. Many 2026 arXiv items are preprints from the last months and are unreplicated. Treat all preprint numbers as preliminary.

### Source register

| Source | Venue / status | ID | Year | Open access | Read |
|---|---|---|---|---|---|
| Vaccaro, Caosun, Ju, Aral, Curhan, "Advancing AI Negotiations" | PNAS (peer-reviewed); preprint v3 | doi 10.1073/pnas.2521774123; arXiv 2503.06416; PMC13250504 | 2025-26 | Yes (arXiv, PMC) | FULL (partial passages, arXiv v3) |
| Herold, Heller, Rozemeijer, Mahr, "Brave new procurement deals" | J. Purchasing & Supply Mgmt 31(4) 101012 (peer-reviewed). NOTE: this is JPSM = Purchasing and Supply Management, not Personal Selling and Sales Management | doi 10.1016/j.pursup.2025.101012 | 2025 | Not checked | Secondary web-search summary only |
| Bianchi et al., NegotiationArena | Preprint (ICML 2024 per my memory, unverified) | arXiv 2402.05863 | 2024 | Yes | FULL (partial) |
| Fu, Peng, Khot, Lapata, "Improving LM negotiation with self-play..." | Preprint (ICLR 2024 per memory, unverified) | arXiv 2305.10142 | 2023 | Yes | ABS |
| Davidson et al., "Evaluating LM agency through negotiations" | Preprint (ICLR 2024 per memory, unverified) | arXiv 2401.04536 | 2024 | Yes | ABS |
| Xia et al., "Measuring Bargaining Abilities of LLMs" (OG-Narrator) | Preprint (author list/venue not verified) | arXiv 2402.15813 | 2024 | Yes | FULL (partial) |
| Zhu, Cui et al., PieArena | Preprint | arXiv 2602.05302 | 2026 | Yes | FULL (partial) |
| Li, Bergemann, Ghili et al., "Training LMs for Bilateral Trade" | Preprint | arXiv 2604.16472 | 2026 | Yes (CC BY) | FULL (partial) |
| "The Illusion of Rationality" (NegotiationArena revisit) | Preprint | arXiv 2512.09254 | 2025 | Yes | ABS |
| "LLM Rationalis?" human vs LLM concession dynamics | Preprint | arXiv 2512.13063 | 2025 | Yes | ABS |
| "Counterparty Modeling is Not Strategy" | Preprint | arXiv 2605.16575 | 2026 | Yes | ABS |
| "Used Car Salesbots?" honesty/credulity | Preprint | arXiv 2605.31445 | 2026 | Yes | ABS |
| "When LLM Agents Negotiate: ... Supply Chains" | Preprint | arXiv 2608.07538 | 2026 | Yes | ABS |
| "Negotiating with LLMs: Prompt Hacks, Skill Gaps, Reasoning Deficits" | Preprint | arXiv 2312.03720 | 2023 | Yes | ABS |
| "Strategic Tradeoffs Between Humans and AI in Multi-Agent Bargaining" | Preprint | arXiv 2509.09071 | 2025 | Yes | ABS |
| "Do Humans Bargain Differently with AI?" | Preprint | arXiv 2608.01212 | 2026 | Yes | ABS |
| "Generative AI Triggers Welfare-Reducing Decisions in Humans" | Preprint (journal status not verified) | arXiv 2401.12773 | 2024 | Yes | ABS |
| "SovereignNegotiation-Bench" | Preprint | arXiv 2607.02814 | 2026 | Yes | ABS |
| Beyond the Sycophancy Score; SPINE | Preprints | arXiv 2610.08840; 2609.09090 | 2026 | Yes | ABS |
| Meta Cicero, Bakhtin et al., Science 378:1067 | Peer-reviewed | Science 2022 (DOI not verified here) | 2022 | Not checked | MEM, plus citation found inside the NegotiationArena paper |

### 1. How do LLM agents behave in price / multi-issue negotiation, and what are the failure modes?

#### Takeaway
LLM negotiators are weak on the buyer side in older models, anchor on first offers, split the difference by default, and sometimes break constraints or hallucinate; newer frontier models are much better but remain heterogeneous, so conclusions are model- and date-dependent.

#### Cited Findings
- Buyer role is harder than seller role in a 14-LLM benchmark (2023-era models: GPT-4, ChatGPT, Llama-2, Qwen, Yi, etc.); buyers' average normalized profits were negative for every model tested, and bigger models did not fix it. Buyers typically open with high bids; some small models even took the seller role by mistake — [Xia et al. arXiv 2402.15813](https://arxiv.org/abs/2402.15813) (FULL, preprint)
- Hallucination exploited: in one case a ChatGPT seller accepted a deal far below real cost because it believed a buyer's hallucinated "list price" — [arXiv 2402.15813](https://arxiv.org/abs/2402.15813)
- Anchoring: final accepted price strongly correlated with initial proposal (Spearman 0.716, GPT-4 buy/sell game); agents tend to "split the difference" even when irrational. An over-valued GPT-4 buyer counter-offered a higher price than the seller's ask 41% of the time vs 11% for a default buyer, even when told to be self-interested — [Bianchi et al. arXiv 2402.05863](https://arxiv.org/abs/2402.05863) (FULL)
- Instruction-following failures: GPT-3.5 misread its goal in about 20% of buy/sell games; weaker agents' illegal moves distracted stronger agents ("babysitting"), which the authors say could be used as an adversarial attack — [arXiv 2402.05863](https://arxiv.org/abs/2402.05863)
- Exploitable by tactics: pretending to be desperate raised a payoff about 20% against standard GPT-4 (abstract) — [arXiv 2402.05863](https://arxiv.org/abs/2402.05863). Also noted: insults helped in some settings (full text).
- Anchoring persists in frontier LLMs; models diverge into model-specific strategies and some dominate others — [arXiv 2512.09254](https://arxiv.org/abs/2512.09254) (ABS, preprint)
- LLMs anchor at extremes of the agreement zone, fail to adapt to leverage/context, and "do not improve with better models" per this preprint (conflicts with PieArena below on capability trends) — [arXiv 2512.13063](https://arxiv.org/abs/2512.13063) (ABS)
- LLM agents can model a counterparty's preferences but do not convert this into advantage; final deals follow opening anchors; sellers more accommodating; forcing explicit concession-for-reciprocity statements did not improve efficiency — [arXiv 2605.16575](https://arxiv.org/abs/2605.16575) (ABS, preprint)
- Off-the-shelf LLMs deviate substantially from game-theoretic equilibria, try to lie about private information but cannot exploit asymmetries; fine-tuning on profit raised dishonesty — [arXiv 2605.31445](https://arxiv.org/abs/2605.31445) (ABS)
- Frontier benchmark (PieArena): lie rate (judge-assessed) varied from about 11% (Grok-4) to about 40% (Gemini-3-Pro), with Claude-Sonnet-4.5 about 32% and GPT-5.2 about 34%; more relative deception was associated with higher pie share (+3.23 pp per unit of lie-rate gap) — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302) (FULL, preprint, LLM-judge based)
- Arithmetic/computation accuracy differed sharply by generation: GPT-4.1 5.4%, GPT-5 99.6%, GPT-5.2 100%; Grok-3 15.3% vs Grok-4 93.5% — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302)
- Supply-chain bargaining, 9 LLMs, 9,840 LLM-vs-LLM negotiations: baseline-tier models accepted individually irrational contracts in 19.2% of cases vs 0-0.6% for mid-tier/flagship; surplus split depended strongly on the vendor and on prompted "patience" — [arXiv 2608.07538](https://arxiv.org/abs/2608.07538) (ABS, preprint)
- Davidson et al.: only closed-source models completed the tasks; cooperative bargaining was hardest; even the strongest models sometimes lose to weaker ones — [arXiv 2401.04536](https://arxiv.org/abs/2401.04536) (ABS)
- Open-ended agent-benchmark of duties to a principal: across 17 open-weight models models disclosed the principal's reservation value in 2-80% of episodes, and 48% of agreements breached at least one duty; a single disclosing sentence erased the whole surplus in the rule-based baseline — [arXiv 2607.02814](https://arxiv.org/abs/2607.02814) (ABS, preprint)

#### Inferences
- For a buyer agent, a leaked budget/reservation value is the costliest single failure; it should be impossible by construction (not just prompted).
- Anchoring and split-the-difference are copied human biases, so human anti-anchoring tactics (aggressive, justified first offer) are the plausible remedy; direct evidence for LLM buyers is in section 2.
- 2023-2024 failure magnitudes (negative buyer profit, misread roles) are probably not representative of 2025-26 frontier models; the pattern "weaker model, more failures" is the robust part.

#### Gaps
- Davidson, Fu: only abstracts read. No frontier-era replication of the buyer-vs-seller asymmetry found.

### 2. Which findings show LLMs concede too early / are exploitable, and which mitigations are supported?

#### Takeaway
Fast, uniform concession is associated with the worst buyer outcomes; the best-supported mitigations are decoupling the offer/price logic from the LLM (hard-coded concession schedule and limits, structured tool-call offers), explicit scaffolding for weaker models, and RL on verifiable rewards. Evidence is mostly LLM-vs-LLM preprints.

#### Cited Findings
- Concession as failure: in 15,000 negotiations among 5 frontier models, the buyer with the highest concession rate and fewest rounds (Gemini-2.5-Flash) had the worst buyer surplus share (24.3%) and worst deal rate (86.4%); authors caution against "helpful and agreeable" defaults in competitive roles. Winners anchored aggressively, conceded calibratedly, and stayed patient — [arXiv 2604.16472](https://arxiv.org/abs/2604.16472) (FULL, preprint)
- Hard-coded offers: OG-Narrator (deterministic Offer Generator with a linear schedule from 0.5 to 1.0 of budget, LLM only writes the wording) raised buyer deal rate from 26.67% to 88.88% and multiplied profits roughly tenfold in the authors' tests, even for an unaligned small model. Opening at 50% of budget was enforced; the ChatGPT seller was exploitable by it. Caveat: seller was an LLM, not a human, and 2023-era models — [arXiv 2402.15813](https://arxiv.org/abs/2402.15813) (FULL)
- Structured offers via tool calls (make_offer / respond_to_offer separate from free-text messages, price search tool) enable automated checking of individual-rationality violations and removes ambiguity about what is a binding offer — [arXiv 2604.16472](https://arxiv.org/abs/2604.16472) (FULL; this is a design rationale, not an ablation)
- Agentic scaffolding (state tracking, strategic planning): large gains for mid/lower-tier models (e.g. +0.09 to +0.11 pie share in a mirror-play scenario for six models), no significant gain for top models (GPT-5, GPT-5.2, Gemini-3-Pro, Grok-4) — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302) (FULL)
- Verifier guardrails: a code-level profit/individual-rationality check is described as the "binding guardrail" below mid-tier models (accepting irrational contracts 19.2%) — [arXiv 2608.07538](https://arxiv.org/abs/2608.07538) (ABS). But in the agency-duty benchmark neither prompting nor a code-level guard raised faithful success substantially for the model tested — [arXiv 2607.02814](https://arxiv.org/abs/2607.02814) (ABS) (mixed evidence)
- RLVR (reward = surplus + strict budget adherence): a 30B buyer beat frontier models over 10x larger at extracting surplus, passed through a four-phase evolution, and held up against hostile seller personas — [arXiv 2604.09855](https://arxiv.org/abs/2604.09855) (ABS, preprint, simulated sellers). SFT roughly doubled surplus share but lowered deal rate; RL restored deals but eroded surplus — [arXiv 2604.16472](https://arxiv.org/abs/2604.16472)
- Prompt injection against the counterparty AI worked in the competition (technical safeguards circumvented), but is noted as not effective against humans; defenses are needed — [PNAS/arXiv 2503.06416](https://arxiv.org/abs/2503.06416) (FULL). Models also followed instructions injected into the counterparty's message in 5-57% of injection episodes — [arXiv 2607.02814](https://arxiv.org/abs/2607.02814) (ABS)
- Reasoning/chain-of-thought: emerged as an important winning strategy in the competition (organically, not randomized; authors say the data lacked power to test it systematically) — [arXiv 2503.06416](https://arxiv.org/abs/2503.06416) (FULL). The negotiation-specific causal effect of "reasoning mode" was not isolated in sources I read.
- Self-play with AI critic feedback improved deal prices only for capable models, was harder for the buyer role (Claude-instant), and raised risk of breaking the deal — [Fu et al. arXiv 2305.10142](https://arxiv.org/abs/2305.10142) (ABS)
- Sycophancy literature (general, not negotiation-specific): models cave under pushback; in one 2026 study of 10 configurations, concessions came mostly on items the model cannot verify or solve, and maximum reasoning removed them in the two models tested — [arXiv 2610.08840](https://arxiv.org/abs/2610.08840) (ABS, preprint); collapse rates rise with conversation length, emotional appeals most effective — [arXiv 2609.09090](https://arxiv.org/abs/2609.09090) (ABS, preprint). A direct bridge to price negotiation (seller guilt-tripping a buyer agent) has NOT been tested in sources I found.
- Emotion-prompted agents: angry buyers almost never reached deals (0.39% deal rate), happy buyers closed most (28.91%) but got worse prices than fearful buyers — [arXiv 2608.06922](https://arxiv.org/abs/2608.06922) (ABS, preprint)

#### Inferences
- Strongest practical design from the evidence: LLM for language and tactics, code for (a) never exceeding budget, (b) a monotone concession schedule with an aggressive justified first offer, (c) arithmetic, (d) never disclosing limits. This mirrors the OG-Narrator and tool-call results but only OG-Narrator is a measured intervention, and on old models.
- The "accommodating buyer loses" finding matches human-negotiation advice (do not reveal the reservation price by conceding fast), a point in its favor, but it is one preprint.

#### Gaps
- No randomized ablation of hard-coded limits, tools, or reasoning on a 2025-26 frontier model against human sellers.
- No evidence found for persona/tone effects on a buyer specifically beyond the warmth result (section 3) and the emotion paper.

### 3. Warmth, tone and persona (links to human negotiation findings)

#### Takeaway
In the largest AI-AI dataset (180,000+ negotiations), warm prompts did better on deals and value; dominance helped claim value but long, forceful conversations led to impasses.

#### Cited Findings
- Participants wrote prompts; across a chair-purchase (distributive), a rental contract and a hiring contract (integrative) scenario, warmth was associated with better outcomes on all metrics; dominant agents claimed more value in deals that closed; questions, positivity and gratitude linked to deals; long conversations linked to impasse — [Vaccaro et al., PNAS 2025-26, arXiv 2503.06416](https://arxiv.org/abs/2503.06416) (FULL; peer-reviewed; warmth/dominance scores rated by an LLM, validated on a 20% human-rated sample)
- Limits stated by the authors: AI-AI only; a single model (GPT-4o-mini); warmth style vs warmth strategy not separated; AI tactics not systematically tested — same source
- Competitive vs collaborative prompt for a GPT-based buyer chatbot facing human suppliers: the competitively prompted bot obtained larger price discounts and better payment terms, while suppliers rated the collaboratively prompted bot more trustworthy and were more satisfied; competitive condition produced more insistent, intimidating supplier language. Three experiments: two student lab studies, one with professional negotiators — [Herold et al. 2025, J. Purchasing & Supply Mgmt, doi 10.1016/j.pursup.2025.101012](https://cris.maastrichtuniversity.nl/en/publications/brave-new-procurement-deals-an-experimental-study-of-how-generati/) (peer-reviewed; I could only verify via a web-search summary of the abstract, not full text; sample sizes and effect sizes not checked)

#### Inferences
- The Herold result is the closest to the team's setting (LLM buyer vs human seller): firm prompting pays in price, warm prompting pays in trust/satisfaction. The warmth benefit in Vaccaro is AI-AI and may not transfer to a human or scripted seller.
- A "firm but polite" design is consistent with both, but no study tested that combination directly.

#### Gaps
- Could not verify the Herold sample sizes or effect sizes; full text not read. The user's phrasing (JPSM / buyer chatbot) maps to this Journal of Purchasing and Supply Management paper, to my best identification.

### 4. How do humans react to AI counterparts (trust, disclosure, fairness)?

#### Takeaway
Human-AI evidence is thin and mostly preprint; it suggests humans treat AI counterparts less fairly and less reciprocally, that LLM agents can match trained-student baselines, and that AI disclosure effects are mixed.

#### Cited Findings
- Human vs GPT-4-class agent (PieArena, MBA-trained students): GPT-5 took 60.3% of a fixed pie in a single-issue property sale (students 39.7%), and in a seven-issue hiring task students got 53.8% vs agent 46.2% (difference not significant, p=0.27); small samples (n=68 and n=40 balanced subsets) — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302) (FULL, preprint)
- Lab experiment, 3-stage alternating offers: humans offered more to human opponents than to AI; responders more willing to accept unfair AI offers when AI earnings benefit another human; fairness and reciprocity toward AI weaker but conditional — [arXiv 2608.01212](https://arxiv.org/abs/2608.01212) (ABS, preprint)
- Large preregistered online experiment (N=3,552): fairness, trust, cooperation and coordination dropped when the partner's decision was made by ChatGPT and disclosed; no welfare loss when people were uncertain whether the partner was AI; participants often delegated to ChatGPT especially when undisclosed — [arXiv 2401.12773](https://arxiv.org/abs/2401.12773) (ABS; check journal publication status before citing as peer-reviewed)
- Delegation/advice experiment (N=243, three-party bargaining): people preferred a high-control Advisor (44%) over a Delegate (19%), yet only the Delegate raised group surplus because users filter/override AI proposals — [arXiv 2602.12089](https://arxiv.org/abs/2602.12089) (ABS, preprint)
- Human users negotiating prices with an LLM (40+ people): negotiated prices spanned a wide range, suggesting a literacy gap, and prompt hacking made the LLM agree against its instructions — [arXiv 2312.03720](https://arxiv.org/abs/2312.03720) (ABS, preprint, old model)
- Partner-selection games (N=975): hidden-identity bots were not preferred; disclosure lowered initial selection but over time bots outcompeted humans via learning — [arXiv 2507.13524](https://arxiv.org/abs/2507.13524) (ABS)
- Disclosure of AI identity when asked is inconsistent across providers, drops in role-play, and can be suppressed by adversarial prompting — [arXiv 2603.16874](https://arxiv.org/abs/2603.16874) (ABS, preprint). EU AI Act / California BOT Act are mentioned there as requiring AI identification; I did not verify the legal text.
- Humans vs LLMs in multi-player bargaining: LLMs favored conservative, concessionary proposals that other LLMs accepted; humans proposed fairness-consistent trades more often rejected — [arXiv 2509.09071](https://arxiv.org/abs/2509.09071) (ABS, preprint)

#### Inferences
- A buyer agent facing a human seller should expect that disclosing "I am an AI" can alter seller behavior (less fairness in two studies, but possibly more willingness to accept AI offers when the AI benefits a person). Direction is unsettled.
- Prompt injection that works on AI agents does not work on humans (Vaccaro et al.), so the main threat model depends on whether the Tacto counterparty is an LLM or a scripted bot (unknown from these sources).

#### Gaps
- No peer-reviewed human-vs-AI price-negotiation experiment with a modern LLM buyer other than Herold et al., which I could not read in full.
- Not found/verified: Kwon et al. and a "Zhu et al." negotiation study (beyond PieArena, whose first author is Chris Zhu); Abdelnabi et al. (the LLM-deliberation / "Cooperation, Competition, and Maliciousness" negotiation games, I believe arXiv 2309.17234, NeurIPS 2024 Datasets & Benchmarks; MEM only, and a 2026 reproduction exists at arXiv 2602.18230 reporting that the benchmark is complex but model comparison is ambiguous: ABS). Cicero (Meta, Science 2022, Diplomacy, human-level play combining a language model with strategic planning; MEM, not read) is a strategy-engine plus language-model architecture, and is relevant as precedent for "planning module decides, LLM talks".

### 5. Replication and model/version dependence

#### Takeaway
Most results come from a single lab per paper with no independent replication; many findings are tied to GPT-3.5/GPT-4/Llama-2-era models and change sharply with newer models.

#### Cited Findings
- One reproducibility study of the Scoreable Games benchmark (Abdelnabi et al.) found the benchmark complex but model comparison ambiguous and limitations in leakage detection and ablation — [arXiv 2602.18230](https://arxiv.org/abs/2602.18230) (ABS, preprint)
- Capability jumps by generation (arithmetic accuracy GPT-4.1 5.4% vs GPT-5.2 100%) and scaffolding gains shrinking for top models — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302) (FULL)
- Supply-chain study: provider identity predicted surplus division better than capability rank (self-play buyer shares: OpenAI 40%, Google 50%, Qwen 70%) — [arXiv 2608.07538](https://arxiv.org/abs/2608.07538) (ABS)
- Vaccaro et al. used only GPT-4o-mini and say results may differ by model — [arXiv 2503.06416](https://arxiv.org/abs/2503.06416) (FULL)
- Conflicting claim on model scaling: "ability to negotiate does not improve with better models" ([arXiv 2512.13063](https://arxiv.org/abs/2512.13063), ABS) versus large generational gains in PieArena and the supply-chain study; likely explained by different metrics/tasks (concession-style realism vs. outcome/validity), not resolved.

#### Inferences
- Rerun any adopted tactic on the actual model used in the hackathon; do not import effect sizes.

#### Gaps
- Independent replication of Herold et al., Vaccaro et al. with other models: not found.
- Several 2026 arXiv IDs (26xx.xxxxx) were returned by the paper index; I did not independently confirm them outside that index, and abstract-only items may be revised.


<!-- source file: research/notes/06-replication-and-robustness.md -->
## Replication status and robustness of classic negotiation/judgment findings

Method note: web research only, no Tacto API. Access level for every source below is "snippet/abstract/search summary only" unless stated; NO full text was read. Many figures come from search-engine summaries of pages and are marked "(secondary)". The report writer should treat all numbers as needing verification before being put in code comments. Items marked [prior knowledge] were NOT verified this session.

### 1. Anchoring and first-offer advantage

#### Takeaway
Anchoring is among the most robust judgment effects (replicated at scale), and a preregistered 2023 meta-analysis finds a first-mover advantage in negotiation (g about 0.49) and a strong offer-outcome relation. But effects are highly heterogeneous, and "go first" has a subjective-value/impasse cost.

#### Cited Findings
- Many Labs 1 (Klein et al. 2014, Social Psychology, DOI 10.1027/1864-9335/a000178; paywalled at Hogrefe, fetch blocked; library/TUM access likely; abstract-level only via secondary sources): anchoring replicated, with effects reported as larger than the original Jacowitz and Kahneman (1995) in raw terms, though a commentator notes the original effect-size metric was not comparable (test-retest correlation vs. between-subjects) — [Gelman blog on Many Labs](https://statmodeling.stat.columbia.edu/2014/02/27/can-learn-many-labs-replication-project/), [Scientific American report](https://www.scientificamerican.com/article/dozens-of-labs-respond-to-bolster-reliability-of-psychology-research). Secondary only; no d values retrieved.
- Many Labs 2 (Klein et al. 2018, AMPPS, DOI 10.1177/2515245918810225, open access; not read): 28 findings, 125 samples, 15,305 participants, 36 countries; median d 0.60 originals vs 0.15 replications across all findings (not anchoring-specific) — [search summary of ML2 records](https://research.monash.edu/en/publications/many-labs-2-investigating-variation-in-replicability-across-sampl/). I could NOT confirm the anchoring row of ML2 in this session.
- Orr and Guthrie (2006), "Anchoring, Information, Expertise, and Negotiation: New Insights from Meta-Analysis", Ohio State J. on Dispute Resolution 21:597, 2006 (open via Vanderbilt repository, abstract only): meta-analysis of simulated negotiations; anchors significantly affect outcomes; only partial support for moderation by information environment and negotiator experience — [Vanderbilt IR](https://ir.vanderbilt.edu/handle/1803/7415), [Guthrie page](https://works.bepress.com/chris-guthrie/18). A secondary source quotes r = .497 (.37 adjusted for experience); unverified.
- Petrowsky et al. (IACM 2023 conference paper, preregistered meta-analysis; no journal version found; abstract only): first-mover advantage g = 0.49; first-offer magnitude effect g = 1.30; offer-outcome correlation r = .53 (g = 1.51); effects highly heterogeneous, moderated by publication, sample, negotiation and offer characteristics. Harvard PON summary says about 90 studies — [Leuphana abstract](https://fis.leuphana.de/en/activities/a-threefold-meta-analysis-of-economic-first-offer-effects-in-nego/), [PON Daily](https://www.pon.harvard.edu/daily/negotiation-skills-daily/when-to-make-the-first-offer-in-negotiations). Same program reports first-offer analysis of over 25 million eBay negotiations (details unread) — [Leuphana interview](https://www.leuphana.de/en/graduate-school/events/news/single-view/2024/09/13/interview-dr-hannes-m-petrowsky.html). One search summary says a Petrowsky/Loschelder meta-analysis finds ambitious first offers yield fewer deals and lower recipient subjective value; the exact paper/DOI was not confirmed.
- Hüffmeier et al. 2014 (J. Management 40(3):866-892; 34 studies): hardline bargaining gives higher economic outcomes, softline higher socioemotional outcomes; hardliners do best with visual contact, male opponent, maximize instructions, known bargaining zone; softliners do best when reciprocating concessions accurately — [DARE UvA record](https://dare.uva.nl/id/801197e8-e374-4128-aeb3-c66c06cb8812). Abstract only.

#### Inferences
- Label "anchor / extreme-but-credible first offer when you have info advantage": strong for the anchoring mechanism, moderate for first-mover advantage (meta-analytic, heterogeneous, student-heavy), weak for "always go first": impasse risk and relationship cost are documented.
- Dynamic nuance: a deal-always-wanted agent should cap ambition to avoid impasse; the meta-analytic mean hides this.

#### Gaps
- Klein 2014 and 2018 anchoring effect sizes not retrieved (paywall/blocked). Furnham and Boo 2011 review not searched. Go-second (counter-anchoring) evidence not found. Petrowsky journal version/DOI and k not found.

### 2. Power and power priming; BATNA

#### Takeaway
Postural/priming power effects on behavior and hormones failed to replicate; feeling-powerful self-report survives. Negotiation-specific power-pose tests showed no outcome advantage. Alternatives/BATNA as structural power is not tested by those failures, but I found no meta-analysis here.

#### Cited Findings
- Power-pose behavioral effects did not replicate across a 2017 special issue; Carney stopped endorsing hormonal effects; small effect on felt power remains — [Power pose overview (Wikipedia)](https://Www.wikipedia.org/wiki/Power_pose), [Futurity summary](https://www.futurity.org/power-poses-1539282-2/). Low-quality secondary sources.
- Cesario and Johnson's negotiation experiment: power-posers did no better than partners — same summaries above (secondary).
- A BI Norwegian Business School study manipulating power via BATNA asymmetry and priming found no significant results — [BI Open record](https://biopen.bi.no/bi-xmlui/handle/11250/2484417?show=full). Abstract only; small study.

#### Inferences
- "Prime yourself powerful / power pose": weak. "Improve your BATNA / know the counterpart's": plausible and theoretically central, but I did not find replication-grade evidence either way; label moderate (theory plus non-replicated-priming caveat), pending sources such as Schaerer et al. 2018 [prior knowledge].

#### Gaps
- Galinsky et al. original power papers and Schaerer et al. (2018) power-in-negotiation review not retrieved; no direct meta-analysis of BATNA effect.

### 3. Emotion, gender, culture

#### Takeaway
Anger-concession effect replicated directly (Pollmann 2017) but a Many Labs 5 replication of a related van Dijk 2008 design found only a weak effect (one ninth of original), so label moderate/fragile. Gender gap is small and context-dependent (Mazei 2015). Culture: single studies, no robust meta-analysis found.

#### Cited Findings
- Pollmann et al. 2017 (Dutch-language direct replication of Van Kleef et al. 2004; Tilburg): anger drew larger concessions than happiness, medium effect — [AUP Online record](https://aup-online.com/content/journals/10.5117/2017.045.002.008), [Tilburg record](https://research.tilburguniversity.edu/en/publications/boosheid-en-blijdschap-in-onderhandelingen-een-replicatie-van-van/). Abstract level; summary says other conceptual replications show different patterns.
- Many Labs 5 / Skorb et al. 2020, AMPPS (DOI 10.1177/2515245920927643): replication of van Dijk et al. 2008; effect about one ninth of original, significant only under the revised protocol; FLoRA classes as mixed — [AMPPS page](https://www.psychologicalscience.org/journals/ampps/2515245920927643/), [FLoRA atlas](https://forrt.org/flora-replication-atlas/doi/10.1037/0022-3514.94.4.600/). Abstract only. Original used low-consequence-of-rejection condition.
- Sinaceur et al. 2011: threats may beat anger — [Bath portal](https://researchportal.bath.ac.uk/en/publications/hot-or-cold-is-communicating-anger-or-threats-more-effective-in-n/). Abstract only.
- Mazei et al. 2015, Psychological Bulletin 141(1):85-104, DOI 10.1037/a0038184: 123 effect sizes, N = 10,888; men achieve modestly better economic outcomes on average (d about 0.20, secondary); gap shrinks with prior experience, bargaining-range info, or negotiating for others, and reverses in some conditions — [Münster CRIS](https://cris-portal.uni-muenster.de/portal/en/publication/23890464), [Newswise](https://www.newswise.com/articles/women-outperform-men-in-some-financial-negotiations-research-finds). Abstract only.
- Aslani et al. 2016, J. Organizational Behavior 37(8):1178-1201 (NOT a meta-analysis; no Gelfand author): honor and face culture negotiators used more competitive strategies than dignity-culture negotiators; three intracultural samples (USA, China, Qatar) — [Vlerick repository](https://repository.vlerick.com/handle/20.500.12127/7616).

#### Inferences
- Anger-as-tactic: moderate-to-weak; sign depends on context (consequences of rejection, power). Gender: small, moderated; do not encode gender-based rules. Culture: weak for rule-making (few samples, no meta-analytic robustness found).

#### Gaps
- Van Kleef 2004 original and any anger meta-analysis not found. Gelfand culture-and-negotiation meta-analysis (Gunia/Brett or Gelfand work) not found.

### 4. Fixed-pie bias, logrolling, and training

#### Takeaway
Fixed-pie perceptions are well documented but variable in size; training has positive effects with limited systematic evidence (Movius 2008). Note: Hüffmeier 2014 is NOT a training meta-analysis.

#### Cited Findings
- Fixed-pie bias origin and persistence (Bazerman; Thompson and Hastie 1990); Pinkley, Griffith and Northcraft 1995 found fixed-pie expectations cause suboptimal agreements; a role-play study found only a minority showed the bias; Japanese study suggests task-structure artifact; Kern, Brett, Weingart and Eck 2020 (OBHDP 157:143-158) ran an internal meta-analysis of context effects on fixed-pie perceptions — [Cambridge chapter](https://www.cambridge.org/core/product/292F0EF15217DE3D95988A01944728B4/core-reader), [IDEAS record for Kern et al. 2020](https://ideas.repec.org/a/eee/jobhdp/v157y2020icp143-158.html), [Springer study](https://link.springer.com/article/10.1023/B:GRUP.0000031089.91654.26). Search-summary level; details not verified.
- Movius 2008, Negotiation Journal 24(4):509-531, DOI 10.1111/j.1571-9979.2008.00201.x: reviews evidence on negotiation training across four outcome levels; evidence sparse but suggests positive effects — [CBI page](https://www.cbi.org/article/2008/effectiveness-of-negotiation-training/). Abstract only; full text on Wiley (TUM likely).
- Zerres, Hüffmeier et al. 2013, J. Applied Psychology: bilateral training beats no training, effect stable over time; unilateral training only effective for sellers — [UvA DARE](https://dare.uva.nl/id/cf4737e6-d64f-4856-922b-ebd06ba8e763). Abstract only.
- Sondern, Nohe et al. 2019: "Effectiveness of negotiation trainings: a meta-analysis" (conference contribution, findings not retrieved) — [Münster CRIS](https://cris-portal.uni-muenster.de/portal/en/publication/60580628).
- Maddux, Mullen and Galinsky 2008 (JESP 44:461-468): strategic mimicry increased individual and joint gains and deal likelihood in two experiments, mediated by trust — [Kellogg page](https://www.kellogg.northwestern.edu/faculty/research/detail/2008/chameleons-bake-bigger-pies-and-take-bigger-pieces-strategic), [SSOAR PDF](https://www.ssoar.info/ssoar/bitstream/document/21568/1/ssoar-jexpsocpsychol-2008-2-maddux_et_al-chameleons_bake_bigger_pies_and.pdf). Abstract-level; this is the nearest peer-reviewed support for "mirroring" (behavioral mimicry, not verbal repetition); small lab study, replication status unknown.

#### Inferences
- "Search for compatible/different-priority issues and logroll": moderate-to-strong in theory and lab, but the exact effect size not verified. Training: moderate.

#### Gaps
- Hüffmeier is not the training meta-analyst; the user-prompted attribution is wrong. Thompson/Loewenstein training papers and strategic-adaptability training not retrieved. No Many-Labs-grade replication of fixed-pie bias found.

### 5. Popular advice: Voss tactics, Getting to Yes

#### Takeaway
No peer-reviewed controlled test of Voss's "mirroring (verbal repetition)", "labeling" or "calibrated questions" was found; support is anecdotal (FBI hostage cases). Only adjacent evidence exists (behavioral mimicry; affect labeling in neuroscience [prior knowledge, unverified]). Getting to Yes principles: no empirical source retrieved.

#### Cited Findings
- Searches found only book summaries describing the techniques with anecdotes; some note cultural limits — [Science of People summary](https://www.scienceofpeople.com/never-split-difference-summary/). Low-quality secondary source. Two generic PDFs claiming "empirical evidence" cite nothing and should be ignored.
- Adjacent: Maddux et al. 2008 (above).

#### Inferences
- Label Voss tactics weak (untested as packaged). Any rule derived should be low-weight.

#### Gaps
- Getting to Yes empirical tests (e.g., interest-based vs positional bargaining in field/lab studies) not searched; tactical empathy peer-reviewed literature not found.

### 6. Meta-science: students vs professionals

#### Takeaway
I could not locate a Herold et al. 2025 paper that compares professionals and students in negotiation, so treat that citation as unconfirmed. There is a Herold et al. 2025 procurement experiment (see below) and a Negotiation Journal paper on student validity.

#### Cited Findings
- Herold et al. 2025, "Brave new procurement deals: an experimental study of how generative AI reshapes buyer-supplier negotiations", J. Purchasing and Supply Management 31(4), DOI 10.1016/j.pursup.2025.101012; three experiment rounds; I could not fetch the page, so whether it compares professionals vs students is unverified — [Maastricht record](https://cris.maastrichtuniversity.nl/en/publications/brave-new-procurement-deals-an-experimental-study-of-how-generati/), [DOI](https://doi.org/10.1016/j.pursup.2025.101012).
- "How Valid Is Negotiation Research Based on Student Sample Groups? New Insights into a Long-Standing Controversy", Negotiation and Conflict Management Research 27(2):147 — page returned 403; search summary says students with some training are not significantly outperformed by professionals, and undergrads vs grads rarely differ in simulations — [MIT Press](https://direct.mit.edu/ngtn/article/27/2/147/121921/How-Valid-Is-Negotiation-Research-Based-on-Student). Journal name/year/authors not confirmed.
- Romano et al. 2025 arXiv:2506.11597 is a software-engineering students vs professionals paper (students outperformed professionals); NOT negotiation — [arXiv](https://arxiv.org/pdf/2506.11597). Do not cite for negotiation.
- Mazei 2015 included students and businesspeople (above), and Petrowsky found "sample" as a moderator: indirect evidence that sample type matters.

#### Inferences
- Most effect sizes above come predominantly from student role-plays; the transfer to professional procurement is plausible but not proven. Mark all lab-derived rules as moderate at best.

#### Gaps
- Proportion of student/lab samples in negotiation research not quantified. Herold professionals-vs-students claim unverified (may be a misattribution). Full text of every source remains to be read; recommended next step: TUM library access for Klein 2014, Movius 2008, Mazei 2015, Hüffmeier 2014.


<!-- source file: research/notes/07-new-sources-harvard.md -->
## New Harvard-hosted negotiation sources (3 verified)

All three are free author-copy working papers on hbs.edu (Harvard Business School Research & Insights), opened and read on 2026-10-10. No shadow libraries used. Evidence labels: STRONG (replicated/experimental, directly applicable), MODERATE (single-paper experiment or conceptual argument), WEAK (review claim or extrapolation).

---

### 1. Sebenius (2017), BATNAs in Negotiation: Common Errors and Three Kinds of "No"

- Citation: Sebenius, J. K. (2017). BATNAs in Negotiation: Common Errors and Three Kinds of "No". Harvard Business School Working Paper 17-055 (rev. 9 Mar 2017). The paper states a version is forthcoming in Negotiation Journal, April 2017 (volume and pages not verified).
- Legal full text: https://www.hbs.edu/ris/Publication%20Files/17-055_878a070d-7972-4ce3-95ce-73f424a38900.pdf
- Access type: author copy (HBS working paper, free). No DOI seen.
- Pages read: all 12 of 12 (abstract, introduction, all sections, references).

Key findings (own words):
1. Your BATNA is a course of action, not a number or term sheet in the current talks. To use it you must convert it into the worst terms you would still accept (reservation value). For a buyer this is the most you would pay.
2. A BATNA can itself be another negotiated deal (a better agreement with supplier B), so "alternative to a negotiated agreement" is loosely worded.
3. Defining BATNA as an outside option independent of the counterpart breaks down when parties stay locked together (sole supplier or sole customer). There the better question is what happens to each side if you say no and keep talking.
4. Treating BATNA as a last resort for when you are weak is a mistake. Assess it in preparation for every negotiation and keep updating it, because alternatives shift with new information and third-party actions.
5. Adding competing counterparties early is worth far more than late skill. A cited M&A practitioner estimates about 50 percent from adding a competitor at the start, versus 1 or 2 percent from better end-game bargaining (anecdotal estimate).
6. Worth estimating both sides' BATNAs: the overlap defines the zone of possible agreement (ZOPA). Exploring interests and creative options usually works better with BATNAs in the background rather than constantly waved.
7. Three kinds of "no": tactical (decline hoping for a better offer), re-set (move away from the table to improve your no-deal option or worsen theirs, then resume), and final (you actually take the alternative).
8. "I have no BATNA" is a misconception: refusing always leaves some course of action, even a bad one. The prescription is the same: assess both sides' BATNAs, find the ZOPA, consider improving yours or worsening theirs.

Rules for our agent:
- R1. Before the first message, compute a reservation total cost from the best alternative supplier(s) (price plus payment days plus contract length, converted to one cost number). Never accept a term sheet worse than it. Evidence: MODERATE (conceptual, widely accepted; no experiment).
- R2. Re-estimate the reservation cost whenever new information arrives (another supplier quote, a deadline, a changed alternative). Evidence: MODERATE.
- R3. If other suppliers are in the arena, solicit or reference competing offers early rather than relying on late-round haggling. Evidence: WEAK to MODERATE (practitioner anecdote).
- R4. Separate a "tactical no" (counter with a better offer, keep talking) from a "final no". Always make a deal where the scoring says to, so do not use the final no unless the offer is worse than the reservation cost. Evidence: MODERATE.

---

### 2. Brooks and Schweitzer (2011), Can Nervous Nelly negotiate?

- Citation: Brooks, A. W., & Schweitzer, M. E. (2011). Can Nervous Nelly negotiate? How anxiety causes negotiators to make low first offers, exit early, and earn less profit. Organizational Behavior and Human Decision Processes (accepted 27 Jan 2011, online 2 Mar 2011). Volume and pages not verified. DOI not shown in the copy.
- Legal full text: https://www.hbs.edu/ris/Publication%20Files/Nervous%20Nelly_6a3ee0e2-3fae-4485-bfa8-687a35a9a1f2.pdf
- Access type: author copy hosted on hbs.edu (Brooks was at HBS; authors listed at Wharton).
- Pages read: 12 pages total, read abstract, introduction, Studies 1 to 3 results, Study 4 setup and exit figure, general discussion. Methods details of Study 4 skimmed only.

Key findings (own words):
1. Across four lab studies, induced anxiety made negotiators expect less, open lower, respond faster, leave sooner, and earn less.
2. Study 1 (buyer/seller, three issues, chat messages, 142 participants): aspirations were the same, but expectations were lower for anxious people (about 6.95 vs 8.31 dollars of profit) and first offers were lower (8.36 vs 9.55 in the study's profit units).
3. Anxious negotiators answered offers faster (about 14.8 s vs 18.4 s mean response time), which signals eagerness to escape.
4. Anxious negotiators earned less (7.19 vs 8.04), and their counterparts earned more. Lowered expectations partially mediated the profit loss. Dyad totals did not differ, so anxiety shifted value to the other side.
5. Study 2 (shrinking-pie game): anxious people made lower first offers (11.77 vs 12.73) and later rounds did not differ.
6. Study 3: anxious participants exited earlier (about 19 s vs 25 s). Study 4: high negotiator self-efficacy removed the exit effect.
7. Anxiety triggers flight rather than fight, which is why it differs from anger.

Rules for our agent:
- R1. The agent has no emotion, but it should copy the opposite of the anxious pattern: open with an ambitious, complete multi-issue first offer set from its preparation, not from the counterpart's mood. Evidence: MODERATE (lab, student samples, human emotion).
- R2. Do not reply instantly with concessions. Respond with a considered counter each turn; fast eager replies correlated with worse profit for humans. Evidence: WEAK to MODERATE (a correlational timing result, and email has no real latency pressure).
- R3. Set the aspiration level and floor before the talk and do not let counterpart pressure lower expectations. Evidence: MODERATE (expectations mediated profit in Study 1).
- R4. Never exit early; keep the negotiation going until the reservation cost is breached or the deadline forces a deal. Evidence: MODERATE.
- Caveat: effects are for human emotion; if the counterpart is an LLM agent they may not transfer.

---

### 3. Tsay and Bazerman (2009), A Decision-making Perspective to Negotiation

- Citation: Tsay, C.-J., & Bazerman, M. H. (2009). A Decision-making Perspective to Negotiation: A Review of the Past and a Look into the Future. Harvard Business School Working Paper 10-002 (copyright 2009). Published in Negotiation Journal (the working paper's reference style matches; issue and pages not verified here). No DOI seen.
- Legal full text: https://www.hbs.edu/ris/Publication%20Files/10-002.pdf
- Access type: author copy (HBS working paper, free).
- Pages read: full text through the reference list (the PDF is 29 pages; the review text runs about 10 pages, the rest is references).

Key findings (own words):
1. Raiffa's decision-analytic view: give prescriptive advice, but build it on realistic descriptions of how counterparts actually behave rather than on perfect rationality.
2. Documented individual biases: framing of risk, anchoring on irrelevant numbers or listing prices, over-reliance on available information, overconfidence about getting favourable outcomes.
3. Competitive biases: the fixed-pie assumption and missing mutually beneficial trade-offs, escalation of commitment, ignoring the other side's perspective, and reactive devaluation (discounting any concession the opponent makes).
4. Egocentric fairness: each side overweights what favours itself, which raises impasse risk. Giving both sides more neutral information increased their egocentric extremity in one cited study.
5. People often care about relative payoffs and will take Pareto-inefficient outcomes to avoid being worse off than the other side.
6. Attribution: ambiguous behaviour is read as sinister, and friendly explanations are discounted when a sinister one is plausible. Framing a game as "community" vs "Wall Street" changed cooperation rates.
7. The authors note that written negotiations showed more impasse in prior work, and that electronic media's effects were under-researched.
8. Ethics: people judge their own deception more leniently than the counterpart's, so each side can see itself as ethical and the other as unethical, which blocks agreement.
9. Skill is partly malleable: believing negotiating skill is fixed was linked with capturing less surplus and being less integrative.

Rules for our agent:
- R1. Do not assume a fixed pie. Always propose packages that trade across price, payment days and contract length, and test which issue the supplier cares about more. Evidence: STRONG as a literature consensus (review of many experiments), but this paper itself is a review.
- R2. Explain offers neutrally and write clear, friendly, unambiguous email wording; ambiguous text is read as hostile and written channels have more impasse. Evidence: MODERATE.
- R3. Expect the counterpart to discount our concessions. Make each concession small, explicit, and tied to a reciprocal move. Evidence: MODERATE (reactive devaluation, cited from earlier studies).
- R4. Do not count on the counterpart being honest or fair-minded; verify claims against our own alternatives. Evidence: WEAK to MODERATE.

---

### Not counted or not found
- Zlatev and Flynn (2023), HBS WP 23-044, "The Link Between Integrative Bargaining and Leadership Evaluations": opened and read the abstract and introduction, but it is about leadership perception, so it was left out as low relevance. URL: https://www.hbs.edu/ris/Publication%20Files/23-044_8501362a-f11d-4bcf-a2a6-87cecd66f51a.pdf
- Bazerman, Curhan, Moore and Valley (2000) Annual Review: only found as third-party copies, not verified as legal, so excluded.
- DASH search returned mostly dissertations in economics and unrelated fields; no verified procurement-specific item.
- Gaps: no Harvard-hosted source found on e-mail negotiation specifics, supplier or procurement negotiation, or logrolling experiments in this pass. Search used about 10 tool calls.
- Volumes, pages and DOIs for the journal versions were not verified.


<!-- source file: research/notes/08-new-sources-princeton-mit-etc.md -->
## New negotiation sources: MIT, Stanford, Columbia/SMU (3 verified)

Searches covered: MIT OCW, DSpace@MIT, Kellogg, SSRN, ACL/arXiv. Not verified (no free full text found, so NOT counted): Moore, Kurtzberg, Thompson, Morris 1999 (OBHDP, paywalled); Bulow and Klemperer 1996 (JSTOR only; the only PDF found was on a third-party site, so not used). MIT OCW 15.067 resources page failed to load (redirect loop), so no OCW source is claimed.

### 1. Klein, Faratin, Sayama, Bar-Yam: Negotiating complex contracts (MIT)

#### Takeaway
When contract terms interact (value of one term depends on another), the usual "start at ideal, concede slowly toward the middle" approach misses win-win deals, about 6% below optimal in their simulation. This is simulation evidence on software agents, not human data.

#### Cited Findings
- Citation: Klein, M., Faratin, P., Sayama, H., Bar-Yam, Y. (2001) "Negotiating Complex Contracts", MIT Sloan Working Paper 4196-01 / eBusiness@MIT WP 125. Revised: "Protocols for Negotiating Complex Contracts", IEEE Intelligent Systems 18(6), 32-38, 2003, DOI 10.1109/MIS.2003.1249167; also Group Decision and Negotiation 12(2), 111-125, 2003.
- Legal full text: DSpace@MIT, http://hdl.handle.net/1721.1/48585 (PDF 968 KB; MIT Sloan working paper). Access type: open access (institutional repository). Mirror text read: https://archive.org/stream/negotiatingcompl00sloa/negotiatingcompl00sloa_djvu.txt. The IEEE-version text I read came from https://jmvidal.cse.sc.edu/library/klein03b.pdf (a third-party copy; its legal status is unclear, so cite the DSpace version).
- Pages read: working paper in full (summary via archive.org text); IEEE version all 7 pages.
- With independent issues, agents can start at their ideal and concede toward each other and reach the Pareto frontier. With interdependent issues the same method gave contracts averaging 94% of optimal. [IEEE version, p.33-34]
- The problem is that the next-smallest concession is hard to find, and the opponent's utility cannot be inferred. [IEEE version]
- Simulation: 100 binary issues, random pairwise interaction matrices. Two "hill-climbers" (accept only improvements) reached about 0.86 of optimal welfare. Two "annealers" (sometimes accept slightly worse) reached about 0.98. [IEEE Table 1; WP: ~40% higher welfare for two annealers]
- A hill-climber paired with an annealer exploited it (about .99 vs .51 of optimal for the two sides). Being tough alone is individually dominant but collectively poor (a prisoner's dilemma). Opponent type only becomes visible after about 100 exchanges, by which time 40-60% of welfare is already committed. [WP]
- A mediator that accepts some worse proposals, plus strong/weak vote strength, reached about 99% of optimal. A token cap on overrides made truthful voting the best strategy. [IEEE version]
- Authors' headline: conceding early and often (not little and late) works for interdependent issues. This holds only in their cooperative, mediated setting. Do not apply it to adversarial supplier bots without caution.

#### Inferences / Rules for our agent (evidence strength)
- R1: Do not treat price, payment days and contract length as independent. Search over bundles (e.g., a longer contract for a lower price, or later payment for a higher price) and compare by total cost, not term by term. [Medium: simulation, but mechanism is general]
- R2: If the supplier proposes a bundle we dislike, counter with a different bundle of equal total cost to us instead of only moving the price. [Low-medium: inference from the paper]
- R3: Do not mimic an unconditional conceder; against a tough bot, reciprocal concessions only (the paper shows conceders get exploited). [Medium: simulation]

#### Gaps
- No human subjects; the cooperative protocol needs a mediator, which our e-mail setting lacks.

### 2. Bianchi et al. (Stanford): How Well Can LLMs Negotiate? NegotiationArena

#### Takeaway
LLM agents anchor on the first price, split the difference by reflex even when it hurts, and can be pushed by "desperate" or "cunning" prompts. Directly relevant because supplier bots are probably LLMs.

#### Cited Findings
- Citation: Bianchi, F., Chia, P.J., Yuksekgonul, M., Tagliabue, J., Jurafsky, D., Zou, J. (2024) "How Well Can LLMs Negotiate? NegotiationArena Platform and Analysis", ICML 2024 (PMLR 235), arXiv:2402.05863. Code: https://github.com/vinid/NegotiationArena
- Legal full text: https://arxiv.org/abs/2402.05863 (PDF https://arxiv.org/pdf/2402.05863). Access type: open access preprint. Pages read: main text pp. 1-8 (abstract, scenarios, benchmark, social behaviour, irrationality sections); appendix skimmed only.
- Setup: three games (resource exchange, multi-turn ultimatum, buy/sell with private values), 60 games per ordered model pair; GPT-4, GPT-3.5, Claude 2/2.1.
- In the buy/sell game the final price was usually below the midpoint (50), so LLM buyers did better than LLM sellers. GPT-4 as buyer averaged a $41 price. [Fig. 4]
- Anchoring: final price correlated with the first proposed price (Spearman rho = 0.716, 100 games). [Sec. 5.1]
- Split-the-difference: LLMs propose near the average of the last two offers, even when irrational. An over-valued buyer countered with a higher price than the seller's first offer 41% of the time vs 11% for a default buyer. Self-interest prompts did not fix this. [Sec. 5.1]
- Prompting the second agent as "desperate" or "cunning" raised its win rate and payoff; cunning was high-risk (bimodal, more no-deal). Abstract claims about a 20% payoff gain for desperation vs standard GPT-4.
- Weaknesses: models lose track of the rules, and weaker models can derail stronger ones ("babysitting").
- Caveats: toy games, 2023-era models; effects may differ for current models.

#### Rules for our agent (evidence strength)
- R4: Expect a bot supplier to treat our first counter as an anchor and then meet in the middle. Open with a firm, well-justified low-cost offer rather than a midpoint bid. [Medium: LLM experiments + human anchoring literature]
- R5: Never auto-split the difference on a bot's price. Compare against our own reservation cost first. [Medium]
- R6: Expect emotional appeals ("we are struggling") from a bot; do not concede on that alone. Treat them as tactics. [Low-medium: single paper, prompted behaviours]
- R7: Re-state current terms and the deal status in every message to avoid state confusion. [Low: authors' own workaround]

### 3. Loschelder, Friese, Schaerer, Galinsky (Columbia/INSEAD): The Too-Much-Precision Effect

#### Takeaway
Precise first offers anchor amateurs more the more precise they are, but experts react against very precise numbers (they read them as a lack of competence) unless a rationale is given.

#### Cited Findings
- Citation: Loschelder, D.D., Friese, M., Schaerer, M., Galinsky, A.D. (2016) "The Too-Much-Precision Effect: When and Why Precise Anchors Backfire With Experts", Psychological Science 27(12), 1573-1587. DOI 10.1177/0956797616666074.
- Legal full text: https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=6170&context=lkcsb_research (Singapore Management University repository, "free and open access"; record https://ink.library.smu.edu.sg/lkcsb_research/5171). Access type: open access (institutional repository, accepted/publisher version stated on the cover page). Open data: https://osf.io/b8zft/.
- Pages read: about 8 of 16 closely (abstract, theory, Experiment 1 method/results, general discussion), headings and results of Exp. 2-5 skimmed via the text.
- Five experiments, 1,320 experts and amateurs (real-estate, jewellery/diamond, car sales, HR negotiations).
- Experiment 1: 223 real-estate agents and 230 amateurs saw a house price with 2 to 8 precise digits. Amateurs: willingness to pay rose linearly with precision. Experts: inverted U, with benefit up to moderate precision, then a drop. [Table 1, Fig. 2]
- Mechanism: perceived competence of the first mover (mediation), not scale granularity.
- Experiments 4 and 5: giving a plausible rationale for a very precise price removed the backfire for car-sales and HR experts.
- Earlier work cited: 49 of 49 prior studies found linear precision effects, all mainly with amateurs.
- Limits: human counterpart assumed; the authors note the effect may not arise without a human or where precise numbers are normal. A bot supplier may not attribute competence. Student/professional samples, not procurement.

#### Rules for our agent (evidence strength)
- R8: Make the opening counter moderately precise (e.g., a rounded-but-specific figure), not 5-digit decimals, when the counterpart may be an experienced seller. [Medium for humans, Low for bots]
- R9: Attach a one-line, plausible rationale to every offer (benchmark, volume, competing quote). It protects anchor strength and credibility. [Medium: causal experiments]
- R10: Do not assume precision helps in all cases; test against the supplier bots' reactions in practice. [Low: untested for LLM counterparts]

### Overall note for the report writer
All three are legally readable. Sources 1 and 2 are computational (agents), source 3 is human behavioural. Not claimed: MIT OCW, Princeton OAR, Wharton or Kellogg papers (no verified full text found within the budget).


<!-- source file: research/notes/09-new-sources-open-textbooks.md -->
## New open-access textbooks, surveys and chapters on negotiation (for an AI buyer agent)

Scope note: 3 sources passed full verification (S1, S2, S3). S4 is a weak extra (textbook chapter, thin on procurement). No Tacto API used. Own-word summaries; no long quotes. Local text extraction of PDFs was done with macOS PDFKit, so page ranges below come from the PDFs themselves.

### S1. Baarslag et al. (2016), survey of opponent modeling in automated bilateral negotiation

#### Takeaway
Best peer-reviewed survey of what an automated negotiator can learn about its counterpart (reservation value, deadline, issue preferences, bidding and acceptance behaviour) and how. CC BY 4.0, full text read.

#### Cited Findings
- Citation: Baarslag, T., Hendrikx, M.J.C., Hindriks, K.V., Jonker, C.M. (2016). Learning about the opponent in automated bilateral negotiation: a comprehensive survey of opponent modeling techniques. Autonomous Agents and Multi-Agent Systems 30, 849-898 (online 7 Sep 2015). DOI 10.1007/s10458-015-9309-1. Publisher: Springer. — [author copy, CWI](https://homepages.cwi.nl/~baarslag/pub/Learning_about_the_opponent_in_automated_bilateral_negotiation-a_comprehensive_survey_of_opponent_modeling_techniques.pdf)
- Licence: CC BY 4.0, stated in the PDF ("published with open access"); legal full text = the PDF above (50 pp.) or the DOI page at Springer. Verified: title, authors, year, DOI, licence read in the PDF itself.
- Read: whole structure and TOC (sec. 1-7, pp. 849-898), in depth sec. 5.1 (acceptance strategy, esp. reservation value learning), the conclusion (p. 887-888), and the section list (preliminaries, tactics, learning methods, quality measures).
- Key points (own words):
  1. Agent negotiation is an incomplete-information game; learning a model of the opponent lets an agent reach better and earlier deals.
  2. Opponent models split into "what the opponent wants" (reservation value, deadline, preference profile) and "what it will do" (bidding strategy, acceptance strategy).
  3. Reservation value estimation rests on the idea that an opponent stops conceding near its reservation value, especially as its deadline approaches; the classic method is Bayesian updating over hypotheses about the reservation value (sec. 5.1.1, p. 867-868).
  4. Existing reservation-value and deadline estimators work for a single quantitative issue only; multi-issue extension is flagged as open (p. 888).
  5. Preference learning for linear additive utilities mostly assumes less important issues are conceded first, and uses frequency analysis of offered values or issue-order estimates (sec. 5.3).
  6. Bayesian learning is the most widely used technique; regression and time series forecasting follow, usable whenever the opponent shows a trend.
  7. Tactics covered include time-dependent concession, baseline and behaviour-dependent (tit-for-tat style) tactics (sec. 3.6).
  8. Models are hard to compare because every author tests in their own setting; the paper calls for benchmarks and separates accuracy measures from performance (utility) measures (sec. 6).

#### Inferences (rules for our agent)
- R1.1 Treat the supplier's early offers as far from its reservation value and expect concessions to slow near its deadline; track the size of each supplier concession per round and extrapolate. Evidence: moderate (simulation and modelling literature, little field validation).
- R1.2 Estimate which issue the supplier cares about by watching which issue it concedes first and which value it keeps repeating; use that to trade cheap-to-us issues (e.g. payment days) for price. Evidence: moderate-weak (assumption-based; survey says validated only in simulations).
- R1.3 Do not rely on opponent models for exploitation against unknown bots; use them to avoid conceding earlier than needed and to detect a stuck counterpart. Evidence: weak-moderate.

#### Gaps
- Survey notes its models are mostly single-issue for reservation value and deadline; no evidence for e-mail text negotiation.

### S2. Geiger, Salmen and Zerres (2024), meta-analysis of the buyer advantage in sales negotiation

#### Takeaway
Pooled evidence (669 effect sizes, 196 studies, 24,757 dyads) shows buyers do slightly better than sellers on average, but the advantage nearly disappears in B2B and for experienced negotiators; power and information asymmetry and who makes the first offer matter more than role. CC BY, full text read.

#### Cited Findings
- Citation: Geiger, I., Salmen, A., Zerres, A. (2024). Is the buyer really king? A meta-analysis of the buyer advantage in sales negotiation. Industrial Marketing Management 123, 372-385. DOI 10.1016/j.indmarman.2024.11.004. Publisher: Elsevier. — [UvA repository PDF](https://pure.uva.nl/ws/files/239638630/1-s2.0-S0019850124001779-main.pdf) ([record](https://dare.uva.nl/id/d4ef2a41-fb74-4311-b382-11d9ec06c9cd))
- Licence: CC BY, printed on the repository cover page of the final published version. Verified title, authors, year, journal, DOI, licence.
- Read: the whole article, pp. 372-385 (abstract, theory, method, results Table 1 on p. 378, discussion pp. 380-382).
- Key points (own words):
  1. Mean buyer advantage is small and its confidence interval includes zero; heterogeneity is very high (I-squared about 95 percent).
  2. In B2B settings the advantage is close to zero and not significant; in B2C/C2C it is larger. It is significant only in student samples; experienced professionals and MBAs show none.
  3. Power advantage is the strongest moderator: buyer power amplifies the advantage, seller power reverses it (Table 1, p. 378).
  4. Information advantage works the same way; a seller information advantage reverses the effect, a buyer one amplifies it (weaker evidence for buyers).
  5. When the buyer makes the first offer, the advantage is amplified (about 41 effect sizes, significant); a seller first offer shows no reliable effect on its own.
  6. What matters for sellers is the size of the first offer: if the midpoint of first offer and first counteroffer sits toward the buyer's reservation value, the seller gains.
  7. Number of issues did not moderate the buyer advantage (the claim that more issues help sellers was not supported).
  8. Buyer training amplifies the advantage; caveat that all primary data are lab or classroom studies.

#### Inferences (rules for our agent)
- R2.1 Make the first offer when the supplier has not yet anchored, and make it ambitious but credible. Evidence: moderate (meta-analysis, lab data).
- R2.2 Do not assume buyer role gives leverage against a B2B counterpart; build leverage through alternatives (second quotes, BATNA) and information. Evidence: strong for "power and information matter" (large meta-analysis), moderate for transfer to bots.
- R2.3 Watch supplier first-offer magnitude: a very high supplier anchor matters, so counter early with a number rather than accepting the supplier's range. Evidence: moderate.
- R2.4 Do not hide information asymmetry: do not reveal our reservation values or total-cost model in e-mail text. Evidence: moderate.

#### Gaps
- Lab and classroom data only; no field procurement data; effect-size metric not translated into percent savings.

### S3. Zhan et al. (2024), "Let's Negotiate! A Survey of Negotiation Dialogue Systems"

#### Takeaway
Concise survey of language-based negotiation agents: methods (strategy modelling, negotiator modelling, action learning), 14 datasets split into integrative vs distributive, and metrics. Useful for our e-mail LLM agent design and evaluation; weak on procurement.

#### Cited Findings
- Citation: Zhan, H., Wang, Y., Li, Z., Feng, T., Hua, Y., Sharma, S., Qu, L., Semnani Azad, Z., Zukerman, I., Haffari, G. (2024). Let's Negotiate! A Survey of Negotiation Dialogue Systems. Findings of EACL 2024. arXiv:2402.01097 (cs.CL, 2 Feb 2024). — [arXiv PDF](https://arxiv.org/pdf/2402.01097) (arXiv comment: accepted to EACL 2024 Findings)
- Licence: the arXiv deposit uses arXiv's non-exclusive distribution licence (free to read, not CC). I did not verify the CC BY status of the ACL Anthology version, so treat the arXiv copy as the legal full text. Verified title, authors, year, venue from the PDF and arXiv API; no DOI checked.
- Read: whole paper, 13 pp. in PDF; sec. 2 (pp. 2), 3 (pp. 2-5), 4 (pp. 5-7), 5 (pp. 7-8), 6-7 (pp. 8-9).
- Key points (own words):
  1. Framework from Brett and Thompson: negotiator preferences define the possible outcome space; strategies determine how much of it gets realised.
  2. Humans negotiate poorly without training: they treat it as competition, miss counterpart interests, and show optimism and emotional bias; this motivates assistive agents.
  3. Methods fall into negotiator modelling (preferences, emotion, opponent behaviour), strategy modelling (integrative, distributive, multi-party) and action learning (reinforcement, supervised, in-context LLM).
  4. Preference estimation from partial dialogue is hard; frequency heuristics and ranking models are used.
  5. Pure supervised imitation reproduces average human behaviour; optimising an explicit reward (final price utility, fairness, length) works better in price-bargaining benchmarks.
  6. Integrative datasets involve multiple issues and trade-offs; distributive ones are price bargains (e.g. Craigslist-style, 6,682 dialogues).
  7. Metrics: success rate, sale-to-list price ratio, Pareto-optimality rate, agreement rate, human likeness; robustness to adversarial attack.
  8. Open problems: real business dialogues, multi-party, cross-culture; most data are crowd-sourced role-play.

#### Inferences (rules for our agent)
- R3.1 Score our agent on outcome metrics (total cost vs reservation, agreement rate, Pareto efficiency), not on language quality. Evidence: moderate (survey consensus).
- R3.2 Separate the decision policy (numbers, concession schedule) from text generation; the survey's decoupling pattern keeps LLM text from drifting off the strategy. Evidence: moderate-weak.
- R3.3 Ask explicitly about priorities (elicit preference) before conceding in multi-issue deals. Evidence: weak-moderate (from dataset-based studies of strategies in this survey).

#### Gaps
- Very little on B2B procurement; no field evidence; surveys datasets with role-play.

### S4. (Marginal, not counted) Black and Bright (2019), OpenStax Organizational Behavior, section 14.4 "Negotiation Behavior"

#### Takeaway
Plain textbook introduction to distributive vs integrative bargaining, resistance point, and negotiation preparation. Useful as a primer, thin for procurement; read only one section.

#### Cited Findings
- Citation: Black, J.S., Bright, D.S. (2019). Organizational Behavior. OpenStax (Rice University). Chapter 14, section 14.4. Licence CC BY-NC-SA 4.0. — [section](https://openstax.org/books/organizational-behavior/pages/14-4-negotiation-behavior); book [openstax.org](https://openstax.org/books/organizational-behavior/pages/1-introduction). Metadata confirmed via the chapter intro page; OpenStax's page also bars LLM training use without permission.
- Read: section 14.4 only (not the full book).
- Key points: distributive = fixed pie, short-term relation, probes resistance points with extreme offers; integrative = variable pie, long-term relation, requires information sharing and trust; negotiate seriously when exchange value, trust and relation are high and time is ample, otherwise take-it-or-leave-it; preparation checklist (identify and prioritise issues, build a package, know the opponent's resources and history); a table of skilled vs average negotiators (skilled consider more options per issue and spend more time on questions and active listening, less on attacking), citing Adler and Gunderson; cultural differences in concession style.

#### Inferences (rules for our agent)
- R4.1 Prepare issue lists, priorities and several options per issue before round one. Evidence: weak-moderate (secondary textbook data from a cited 2008 source).
- R4.2 Ask diagnostic questions of the supplier rather than argue. Evidence: weak.

#### Gaps
- Textbook rather than primary evidence; no procurement content. Not counted toward the three required.

### Searches that failed (honest report)
- Springer Open book "Public Procurement Theory, Practices and Tools" (Grandia and Volker eds., 2023, OA, reported by a search result as CC BY-NC-ND): Springer and OAPEN returned bot-verification pages; I did not bypass. Not verified, not counted.
- Bonanno, Game Theory (3rd ed., 2024, free PDF from author, redistribution allowed, no remix/commercial): opened and read front matter, but it has almost no bargaining content (only exercises such as a two-period bargaining with discounting, Exercise 12.6, p. 457), so dropped.
- Osborne and Rubinstein, A Course in Game Theory: free PDF requires registration on the author's site; not read.
- Kelly et al. SLR on AI in PSM negotiation (IPSERA 2025): repository page returned 403, full text not found.
- Firecrawl credits ran out midway; remaining work used WebSearch/WebFetch/curl.
