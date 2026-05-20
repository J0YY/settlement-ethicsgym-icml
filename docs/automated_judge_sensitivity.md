# Automated Judge Sensitivity Plan

External human or legal adjudication is not currently available. Do not report
LLM-judge outputs as human labels.

## Replacement Evidence

Use automated sensitivity checks:

- deterministic evaluator as a replayable lower-bound measurement;
- GPT-4.1 default-rubric judge as the main detector-independent audit;
- GPT-4.1 strict-rubric judge as a conservative automated audit;
- GPT-4.1 sensitive-rubric judge as an upper-sensitivity audit;
- a second model judge when access is reliable.

Report any-judge, majority-judge, unanimous-judge, and judge-disagreement rates
with Wilson intervals. Keep these rows under
`automated_multi_judge_sensitivity` in `paper/tables/headline_claims.csv`.

## Current Status

`paper/tables/paper48_stratified_multi_judge_summary.csv` aggregates the
available GPT-4.1 and GPT-4.1-nano stratified-audit outputs. The panel produces
an any-judge rate of 107/400 and majority/unanimous rates of 0/400, showing
that the nano judge is a low-sensitivity bound rather than adjudicated truth.

The main blindspot outputs still need additional strong judge passes before
multi-judge majority or unanimous claims should be made:

- `data/audit/blindspot_stress_bon_audit_sample.csv`
- `data/audit/blindspot_stress_bon_transcript_audit_sample.csv`
- `data/audit/blindspot_verified_shield_transcript_audit_sample.csv`

Use `scripts/evaluate_audit_labels.py --llm-judge --judge-rubric strict` and
`--judge-rubric sensitive`, then aggregate with
`scripts/aggregate_multi_judge_audit.py`.
