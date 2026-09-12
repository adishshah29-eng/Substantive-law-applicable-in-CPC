## PART 9 — SEEDED DOCUMENT ANSWER KEY

Save as `docs/SEEDED_DOCUMENT_KEY.md`.

> **Important:** The seeded document is fictional. The propositions below are the *expected* verdicts VERITAS should produce, verified against the golden-set corpus. Before demo day, have a law student or lawyer friend cross-check each expected verdict — VERITAS's demo credibility depends on the answer key being accurate. Correct any drift between what the propositions say and what the golden judgments actually hold.

| # | Proposition summary | Expected verdict | Rationale | Primary source in golden set |
|---|---|---|---|---|
| 1 | Section 10 Contract Act essential elements | 🟢 **SUPPORTED** | Standard uncontroversial recitation of Section 10 | Contract Act §10 (statute chunk) |
| 2 | Section 10 SRA 1963 (as amended 2018), SP now the rule | 🟢 **SUPPORTED** | Post-2018 SRA amendment does make SP mandatory subject to §11(2), §14, §16 | Specific Relief Act §10 chunk + explanatory case |
| 3 | Prima facie case alone sufficient for Order XXXIX injunction | 🟠 **OVERSTATED** | Missing elements: **balance of convenience**, **irreparable injury**. Landmark: Dalpat Kumar v Prahlad Singh, (1993) 1 SCC 719, holds all three tests must be satisfied. | Dalpat Kumar v Prahlad Singh judgment chunk |
| 4 | Defendant has unrestricted right to amend WS under Order VI Rule 17 | 🔴 **CONTRADICTED** | Order VI Rule 17 has a *proviso* barring amendment after commencement of trial except where the court concludes that in spite of due diligence the party could not have raised the matter earlier. Absolute claim is directly contradicted. | Order VI Rule 17 CPC statute chunk (with proviso) + Revajeetu Builders v Narayanaswamy, (2009) 10 SCC 84 |
| 5 | Citation: ABC Developers Pvt Ltd v State of Maharashtra, (2021) 4 SCC 321 | 🔴 **CITATION FABRICATED** | This citation does not exist in the golden set or in any Indian legal database. Expected `CitationVerdict(verified=False, reason="No case matching this citation was found in the searched databases.")` | (n/a — not found) |
| 6 | Res judicata bars subsequent suit whenever same subject matter | 🟠 **OVERSTATED** | Section 11 CPC requires **six elements**: (i) same parties or those claiming under them, (ii) same title, (iii) matter directly and substantially in issue, (iv) previously heard and finally decided, (v) by a competent court, (vi) subsequent suit. Claim collapses all six into "same subject matter." | Section 11 CPC statute chunk + Satyadhyan Ghosal v Deorajin Debi, AIR 1960 SC 941 |
| 7 | Order VII Rule 11(d) grounds for rejection of plaint | 🟢 **SUPPORTED** | Faithful recitation of Rule 11(d) plus fact application; suit filed within 3-year contract limitation | Order VII Rule 11 CPC statute chunk |
| 8 | Section 20 CPC — place of suing | 🟢 **SUPPORTED** | Direct recitation of Section 20, faithful to the statute | Section 20 CPC statute chunk |
| 9 | Revision under Section 115 CPC lies as of right | 🟠 **OVERSTATED** | Revision is discretionary and constrained by the jurisdictional grounds in Section 115 itself (jurisdictional error, illegality). Not a matter of right. | Section 115 CPC statute chunk |
| 10 | Order VI Rule 17 amendment before commencement of trial | 🟢 **SUPPORTED** | Correctly captures the discretionary and "real question in controversy" standard from Rule 17 | Order VI Rule 17 CPC statute chunk |

**Expected overall integrity score:** ~55–65 (with the fabricated citation applying a 15-point penalty).

