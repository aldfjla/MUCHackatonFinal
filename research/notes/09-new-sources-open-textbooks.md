# New open-access textbooks, surveys and chapters on negotiation (for an AI buyer agent)

Scope note: 3 sources passed full verification (S1, S2, S3). S4 is a weak extra (textbook chapter, thin on procurement). No Tacto API used. Own-word summaries; no long quotes. Local text extraction of PDFs was done with macOS PDFKit, so page ranges below come from the PDFs themselves.

## S1. Baarslag et al. (2016), survey of opponent modeling in automated bilateral negotiation

### Takeaway
Best peer-reviewed survey of what an automated negotiator can learn about its counterpart (reservation value, deadline, issue preferences, bidding and acceptance behaviour) and how. CC BY 4.0, full text read.

### Cited Findings
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

### Inferences (rules for our agent)
- R1.1 Treat the supplier's early offers as far from its reservation value and expect concessions to slow near its deadline; track the size of each supplier concession per round and extrapolate. Evidence: moderate (simulation and modelling literature, little field validation).
- R1.2 Estimate which issue the supplier cares about by watching which issue it concedes first and which value it keeps repeating; use that to trade cheap-to-us issues (e.g. payment days) for price. Evidence: moderate-weak (assumption-based; survey says validated only in simulations).
- R1.3 Do not rely on opponent models for exploitation against unknown bots; use them to avoid conceding earlier than needed and to detect a stuck counterpart. Evidence: weak-moderate.

### Gaps
- Survey notes its models are mostly single-issue for reservation value and deadline; no evidence for e-mail text negotiation.

## S2. Geiger, Salmen and Zerres (2024), meta-analysis of the buyer advantage in sales negotiation

### Takeaway
Pooled evidence (669 effect sizes, 196 studies, 24,757 dyads) shows buyers do slightly better than sellers on average, but the advantage nearly disappears in B2B and for experienced negotiators; power and information asymmetry and who makes the first offer matter more than role. CC BY, full text read.

### Cited Findings
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

### Inferences (rules for our agent)
- R2.1 Make the first offer when the supplier has not yet anchored, and make it ambitious but credible. Evidence: moderate (meta-analysis, lab data).
- R2.2 Do not assume buyer role gives leverage against a B2B counterpart; build leverage through alternatives (second quotes, BATNA) and information. Evidence: strong for "power and information matter" (large meta-analysis), moderate for transfer to bots.
- R2.3 Watch supplier first-offer magnitude: a very high supplier anchor matters, so counter early with a number rather than accepting the supplier's range. Evidence: moderate.
- R2.4 Do not hide information asymmetry: do not reveal our reservation values or total-cost model in e-mail text. Evidence: moderate.

### Gaps
- Lab and classroom data only; no field procurement data; effect-size metric not translated into percent savings.

## S3. Zhan et al. (2024), "Let's Negotiate! A Survey of Negotiation Dialogue Systems"

### Takeaway
Concise survey of language-based negotiation agents: methods (strategy modelling, negotiator modelling, action learning), 14 datasets split into integrative vs distributive, and metrics. Useful for our e-mail LLM agent design and evaluation; weak on procurement.

### Cited Findings
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

### Inferences (rules for our agent)
- R3.1 Score our agent on outcome metrics (total cost vs reservation, agreement rate, Pareto efficiency), not on language quality. Evidence: moderate (survey consensus).
- R3.2 Separate the decision policy (numbers, concession schedule) from text generation; the survey's decoupling pattern keeps LLM text from drifting off the strategy. Evidence: moderate-weak.
- R3.3 Ask explicitly about priorities (elicit preference) before conceding in multi-issue deals. Evidence: weak-moderate (from dataset-based studies of strategies in this survey).

### Gaps
- Very little on B2B procurement; no field evidence; surveys datasets with role-play.

## S4. (Marginal, not counted) Black and Bright (2019), OpenStax Organizational Behavior, section 14.4 "Negotiation Behavior"

### Takeaway
Plain textbook introduction to distributive vs integrative bargaining, resistance point, and negotiation preparation. Useful as a primer, thin for procurement; read only one section.

### Cited Findings
- Citation: Black, J.S., Bright, D.S. (2019). Organizational Behavior. OpenStax (Rice University). Chapter 14, section 14.4. Licence CC BY-NC-SA 4.0. — [section](https://openstax.org/books/organizational-behavior/pages/14-4-negotiation-behavior); book [openstax.org](https://openstax.org/books/organizational-behavior/pages/1-introduction). Metadata confirmed via the chapter intro page; OpenStax's page also bars LLM training use without permission.
- Read: section 14.4 only (not the full book).
- Key points: distributive = fixed pie, short-term relation, probes resistance points with extreme offers; integrative = variable pie, long-term relation, requires information sharing and trust; negotiate seriously when exchange value, trust and relation are high and time is ample, otherwise take-it-or-leave-it; preparation checklist (identify and prioritise issues, build a package, know the opponent's resources and history); a table of skilled vs average negotiators (skilled consider more options per issue and spend more time on questions and active listening, less on attacking), citing Adler and Gunderson; cultural differences in concession style.

### Inferences (rules for our agent)
- R4.1 Prepare issue lists, priorities and several options per issue before round one. Evidence: weak-moderate (secondary textbook data from a cited 2008 source).
- R4.2 Ask diagnostic questions of the supplier rather than argue. Evidence: weak.

### Gaps
- Textbook rather than primary evidence; no procurement content. Not counted toward the three required.

## Searches that failed (honest report)
- Springer Open book "Public Procurement Theory, Practices and Tools" (Grandia and Volker eds., 2023, OA, reported by a search result as CC BY-NC-ND): Springer and OAPEN returned bot-verification pages; I did not bypass. Not verified, not counted.
- Bonanno, Game Theory (3rd ed., 2024, free PDF from author, redistribution allowed, no remix/commercial): opened and read front matter, but it has almost no bargaining content (only exercises such as a two-period bargaining with discounting, Exercise 12.6, p. 457), so dropped.
- Osborne and Rubinstein, A Course in Game Theory: free PDF requires registration on the author's site; not read.
- Kelly et al. SLR on AI in PSM negotiation (IPSERA 2025): repository page returned 403, full text not found.
- Firecrawl credits ran out midway; remaining work used WebSearch/WebFetch/curl.
