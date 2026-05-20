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

The main GPT-4.1-flagged blindspot rows now have three-rubric GPT-4.1
sensitivity checks:

- `paper/tables/blindspot_mixed_gpt41_flagged_multi_judge_summary.csv`
- `paper/tables/blindspot_transcript_gpt41_flagged_multi_judge_summary.csv`
- `paper/tables/verifier_shield_transcript_gpt41_flagged_multi_judge_summary.csv`

These are robustness checks over the default-flagged rows, not prevalence
estimates over all rows. The mixed blindspot flagged rows have 152/160
majority-rubric support; transcript flagged rows have 58/63 majority-rubric
support; verifier-shield residual rows have 4/4 majority-rubric support but
only 1/4 unanimous-rubric support.

The next strongest validation step is a strong non-GPT-4.1 judge or a small
external expert review. Do not use GPT-4.1 rubric variants as independent human
or legal adjudication.
