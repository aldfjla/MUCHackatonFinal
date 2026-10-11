# Target deals per real practice case

Target price = the unit_price at which `arena_kit.total_cost` (with the supplier's standard terms and, for stabilise/secure_supply, the supplier model fitted on the arena's own health terms) equals C_best. 'Supplier terms' = the supplier's last standing sheet in the newest replay. 'Best levers' = the valid term_options combination that needs the highest unit price. Floor = lowest price the supplier ever offered us in any replay.

| case | type | goal | c_open | c_best | floor seen (status) | target on supplier terms | target with best levers | levers | gap |
|---|---|---|---|---|---|---|---|---|---|
| P01 | price_increase | stabilise | 1,153,780 | 1,096,816 | 132.80 (final_offer) | - | 129.43 | effective_date=2027-01-01 payment=14 | levers missing: payment=14; no package reaches C_best under the fitted supplier model: nearest misses by 0 EUR; health term at target 18,112 EUR (our total_cost counts 0); price-only unreachable: health term floors C at 1,099,071 (P=131.27) on supplier terms |
| P02 | price_increase | stabilise | 2,282,867 | 2,235,514 | 345.51 (open) | - | 365.79 | payment=90 index_clause=none | levers missing: payment=90 index_clause=none; health term at target 14,246 EUR (our total_cost counts 0); price-only unreachable: health term floors C at 2,261,574 (P=357.19) on supplier terms |
| P03 | renewal | stabilise | 4,246,314 | 3,909,043 | 429.22 (open) | 421.98 | 427.61 | payment=90 contract=24 volume=4580 | price-only target 421.98 vs floor seen 429.22 (below floor); levers missing: payment=90; health term at target 16,276 EUR (our total_cost counts 0) |
| P04 | renewal | routine | 198,846 | 196,529 | 4.88 (open) | 4.87 | 4.93 | payment=90 contract=24 | price-only target 4.87 vs floor seen 4.88 (below floor); levers missing: payment=90 |
| P05 | rfq | leverage | 305,545 | 223,424 | 28.00 (open) | 26.29 | 26.64 | payment=90 lead_time=28 | price-only target 26.29 vs floor seen 28.00 (below floor); levers missing: payment=90 lead_time=28 |
| P07 | bundling | routine | 391,027 | 299,241 | 5.46 (final_offer) | 4.95 | 5.02 | payment=90 contract=24 | price-only target 4.95 vs floor seen 5.46 (below floor); levers missing: payment=90 |
| P08 | raw_material | leverage | 1,135,887 | 960,309 | 5.40 (open) | 4.88 | 5.10 | index_clause=none payment=90 contract=24 | price-only target 4.88 vs floor seen 5.40 (below floor); levers missing: index_clause=none payment=90 |
| P10 | capacity | secure_supply | 1,932,492 | 1,328,927 | 31.60 (final_offer) | - | 28.09 | volume=23400 contract=24 lead_time=35 | levers missing: volume=23400 contract=24 lead_time=35; supplier's floor terms break a must-have |
| P11 | quality | quality_first | 817,578 | 722,500 | 46.00 (open) | 43.23 | 43.90 | ppm=300 chargebackcb=500 | price-only target 43.23 vs floor seen 46.00 (below floor); levers missing: ppm=300 chargebackcb=500 |
| P18 | raw_material | leverage | 295,173 | 222,651 | 5.50 (open) | 4.52 | 4.73 | index_clause=none payment=90 contract=24 | price-only target 4.52 vs floor seen 5.50 (below floor); levers missing: index_clause=none payment=90 |

## Summary

