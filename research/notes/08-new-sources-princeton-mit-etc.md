# New negotiation sources: MIT, Stanford, Columbia/SMU (3 verified)

Searches covered: MIT OCW, DSpace@MIT, Kellogg, SSRN, ACL/arXiv. Not verified (no free full text found, so NOT counted): Moore, Kurtzberg, Thompson, Morris 1999 (OBHDP, paywalled); Bulow and Klemperer 1996 (JSTOR only; the only PDF found was on a third-party site, so not used). MIT OCW 15.067 resources page failed to load (redirect loop), so no OCW source is claimed.

## 1. Klein, Faratin, Sayama, Bar-Yam: Negotiating complex contracts (MIT)

### Takeaway
When contract terms interact (value of one term depends on another), the usual "start at ideal, concede slowly toward the middle" approach misses win-win deals, about 6% below optimal in their simulation. This is simulation evidence on software agents, not human data.

### Cited Findings
- Citation: Klein, M., Faratin, P., Sayama, H., Bar-Yam, Y. (2001) "Negotiating Complex Contracts", MIT Sloan Working Paper 4196-01 / eBusiness@MIT WP 125. Revised: "Protocols for Negotiating Complex Contracts", IEEE Intelligent Systems 18(6), 32-38, 2003, DOI 10.1109/MIS.2003.1249167; also Group Decision and Negotiation 12(2), 111-125, 2003.
- Legal full text: DSpace@MIT, http://hdl.handle.net/1721.1/48585 (PDF 968 KB; MIT Sloan working paper). Access type: open access (institutional repository). Mirror text read: https://archive.org/stream/negotiatingcompl00sloa/negotiatingcompl00sloa_djvu.txt. The IEEE-version text I read came from https://jmvidal.cse.sc.edu/library/klein03b.pdf (a third-party copy; its legal status is unclear, so cite the DSpace version).
- Pages read: working paper in full (summary via archive.org text); IEEE version all 7 pages.
- With independent issues, agents can start at their ideal and concede toward each other and reach the Pareto frontier. With interdependent issues the same method gave contracts averaging 94% of optimal. [IEEE version, p.33-34]
- The problem is that the next-smallest concession is hard to find, and the opponent's utility cannot be inferred. [IEEE version]
- Simulation: 100 binary issues, random pairwise interaction matrices. Two "hill-climbers" (accept only improvements) reached about 0.86 of optimal welfare. Two "annealers" (sometimes accept slightly worse) reached about 0.98. [IEEE Table 1; WP: ~40% higher welfare for two annealers]
- A hill-climber paired with an annealer exploited it (about .99 vs .51 of optimal for the two sides). Being tough alone is individually dominant but collectively poor (a prisoner's dilemma). Opponent type only becomes visible after about 100 exchanges, by which time 40-60% of welfare is already committed. [WP]
- A mediator that accepts some worse proposals, plus strong/weak vote strength, reached about 99% of optimal. A token cap on overrides made truthful voting the best strategy. [IEEE version]
- Authors' headline: conceding early and often (not little and late) works for interdependent issues. This holds only in their cooperative, mediated setting. Do not apply it to adversarial supplier bots without caution.

### Inferences / Rules for our agent (evidence strength)
- R1: Do not treat price, payment days and contract length as independent. Search over bundles (e.g., a longer contract for a lower price, or later payment for a higher price) and compare by total cost, not term by term. [Medium: simulation, but mechanism is general]
- R2: If the supplier proposes a bundle we dislike, counter with a different bundle of equal total cost to us instead of only moving the price. [Low-medium: inference from the paper]
- R3: Do not mimic an unconditional conceder; against a tough bot, reciprocal concessions only (the paper shows conceders get exploited). [Medium: simulation]

### Gaps
- No human subjects; the cooperative protocol needs a mediator, which our e-mail setting lacks.

## 2. Bianchi et al. (Stanford): How Well Can LLMs Negotiate? NegotiationArena

### Takeaway
LLM agents anchor on the first price, split the difference by reflex even when it hurts, and can be pushed by "desperate" or "cunning" prompts. Directly relevant because supplier bots are probably LLMs.

### Cited Findings
- Citation: Bianchi, F., Chia, P.J., Yuksekgonul, M., Tagliabue, J., Jurafsky, D., Zou, J. (2024) "How Well Can LLMs Negotiate? NegotiationArena Platform and Analysis", ICML 2024 (PMLR 235), arXiv:2402.05863. Code: https://github.com/vinid/NegotiationArena
- Legal full text: https://arxiv.org/abs/2402.05863 (PDF https://arxiv.org/pdf/2402.05863). Access type: open access preprint. Pages read: main text pp. 1-8 (abstract, scenarios, benchmark, social behaviour, irrationality sections); appendix skimmed only.
- Setup: three games (resource exchange, multi-turn ultimatum, buy/sell with private values), 60 games per ordered model pair; GPT-4, GPT-3.5, Claude 2/2.1.
- In the buy/sell game the final price was usually below the midpoint (50), so LLM buyers did better than LLM sellers. GPT-4 as buyer averaged a $41 price. [Fig. 4]
- Anchoring: final price correlated with the first proposed price (Spearman rho = 0.716, 100 games). [Sec. 5.1]
- Split-the-difference: LLMs propose near the average of the last two offers, even when irrational. An over-valued buyer countered with a higher price than the seller's first offer 41% of the time vs 11% for a default buyer. Self-interest prompts did not fix this. [Sec. 5.1]
- Prompting the second agent as "desperate" or "cunning" raised its win rate and payoff; cunning was high-risk (bimodal, more no-deal). Abstract claims about a 20% payoff gain for desperation vs standard GPT-4.
- Weaknesses: models lose track of the rules, and weaker models can derail stronger ones ("babysitting").
- Caveats: toy games, 2023-era models; effects may differ for current models.

### Rules for our agent (evidence strength)
- R4: Expect a bot supplier to treat our first counter as an anchor and then meet in the middle. Open with a firm, well-justified low-cost offer rather than a midpoint bid. [Medium: LLM experiments + human anchoring literature]
- R5: Never auto-split the difference on a bot's price. Compare against our own reservation cost first. [Medium]
- R6: Expect emotional appeals ("we are struggling") from a bot; do not concede on that alone. Treat them as tactics. [Low-medium: single paper, prompted behaviours]
- R7: Re-state current terms and the deal status in every message to avoid state confusion. [Low: authors' own workaround]

## 3. Loschelder, Friese, Schaerer, Galinsky (Columbia/INSEAD): The Too-Much-Precision Effect

### Takeaway
Precise first offers anchor amateurs more the more precise they are, but experts react against very precise numbers (they read them as a lack of competence) unless a rationale is given.

### Cited Findings
- Citation: Loschelder, D.D., Friese, M., Schaerer, M., Galinsky, A.D. (2016) "The Too-Much-Precision Effect: When and Why Precise Anchors Backfire With Experts", Psychological Science 27(12), 1573-1587. DOI 10.1177/0956797616666074.
- Legal full text: https://ink.library.smu.edu.sg/cgi/viewcontent.cgi?article=6170&context=lkcsb_research (Singapore Management University repository, "free and open access"; record https://ink.library.smu.edu.sg/lkcsb_research/5171). Access type: open access (institutional repository, accepted/publisher version stated on the cover page). Open data: https://osf.io/b8zft/.
- Pages read: about 8 of 16 closely (abstract, theory, Experiment 1 method/results, general discussion), headings and results of Exp. 2-5 skimmed via the text.
- Five experiments, 1,320 experts and amateurs (real-estate, jewellery/diamond, car sales, HR negotiations).
- Experiment 1: 223 real-estate agents and 230 amateurs saw a house price with 2 to 8 precise digits. Amateurs: willingness to pay rose linearly with precision. Experts: inverted U, with benefit up to moderate precision, then a drop. [Table 1, Fig. 2]
- Mechanism: perceived competence of the first mover (mediation), not scale granularity.
- Experiments 4 and 5: giving a plausible rationale for a very precise price removed the backfire for car-sales and HR experts.
- Earlier work cited: 49 of 49 prior studies found linear precision effects, all mainly with amateurs.
- Limits: human counterpart assumed; the authors note the effect may not arise without a human or where precise numbers are normal. A bot supplier may not attribute competence. Student/professional samples, not procurement.

### Rules for our agent (evidence strength)
- R8: Make the opening counter moderately precise (e.g., a rounded-but-specific figure), not 5-digit decimals, when the counterpart may be an experienced seller. [Medium for humans, Low for bots]
- R9: Attach a one-line, plausible rationale to every offer (benchmark, volume, competing quote). It protects anchor strength and credibility. [Medium: causal experiments]
- R10: Do not assume precision helps in all cases; test against the supplier bots' reactions in practice. [Low: untested for LLM counterparts]

## Overall note for the report writer
All three are legally readable. Sources 1 and 2 are computational (agents), source 3 is human behavioural. Not claimed: MIT OCW, Princeton OAR, Wharton or Kellogg papers (no verified full text found within the budget).
