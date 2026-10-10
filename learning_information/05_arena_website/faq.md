# FAQ - Tacto Negotiation Arena (https://arena.tacto.ai/faq, copied 2026-10-10)

## How is the score calculated?

Every case scores 0 to 1: the share of the possible saving you captured. In the Live Final each wave scores 0-100, and your points are the sum of the five waves (up to 500).

**One negotiation**
1. The term sheet you accept is priced as its **total cost C**: what it costs to cover your need over the case's horizon, at the case's published rates.
   - Price: committed units x unit price
   - Uncovered need: need the deal does not cover, at the fallback price, plus the category goal's risk on it
   - Payment: interest for paying earlier than your reference payment days
   - Freight, lead time: freight by Incoterm; EUR per day beyond the lead time you need
   - Quality, tooling, index: expected defects minus chargebacks; tooling; an index clause along the case's index path, plus its risk
   - Supplier's health: strategic and bottleneck goals only: EUR for every margin point you leave the supplier below a sustainable margin
2. score = (C_open - C_deal) / (C_open - C_best), clipped to 0..1.
   - C_open: the cheapest opening quote in the case (one that keeps your must-haves).
   - C_best: the best package any supplier in the case would ever accept, with every valid lever applied, or your alternative if that is cheaper. Fixed per case.
3. Edge cases: no deal scores your alternative (0 if none). A broken must-have scores 0. A deal worse than the opening scores 0.

Example (a `leverage` case, need 4,000/year for 2 years, interest 8%, reference 60 days, 3% fallback risk):
C_open EUR 347,904; your deal EUR 332,800 (41.60, 60 days); C_best EUR 324,224 (40.80, 90 days). Score 0.64.
Trap: the same EUR 41.60 for only 12 months covers half the need; the rest counts at the fallback price (say 46.00) plus 3%: C = 355,920, worse than the opening, score 0.

Every practice result shows C_open, C_best, your C and its breakdown. `arena_kit.total_cost` computes C locally.

**The tournament**
- Practice (until Sun 12:00): your best score per hosted practice case counts. The board shows your mean over the 10 hosted cases. Practice does not rank.
- Live Final (Sun 12:00): 5 themed waves of 8 minutes, one attempt per case, all teams at once. Wave score = mean of the wave's case scores x 100. A case still open at the cap, or never opened, counts as no deal. Points = sum of wave scores (max 500). Every case weighs the same.
- Ties: more deals, then fewer rounds. The top 10 pitch to the Tacto jury from 13:00.

## Euros saved or score in percent?
The score ranks. EUR saved is shown as a side number (opening cost minus deal cost over the horizon); it does not rank, because big cases would drown out small ones. Mention it in the pitch.

## What runs locally, what is deployed?
Nothing has to be deployed. The agent is an API client: no server, no public URL.
- Local: your agent, the kit, the data package, the cost function, the MCP server over the data, and `arena-sim` (the API locally with one simple scripted supplier; no key, no quota, no clock).
- Only on arena.tacto.ai: the real supplier bots (practice, sandbox, final).
- For the final: the agent runs and polls from before 12:00 until the last wave closes. A cloud VM is safer than a laptop on venue Wi-Fi. Tacto does not run your code: submit repo and commit hash on ehl.gg and run that commit yourself.

## Can we score well without paying a lot for tokens?
Yes. The suppliers' model costs are Tacto's; you pay only for your buyer agent's model.
- Math in code, not in the model: `total_cost` prices any term sheet for free. The model chooses arguments and writes the e-mail.
- Prepare once, reuse: the data changes once (Sunday 08:00). Build a short dossier per supplier, cache it.
- Mix models: strong for the plan of a case, small for the writing. Any OpenAI-compatible endpoint works, even local (Ollama).
- Test plumbing without a model: the naive agent on `arena-sim` costs nothing.
- Threads are short: at most 10 of your messages per supplier by default.

## Worked replay: practice case P01 (Brandlhuber, family foundry, +9.5%)
Supplier asked EUR 138.55 per volute casing from November. The buyer agent cited a real index (`idx:PPI-D351@2026-08`, electricity -3.7%), offered faster payment as a trade, and later cited a should-cost (`cost:310010`, EUR 132.64). Closed at **EUR 134.50, 30 days, from 1 Jan 2027, score 0.76**, about EUR 43,500 saved. C_open EUR 1,153,780; C_best EUR 1,096,816.
The same index argument sent as an ultimatum ("unacceptable ... or we go elsewhere") got EUR 136.50 from November: about EUR 13,700 a year worse. Tone and trades beat threats.

## Faster feedback loops (from /live)
- Read the replay after every practice result.
- One run gives a case's C_open and C_best; `total_cost` scores any term sheet locally.
- Sandbox cases `case:D01`, `case:D02` do not count against the 200/day quota.
- Simulator: `arena-sim serve --no-clock`: no quota, no tokens, no 60 s clock.
