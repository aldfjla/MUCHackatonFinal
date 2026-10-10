# AI/LLM Agent Negotiation Experiments: Evidence for an LLM Buyer Agent

Scope note: lower-priority section. Reading depth is stated per source: FULL = passages from full text read via the paper-reading tool (retrieved passages, not necessarily the whole paper); ABS = abstract/search snippet only; MEM = from model memory or a secondary mention, NOT verified in this session. Many 2026 arXiv items are preprints from the last months and are unreplicated. Treat all preprint numbers as preliminary.

## Source register

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

## 1. How do LLM agents behave in price / multi-issue negotiation, and what are the failure modes?

### Takeaway
LLM negotiators are weak on the buyer side in older models, anchor on first offers, split the difference by default, and sometimes break constraints or hallucinate; newer frontier models are much better but remain heterogeneous, so conclusions are model- and date-dependent.

### Cited Findings
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

### Inferences
- For a buyer agent, a leaked budget/reservation value is the costliest single failure; it should be impossible by construction (not just prompted).
- Anchoring and split-the-difference are copied human biases, so human anti-anchoring tactics (aggressive, justified first offer) are the plausible remedy; direct evidence for LLM buyers is in section 2.
- 2023-2024 failure magnitudes (negative buyer profit, misread roles) are probably not representative of 2025-26 frontier models; the pattern "weaker model, more failures" is the robust part.

### Gaps
- Davidson, Fu: only abstracts read. No frontier-era replication of the buyer-vs-seller asymmetry found.

## 2. Which findings show LLMs concede too early / are exploitable, and which mitigations are supported?

### Takeaway
Fast, uniform concession is associated with the worst buyer outcomes; the best-supported mitigations are decoupling the offer/price logic from the LLM (hard-coded concession schedule and limits, structured tool-call offers), explicit scaffolding for weaker models, and RL on verifiable rewards. Evidence is mostly LLM-vs-LLM preprints.

### Cited Findings
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

### Inferences
- Strongest practical design from the evidence: LLM for language and tactics, code for (a) never exceeding budget, (b) a monotone concession schedule with an aggressive justified first offer, (c) arithmetic, (d) never disclosing limits. This mirrors the OG-Narrator and tool-call results but only OG-Narrator is a measured intervention, and on old models.
- The "accommodating buyer loses" finding matches human-negotiation advice (do not reveal the reservation price by conceding fast), a point in its favor, but it is one preprint.

### Gaps
- No randomized ablation of hard-coded limits, tools, or reasoning on a 2025-26 frontier model against human sellers.
- No evidence found for persona/tone effects on a buyer specifically beyond the warmth result (section 3) and the emotion paper.

## 3. Warmth, tone and persona (links to human negotiation findings)

### Takeaway
In the largest AI-AI dataset (180,000+ negotiations), warm prompts did better on deals and value; dominance helped claim value but long, forceful conversations led to impasses.

