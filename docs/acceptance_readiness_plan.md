# Acceptance Readiness Plan

Last updated: 2026-05-20

This document tracks the remaining work needed to make the paper defensible for
review. It does not guarantee acceptance; it lists the highest-risk reviewer
objections and the concrete implementation work needed to address them.

## Current Strongest Story

The paper is strongest as a benchmark and evaluation paper, not as a claim that
one shield solves legal-agent truthfulness.

Defensible claims:

- SettlementEthicsGym creates controlled settlement settings with hidden facts,
  role-specific knowledge, bargaining utility, and truthfulness labels.
- Utility pressure and best-of-N selection can surface false or misleading
  negotiation statements.
- Deterministic evaluators and deterministic rewrite shields can overfit their
  own pattern rules.
- Detector-independent GPT-4.1 auditing finds blindspot failures that the
  deterministic evaluator misses, including in final transcript rows.
- A fact-grounded verifier shield reduces GPT-4.1 transcript flags on the
  blindspot split from 63/390 to 4/196, but does not eliminate them.

## Acceptance-Critical Tasks

1. Human/legal adjudication.
   - Adjudicate the 160 GPT-4.1-flagged mixed blindspot rows.
   - Prioritize the 63 GPT-4.1-flagged transcript rows.
   - Record adjudicator, adjudication date, label, severity, and notes.
   - Report judge-based rates separately from adjudicated rates until this is
     complete.

2. Replication reliability.
   - Finish the chunked seed-802 stress replication.
   - Summarize chunked results with Wilson intervals.
   - Keep failed monolithic jobs as infrastructure notes, not empirical results.

3. Claims table discipline.
   - Keep `paper/tables/headline_claims.csv` as the single source for headline
     denominators, rates, confidence intervals, evaluator source, and
     adjudication status.
   - Every paper claim about a rate should map to a row in that table or a
     named summary table.

4. Reviewer-facing limitations.
   - Be explicit that scenarios are synthetic.
   - Be explicit that LLM judges are not ground truth.
   - Be explicit that verifier shielding depends on a model judge at inference
     time and is a mitigation baseline, not a formal guarantee.

5. Presentation polish.
   - Move the paper from preliminary-result framing to final experiment framing.
   - Add a compact experiment matrix table.
   - Add a short method subsection for audit sampling and Wilson intervals.
   - Compile the ICML PDF and fix overfull boxes, table placement, and citation
     formatting.

## Nice-To-Have Tasks

- Add another stronger judge model if access and budget allow.
- Add 12-24 more hand-authored blindspot scenarios beyond economics-rescaled
  variants.
- Add a small manual error taxonomy for the remaining 4 verifier-shield flags.
- Add cost/latency reporting for verifier shielding.

## Do Not Claim

- Do not claim the benchmark determines real attorney discipline.
- Do not claim deterministic zero means zero misconduct.
- Do not claim GPT-4.1 labels are human labels.
- Do not claim verifier shielding solves safety.
- Do not claim acceptance depends on any single mitigation result.
