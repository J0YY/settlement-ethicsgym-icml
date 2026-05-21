# Acceptance Readiness Plan

Last updated: 2026-05-21

This document tracks the remaining work needed to make the paper defensible for
review. It does not guarantee acceptance; it lists the highest-risk reviewer
objections and the concrete implementation work needed to address them.

## ICML AI4Law Requirements Checked

Primary target: AI for Law Workshop @ ICML 2026 (`AI4Law`).

Primary sources checked on 2026-05-21:

- Official workshop page: https://sites.google.com/view/ai4law-icml2026
- OpenReview venue page: https://openreview.net/group?id=ICML.cc/2026/Workshop/AI4Law
- ICML 2026 conference page: https://icml.cc/

Submission constraints and fit:

- The CFP explicitly includes the intersection of artificial intelligence and
  law and lists `AI Evaluation for Law` / `AI Evaluations for Law` as a target
  theme. This paper should be framed first as a benchmark/evaluation paper.
- Submissions must be at most 8 pages excluding references and appendices.
  Current compiled PDF after the citation pass is 7 pages, including
  references.
- Submissions must be anonymous and use the ICML format. Current `main.tex`
  uses the ICML 2026 style and anonymous author block.
- Submissions are via OpenReview. OpenReview lists submission start
  2026-03-24 23:59 UTC and submission deadline 2026-05-22 23:59 UTC; the
  workshop site states the deadline as May 22, 2026 AoE.
- Previously published archival work is only considered for the non-archival
  track. This project should be submitted as original workshop work.

Reviewer expectation implied by the CFP: the paper must answer how legal AI
competence is built, evaluated, or validated in a way that generalizes across
legal systems and high-stakes legal settings. The strongest alignment is not
"a mitigation solves legal negotiation," but "deterministic legal-agent
evaluators can report zero while detector-independent semantic audits reveal
plausible false or misleading representations."

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

1. Label validation without human reviewers.
   - Treat external human/legal adjudication as optional future validation, not
     as required evidence for the paper.
   - Default, strict, and sensitive automated judge rubrics have been run over
     the 160 GPT-4.1-flagged mixed blindspot rows, the 63 transcript flags, and
     the 4 verifier-shield residual flags.
   - Report any-judge, majority-judge, unanimous-judge, and judge-disagreement
     rates with Wilson intervals.
   - Keep all automated judge rates separate from human or legal adjudication.
   - Independent o4-mini transcript audit completed for the 63 default-flagged
     rows and 4 verifier-shield residual rows.
   - Next highest-signal step: add a strong non-OpenAI judge or a small external
     expert review if feasible.

2. Replication reliability.
   - Chunked seed-802 stress replication is complete and summarized.
   - Add one more seed or model replication if budget allows.
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
   - Completed in the current draft: experiment matrix, audit-method paragraph,
     Wilson intervals, qualitative error examples, stronger related work, and
     expanded citations.

## Remaining Highest-Value Work Before Submission

These are ordered by expected review impact, not implementation difficulty.

1. Make the claim sharper in the final edit.
   - Lead every result section with evaluator scope: deterministic episode
     rates, GPT-4.1 row audit rates, multi-rubric sensitivity, o4-mini
     conservative subset.
   - Avoid unsupported language such as "LLMs commit legal misconduct at X%."
   - Prefer: "deterministic evaluator and shield can report zero while
     detector-independent semantic audits find plausible false or misleading
     representations."

2. Add a short appendix or supplementary README mapping artifacts to claims.
   - Table path, run path, evaluator, denominator, and figure/table in paper.
   - This reduces reviewer friction if they inspect the repo.

3. If time and API access permit, add one non-OpenAI judge or external legal
   review.
   - This is the main remaining threat to acceptance because current strong
     audits are mostly within one model family plus o4-mini.
   - If unavailable, say so explicitly and present the multi-rubric/o4-mini
     sensitivity as automated robustness, not adjudication.

4. Trim and polish the 8-page PDF.
   - The draft currently has one page of room under the workshop limit, but
     further content should still replace or compress text where possible.
   - Check for table overflow and citation formatting after every edit.

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