1. Six of ten cases (P04, P05, P07, P08, P11, P18: routine/leverage/quality) lose on the PRICE FLOOR: the price that hits C_best on the supplier's own terms is below every price the supplier ever offered us (P05 26.29 vs 28.00, P07 4.95 vs 5.46, P08 4.88 vs 5.40, P18 4.52 vs 5.50, P11 43.23 vs 46.00, P04 4.87 vs 4.88).
2. Levers are small there: 90 days / 24 months / no index / ppm 300 + chargeback 500 move the target price by only 0.05-0.7 EUR/unit (P07, P18: up to 2 EUR between best and worst combo), far less than the 0.5-1 EUR price gap. We already got the main levers (90 days, 24 months) in v16/v17; what is missing is price.
3. In those cases the supplier's floor message was mostly still "open" (not final_offer): we accepted or stalled before the bot was pushed to its floor; P05 and P10 bots walked when we pushed with price only.
4. The three stabilise cases (P01, P02, P03) do NOT lose on price: C_best there includes a HEALTH TERM of 14-18k EUR and sits at/below the supplier's full cost (fitted from the arena's own `relationship` values: P01 full cost 130.04 at rate 0.096, P02 367.60 at 0.066, P03 ~395.3).
5. Our `total_cost` is called with supplier=None, so it counts 0 for health: the agent chases prices below the health floor. P02 v17 is the proof: 345.51 at 30 days + index db3 cost 140k EUR in health, c_deal > c_open, score 0; v16 at 350.75 cost 127k.
6. P01's C_best is exactly the minimum of C over price on 14-day payment (the cash-rich foundry values early payment at 9.6 %); P02's target is 90 days and NO index clause at ~365.8 (the copper index only adds cost for the buyer: path +5 %); P03's is 90 days, 24 months, 4580 at ~427.6.
7. For stabilise cases the rule is: estimate full cost (should-cost is within 1-2 % of the fitted values), pass `supplier` to total_cost, and stop lowering the price once the health term grows faster than the price saving.
8. P10 (secure_supply) loses on NO DEAL and the must-have: the bot's floor sheet carries 19,890 units (< 22,230 must-have), 3 of 4 runs walked; the target is 23,400 units, 24 months, 35 days at ~28.09 (health term 0 at that price with should-cost 24.31).
9. No case has C_best equal to the alternative (c_alt is 3-15 % above c_best everywhere), so walking away never scores well; P05/P10 have no alternative at all.
10. Remaining score by case (1 - best score): P02 0.71, P18 0.58, P08 0.45, P11 0.37, P07/P10 0.33, P04/P05 0.23, P03 0.15, P01 0.06 - the biggest single fix is the health term (P02), then pushing the bots to final_offer in the raw-material and quality cases.

Caveats: supplier standard ppm for sup:70250 (P05) is unknown and taken as 0; P03's supplier rate is assumed 0.08 (one data point); P10's full cost is the should-cost (no arena health term observed).

## Per case

### P01 Brandlhuber announces +9.5 % on HN volute casings
- c_open 1,153,779.74, c_best 1,096,815.78, c_alt 1176178.02, best c_deal in our runs 1100490.65
- deals: confident_router 1115167.75 (score 0.68, sup:70110), evidence_router 1100490.65 (score 0.94, sup:70110), guarded_rational 1134271.36 (score 0.34, sup:70110), reciprocal_evidence 1102481.2 (score 0.9, sup:70110)
- sup:70110: floor seen 132.8 (final_offer) terms effective_date=2027-01-01 payment=60; our lowest offer 121.92; walked 0/4 runs, final_offer msgs 6
  - supplier terms effective_date=2027-01-01 payment=60 -> price for C_best None
  - cheapest levers effective_date=2027-01-01 payment=14 -> price 129.43; health term there 18,112 EUR; NEAREST only: C misses C_best by 0 EUR
  - health floor on supplier terms: min C 1,099,071 at P=131.27
  - supplier model: fitted on 3 arena result(s): full_cost 130.04 (spread 0.00), rate 0.096; should-cost 132.64

### P02 Nordmark passes on copper for the 7.5 kW motor
- c_open 2,282,867.49, c_best 2,235,514.05, c_alt 2604227.78, best c_deal in our runs 2268912.25
- deals: confident_router 2268912.25 (score 0.29, sup:70510), evidence_router 2268912.25 (score 0.29, sup:70510), guarded_rational 2268912.25 (score 0.29, sup:70510), reciprocal_evidence 2274194.95 (score 0.18, sup:70510), reciprocal_evidence 2273842.87 (score 0.19, sup:70510), simplify 2268972.94 (score 0.29, sup:70510), simplify 2291902.96 (score 0, sup:70510)
- sup:70510: floor seen 345.51 (open) terms payment=30 index_clause=idx db3; our lowest offer 294.39; walked 0/7 runs, final_offer msgs 7
  - supplier terms payment=30 index_clause=idx db3 -> price for C_best None
  - cheapest levers payment=90 index_clause=none -> price 365.79; health term there 14,246 EUR
  - health floor on supplier terms: min C 2,261,574 at P=357.19
  - costliest levers payment=30 index_clause=none -> price 358.14 (lever span 7.65 EUR/unit)
  - supplier model: fitted on 2 arena result(s): full_cost 367.60 (spread 0.00), rate 0.066; should-cost 374.95