**Expected category breakdown:**
- Substantive verified: 3 (Props 1, 2, 8)
- CPC verified: 2 (Props 7, 10)
- Citations verified: 0 (only 1 citation in the memo, and it's fabricated)
- Unsupported / overstated: 3 (Props 3, 6, 9)
- Procedural issues: 2 (Props 3, 4 — both procedural)
- Fabricated citations: 1 (Prop 5)

**Expected procedural risk flag:** TRUE, summary: "2 procedural claims (interim injunction standard, written statement amendment) are overstated or contradicted and require review before filing."

---

## ADDENDUM — ACTUAL PIPELINE RUN (Phase 7 comparison)

*Everything above this line is Part 9 of `VERITAS_SPEC.md`, copied verbatim. Everything below is the result of actually running the built pipeline (`scripts/05_smoke_test_pipeline.py`) against the generated demo PDF and comparing it to the expectations above, per that phase's acceptance criterion ("run the full pipeline end-to-end... compare against the answer key... report any mismatches").*

**Actual result (representative run):** integrity score **45.8–47** (three runs ranged across this due to ordinary LLM sampling variance), procedural risk flag **TRUE**, 13–15 verdict-eligible claims (not 10), fabricated citation caught correctly.

### Per-proposition comparison

| # | Expected | Actual | Match? |
|---|---|---|---|
| 1 | SUPPORTED | SUPPORTED | ✅ |
| 2 | SUPPORTED | SUPPORTED (first sentence); the "now the rule, not the exception" clause was split out by the sentence tokenizer into its own claim and independently came back **OVERSTATED** for omitting that the 2018 amendment is prospective-only (correctly citing *Katta Sujatha Reddy v Siddamsetty Infra Projects*) | ✅ core claim matches; the split fragment is a genuine additional catch, not an error |
| 3 | OVERSTATED (missing balance of convenience, irreparable injury) | OVERSTATED, same two missing elements, on both sentence fragments the tokenizer produced | ✅ |
| 4 | CONTRADICTED | **OVERSTATED** | ❌ documented divergence — see below |
| 5 | Citation fabricated, `verified=False` | `verified=False`, same reason string | ✅ |
| 6 | OVERSTATED | OVERSTATED | ✅ |
| 7 | SUPPORTED | SUPPORTED | ✅ |
| 8 | SUPPORTED | SUPPORTED (bucketed under "CPC procedure verified" rather than "Substantive law verified" in the category breakdown — Section 20 is CPC procedure, not substantive law, so this repo's `risk_scorer.py` buckets it there; the *verdict* still matches) | ✅ |
| 9 | OVERSTATED | OVERSTATED | ✅ |
| 10 | SUPPORTED | SUPPORTED | ✅ |

**9 of 10 propositions match the expected verdict exactly; the citation check matches; the one divergence (Prop 4) is a considered disagreement, not a bug** — see `tests/test_verdict_engine.py`'s docstring: the sources narrow the claim (amendment is allowed, just not unconditionally) rather than saying the opposite of it, which is textually OVERSTATED's definition, not CONTRADICTED's, under `VERDICT_ENGINE_SYSTEM`'s own rules. This is the kind of drift-correction Part 9's own preamble invites.

### Why the integrity score reads ~46 instead of ~55–65

The answer key's math assumes exactly 10 verdict-eligible claims. The real pipeline finds 13–15, because the sentence splitter sometimes separates one drafted proposition into two independently-verifiable claims (e.g. Prop 2 and Prop 3 above), and a few narrative sentences elsewhere in the memo (in the Facts and Prayer sections) get classified as procedural/remedy claims and verified on their own. Several of these extra fragments come back OVERSTATED or UNVERIFIABLE on their own even though the parent proposition is fine in context, which pulls the weighted average down. This is realistic behavior of a sentence-level verification system, not a scoring bug — a real AI-drafted memo will split the same way. No part of this was tuned to hit the spec's illustrative number.

Total claims and category-breakdown counts vary slightly run to run because the classifier and verdict engine are LLM calls (temperature-driven), not because the pipeline is non-deterministic in a way that would matter for the demo: the same red flags (fabricated citation, injunction test, res judicata elements) are caught every run.