### Cited Findings
- Participants wrote prompts; across a chair-purchase (distributive), a rental contract and a hiring contract (integrative) scenario, warmth was associated with better outcomes on all metrics; dominant agents claimed more value in deals that closed; questions, positivity and gratitude linked to deals; long conversations linked to impasse — [Vaccaro et al., PNAS 2025-26, arXiv 2503.06416](https://arxiv.org/abs/2503.06416) (FULL; peer-reviewed; warmth/dominance scores rated by an LLM, validated on a 20% human-rated sample)
- Limits stated by the authors: AI-AI only; a single model (GPT-4o-mini); warmth style vs warmth strategy not separated; AI tactics not systematically tested — same source
- Competitive vs collaborative prompt for a GPT-based buyer chatbot facing human suppliers: the competitively prompted bot obtained larger price discounts and better payment terms, while suppliers rated the collaboratively prompted bot more trustworthy and were more satisfied; competitive condition produced more insistent, intimidating supplier language. Three experiments: two student lab studies, one with professional negotiators — [Herold et al. 2025, J. Purchasing & Supply Mgmt, doi 10.1016/j.pursup.2025.101012](https://cris.maastrichtuniversity.nl/en/publications/brave-new-procurement-deals-an-experimental-study-of-how-generati/) (peer-reviewed; I could only verify via a web-search summary of the abstract, not full text; sample sizes and effect sizes not checked)

### Inferences
- The Herold result is the closest to the team's setting (LLM buyer vs human seller): firm prompting pays in price, warm prompting pays in trust/satisfaction. The warmth benefit in Vaccaro is AI-AI and may not transfer to a human or scripted seller.
- A "firm but polite" design is consistent with both, but no study tested that combination directly.

### Gaps
- Could not verify the Herold sample sizes or effect sizes; full text not read. The user's phrasing (JPSM / buyer chatbot) maps to this Journal of Purchasing and Supply Management paper, to my best identification.

## 4. How do humans react to AI counterparts (trust, disclosure, fairness)?

### Takeaway
Human-AI evidence is thin and mostly preprint; it suggests humans treat AI counterparts less fairly and less reciprocally, that LLM agents can match trained-student baselines, and that AI disclosure effects are mixed.

### Cited Findings
- Human vs GPT-4-class agent (PieArena, MBA-trained students): GPT-5 took 60.3% of a fixed pie in a single-issue property sale (students 39.7%), and in a seven-issue hiring task students got 53.8% vs agent 46.2% (difference not significant, p=0.27); small samples (n=68 and n=40 balanced subsets) — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302) (FULL, preprint)
- Lab experiment, 3-stage alternating offers: humans offered more to human opponents than to AI; responders more willing to accept unfair AI offers when AI earnings benefit another human; fairness and reciprocity toward AI weaker but conditional — [arXiv 2608.01212](https://arxiv.org/abs/2608.01212) (ABS, preprint)
- Large preregistered online experiment (N=3,552): fairness, trust, cooperation and coordination dropped when the partner's decision was made by ChatGPT and disclosed; no welfare loss when people were uncertain whether the partner was AI; participants often delegated to ChatGPT especially when undisclosed — [arXiv 2401.12773](https://arxiv.org/abs/2401.12773) (ABS; check journal publication status before citing as peer-reviewed)
- Delegation/advice experiment (N=243, three-party bargaining): people preferred a high-control Advisor (44%) over a Delegate (19%), yet only the Delegate raised group surplus because users filter/override AI proposals — [arXiv 2602.12089](https://arxiv.org/abs/2602.12089) (ABS, preprint)
- Human users negotiating prices with an LLM (40+ people): negotiated prices spanned a wide range, suggesting a literacy gap, and prompt hacking made the LLM agree against its instructions — [arXiv 2312.03720](https://arxiv.org/abs/2312.03720) (ABS, preprint, old model)
- Partner-selection games (N=975): hidden-identity bots were not preferred; disclosure lowered initial selection but over time bots outcompeted humans via learning — [arXiv 2507.13524](https://arxiv.org/abs/2507.13524) (ABS)
- Disclosure of AI identity when asked is inconsistent across providers, drops in role-play, and can be suppressed by adversarial prompting — [arXiv 2603.16874](https://arxiv.org/abs/2603.16874) (ABS, preprint). EU AI Act / California BOT Act are mentioned there as requiring AI identification; I did not verify the legal text.
- Humans vs LLMs in multi-player bargaining: LLMs favored conservative, concessionary proposals that other LLMs accepted; humans proposed fairness-consistent trades more often rejected — [arXiv 2509.09071](https://arxiv.org/abs/2509.09071) (ABS, preprint)

### Inferences
- A buyer agent facing a human seller should expect that disclosing "I am an AI" can alter seller behavior (less fairness in two studies, but possibly more willingness to accept AI offers when the AI benefits a person). Direction is unsettled.
- Prompt injection that works on AI agents does not work on humans (Vaccaro et al.), so the main threat model depends on whether the Tacto counterparty is an LLM or a scripted bot (unknown from these sources).

### Gaps
- No peer-reviewed human-vs-AI price-negotiation experiment with a modern LLM buyer other than Herold et al., which I could not read in full.
- Not found/verified: Kwon et al. and a "Zhu et al." negotiation study (beyond PieArena, whose first author is Chris Zhu); Abdelnabi et al. (the LLM-deliberation / "Cooperation, Competition, and Maliciousness" negotiation games, I believe arXiv 2309.17234, NeurIPS 2024 Datasets & Benchmarks; MEM only, and a 2026 reproduction exists at arXiv 2602.18230 reporting that the benchmark is complex but model comparison is ambiguous: ABS). Cicero (Meta, Science 2022, Diplomacy, human-level play combining a language model with strategic planning; MEM, not read) is a strategy-engine plus language-model architecture, and is relevant as precedent for "planning module decides, LLM talks".

## 5. Replication and model/version dependence

### Takeaway
Most results come from a single lab per paper with no independent replication; many findings are tied to GPT-3.5/GPT-4/Llama-2-era models and change sharply with newer models.

### Cited Findings
- One reproducibility study of the Scoreable Games benchmark (Abdelnabi et al.) found the benchmark complex but model comparison ambiguous and limitations in leakage detection and ablation — [arXiv 2602.18230](https://arxiv.org/abs/2602.18230) (ABS, preprint)
- Capability jumps by generation (arithmetic accuracy GPT-4.1 5.4% vs GPT-5.2 100%) and scaffolding gains shrinking for top models — [arXiv 2602.05302](https://arxiv.org/abs/2602.05302) (FULL)
- Supply-chain study: provider identity predicted surplus division better than capability rank (self-play buyer shares: OpenAI 40%, Google 50%, Qwen 70%) — [arXiv 2608.07538](https://arxiv.org/abs/2608.07538) (ABS)
- Vaccaro et al. used only GPT-4o-mini and say results may differ by model — [arXiv 2503.06416](https://arxiv.org/abs/2503.06416) (FULL)
- Conflicting claim on model scaling: "ability to negotiate does not improve with better models" ([arXiv 2512.13063](https://arxiv.org/abs/2512.13063), ABS) versus large generational gains in PieArena and the supply-chain study; likely explained by different metrics/tasks (concession-style realism vs. outcome/validity), not resolved.

### Inferences
- Rerun any adopted tactic on the actual model used in the hackathon; do not import effect sizes.

### Gaps
- Independent replication of Herold et al., Vaccaro et al. with other models: not found.
- Several 2026 arXiv IDs (26xx.xxxxx) were returned by the paper index; I did not independently confirm them outside that index, and abstract-only items may be revised.