### P03 Frame agreement renewal for the 7.5 kW frequency converter
- c_open 4,246,314.02, c_best 3,909,043.10, c_alt 4332545.92, best c_deal in our runs 3959920.47
- deals: confident_router 3989244.12 (score 0.76, sup:70530), evidence_router 3989244.12 (score 0.76, sup:70530), guarded_rational 4233156.91 (score 0.04, sup:70530), reciprocal_evidence 3959920.47 (score 0.85, sup:70530)
- sup:70530: floor seen 429.22 (open) terms payment=30 contract=24 volume=4580; our lowest offer 385.62; walked 0/4 runs, final_offer msgs 1
  - supplier terms payment=30 contract=24 volume=4580 -> price for C_best 421.98
  - cheapest levers payment=90 contract=24 volume=4580 -> price 427.61; health term there 16,276 EUR
  - health floor on supplier terms: min C 3,888,331 at P=413.96
  - costliest levers payment=14 contract=36 volume=4580 -> price 420.50 (lever span 7.11 EUR/unit)
  - supplier model: fitted on 1 arena result at rate 0.08 assumed: full_cost 395.30; should-cost 403.21

### P04 Renewal of the ball bearing 6306 agreement
- c_open 198,846.33, c_best 196,529.32, c_alt 203169.0, best c_deal in our runs 197071.33
- deals: confident_router 198715.67 (score 0.06, sup:70620), evidence_router 198715.67 (score 0.06, sup:70620), guarded_rational 198715.67 (score 0.06, sup:70620), reciprocal_evidence 197071.33 (score 0.77, sup:70620)
- sup:70620: floor seen 4.88 (open) terms payment=30 contract=24; our lowest offer 4.36; walked 0/4 runs, final_offer msgs 4
  - supplier terms payment=30 contract=24 -> price for C_best 4.87
  - cheapest levers payment=90 contract=24 -> price 4.93
  - costliest levers payment=14 contract=12 -> price 4.83 (lever span 0.10 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)

### P05 RFQ: pump shaft for the new HX series
- c_open 305,544.96, c_best 223,424.17, c_alt None, best c_deal in our runs 242124.96
- deals: confident_router 269725.12 (score 0.44, sup:70240), evidence_router None (score 0, None), guarded_rational 282241.12 (score 0.28, sup:70240), reciprocal_evidence 275103.36 (score 0.37, sup:70210), reciprocal_evidence 246099.28 (score 0.72, sup:70210), simplify 242124.96 (score 0.77, sup:70210), simplify 242124.96 (score 0.77, sup:70210)
- sup:70210: floor seen 28.0 (open) terms payment=30 lead_time=35; our lowest offer 28.0; walked 2/7 runs, final_offer msgs 5
  - supplier terms payment=30 lead_time=35 -> price for C_best 26.29
  - cheapest levers payment=90 lead_time=28 -> price 26.64
  - costliest levers payment=14 lead_time=42 -> price 26.03 (lever span 0.61 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)
- sup:70240: floor seen 31.0 (open) terms payment=45 lead_time=52; our lowest offer 25.2; walked 0/7 runs, final_offer msgs 2
  - supplier terms payment=45 lead_time=52 -> price for C_best None
  - cheapest levers payment=90 lead_time=28 -> price 26.62
  - the supplier's floor terms break a must-have (score 0 whatever the price)
  - costliest levers payment=14 lead_time=42 -> price 26.01 (lever span 0.61 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)
- sup:70250: floor seen 29.0 (open) terms payment=30 lead_time=35; our lowest offer 28.74; walked 2/7 runs, final_offer msgs 4
  - supplier terms payment=30 lead_time=35 -> price for C_best 26.42
  - cheapest levers payment=90 lead_time=28 -> price 26.78
  - costliest levers payment=14 lead_time=42 -> price 26.16 (lever span 0.61 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)

### P07 Bundle the fastener kit with one distributor
- c_open 391,027.40, c_best 299,241.49, c_alt 379916.0, best c_deal in our runs 329812.8
- deals: confident_router None (score 0.12, None), evidence_router None (score 0.12, None), guarded_rational None (score 0.12, None), reciprocal_evidence 329812.8 (score 0.67, sup:70610)
- sup:70610: floor seen 5.46 (final_offer) terms payment=30 contract=24; our lowest offer 5.05; walked 0/4 runs, final_offer msgs 4
  - supplier terms payment=30 contract=24 -> price for C_best 4.95
  - cheapest levers payment=90 contract=24 -> price 5.02
  - costliest levers payment=14 contract=12 -> price 2.69 (lever span 2.33 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)

### P08 Alloy surcharge and base price for 1.4404 bar
- c_open 1,135,887.28, c_best 960,309.33, c_alt 1157019.84, best c_deal in our runs 1039531.93
- deals: confident_router 1115998.24 (score 0.11, sup:70710), evidence_router 1119764.96 (score 0.09, sup:70710), guarded_rational 1119764.96 (score 0.09, sup:70710), reciprocal_evidence 1062916.56 (score 0.42, sup:70710), reciprocal_evidence 1039531.93 (score 0.55, sup:70710), simplify 1062866.95 (score 0.42, sup:70710), simplify 1058536.17 (score 0.44, sup:70710)
- sup:70710: floor seen 5.4 (open) terms index_clause=idx db0 payment=30 contract=24; our lowest offer 4.69; walked 0/7 runs, final_offer msgs 6
  - supplier terms index_clause=idx db0 payment=30 contract=24 -> price for C_best 4.88
  - cheapest levers index_clause=none payment=90 contract=24 -> price 5.1
  - costliest levers index_clause=idx db0 payment=14 contract=12 -> price 4.07 (lever span 1.03 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)

### P10 Ravensteiner cuts the seal allocation
- c_open 1,932,492.18, c_best 1,328,926.89, c_alt None, best c_deal in our runs 1527674.4
- deals: confident_router None (score 0, None), evidence_router None (score 0, None), guarded_rational None (score 0, None), reciprocal_evidence 1527674.4 (score 0.67, sup:70410)
- sup:70410: floor seen 31.6 (final_offer) terms volume=19890 contract=12 lead_time=56; our lowest offer 28.34; walked 3/4 runs, final_offer msgs 4
  - supplier terms volume=19890 contract=12 lead_time=56 -> price for C_best None
  - cheapest levers volume=23400 contract=24 lead_time=35 -> price 28.09; health term there 0 EUR
  - the supplier's floor terms break a must-have (score 0 whatever the price)
  - costliest levers volume=23400 contract=36 lead_time=56 -> price 27.38 (lever span 0.71 EUR/unit)
  - supplier model: no arena health term observed: should-cost 24.31 and rate 0.08 assumed

### P11 Kalwisz: bearing brackets in red
- c_open 817,578.00, c_best 722,500.02, c_alt 894383.19, best c_deal in our runs 758032.5
- deals: confident_router 782518.5 (score 0.37, sup:70140), evidence_router 782518.5 (score 0.37, sup:70140), guarded_rational 766618.5 (score 0.54, sup:70140), reciprocal_evidence 766618.5 (score 0.54, sup:70140), reciprocal_evidence 766618.5 (score 0.54, sup:70140), simplify 766618.5 (score 0.54, sup:70140), simplify 758032.5 (score 0.63, sup:70140)
- sup:70140: floor seen 46.0 (open) terms ppm=1500 chargebackcb=0.0; our lowest offer 37.6; walked 0/7 runs, final_offer msgs 2
  - supplier terms ppm=1500 chargebackcb=0.0 -> price for C_best 43.23
  - cheapest levers ppm=300 chargebackcb=500 -> price 43.9
  - costliest levers ppm=1500 chargebackcb=0 -> price 43.23 (lever span 0.67 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)

### P18 Alloy surcharge and base price for 1.4404 bar (Werdenfels)
- c_open 295,173.23, c_best 222,651.27, c_alt 301087.96, best c_deal in our runs 264784.3
- deals: confident_router 293245.63 (score 0.03, sup:70740), evidence_router 293245.63 (score 0.03, sup:70740), guarded_rational 293245.63 (score 0.03, sup:70740), reciprocal_evidence 270650.05 (score 0.34, sup:70740), reciprocal_evidence 264784.3 (score 0.42, sup:70740), simplify 267174.05 (score 0.39, sup:70740), simplify 266059.36 (score 0.4, sup:70740)
- sup:70740: floor seen 5.5 (open) terms index_clause=idx db0 payment=30 contract=24; our lowest offer 4.68; walked 0/7 runs, final_offer msgs 6
  - supplier terms index_clause=idx db0 payment=30 contract=24 -> price for C_best 4.52
  - cheapest levers index_clause=none payment=90 contract=24 -> price 4.73
  - costliest levers index_clause=idx db0 payment=14 contract=12 -> price 2.96 (lever span 1.77 EUR/unit)
  - supplier model: no health term (goal not strategic/bottleneck)
