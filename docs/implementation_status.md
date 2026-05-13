# SettlementEthicsGym Implementation Status

Last updated: 2026-05-13

## Cluster Result Check

Local run artifacts show completed calibration runs under `runs/`:

- `runs/mvp_scripted/2026-05-12T082108Z_seed42`
- `runs/generated_scripted/2026-05-11T223959Z_seed43`
- `runs/best_of_n/2026-05-12T082042Z_seed123`
- `runs/llm_zero_shot/2026-05-12T115442Z_seed101`
- `runs/llm_ethics_prompt/2026-05-12T115741Z_seed102`
- `runs/llm_best_of_n/2026-05-12T115741Z_seed103`

The LLM-labeled runs are fake-model smoke tests. The zero-shot transcripts
record `provider: fake`; the ethics-prompt and LLM best-of-N metadata record
`fake_model_env: "1"`. They should not be used as empirical LLM results.

Athena status checked on 2026-05-13:

- `squeue -u joy` showed no active queued or running jobs.
- `sacct` for 2026-05-11 through 2026-05-14 showed many unrelated `safesae`
  jobs under `/work/joy/safesae-vla-eccv-rebuttal-run`.
- A read-only filesystem sweep checked the broad roots `/work`, `/scratch`,
  `/users`, `/athenahomes`, `/athena`, and `/tmp`, then a bounded pass checked
  the user roots `/work/joy`, `/scratch/joy`, `/scratch/users/joy`,
  `/users/joy`, `/athenahomes/joy`, and `/athena/joy`.
- The bounded pass found unrelated run directories such as
  `/work/joy/trak-traj/runs`, `/work/joy/trak-traj_wave16_20260408/runs`,
  `/work/joy/csdistillation_neurips_acceptance_20260502/repo/runs`, and
  `/users/joy/cotracker-rma/runs`, but no SettlementEthicsGym configs or result
  files.
- No additional SettlementEthicsGym result directory was found beyond the local
  repository artifacts.

## Current Evidence Quality

Current results are benchmark-plumbing and calibration evidence only.

- Scripted deceptive agents trigger deterministic violations as expected.
- Utility-only scripted best-of-N selects unsafe actions at N=4.
- Ethics-aware scripted best-of-N avoids deterministic violations.
- The rewrite shield avoids violations but currently loses substantial utility.
- Current LLM runs are fake and cannot support claims about real model behavior.

## Paper-Viable Implementation Queue

### Completed In This Pass

1. Candidate-level logging for best-of-N runs.
   - Store full selected and rejected candidate actions.
   - Store selected index, selector, utility estimate, violation count, and
     evaluator findings.
   - Emit `candidates.jsonl` per episode.
2. Utility-pressure LLM condition.
   - Added `segym/prompts/agent_utility_system.txt`.
   - Added `configs/exp_llm_utility_prompt.yaml`.
   - Verified the config with `scripts/run_experiment.py --dry-run`.
3. LLM shield condition.
   - Added `configs/exp_llm_shield.yaml`.
   - Updated the agent factory so `type: shielded` can wrap an LLM base while
     preserving provider, model, prompt, temperature, token limit, and fake-mode
     settings.
   - Added shield metadata to actions and episode summaries.
   - Added aggregate shield trigger metrics.
   - Verified with a fake-model end-to-end run.
4. LLM parse-failure handling and logging.
   - Added bounded retry for invalid action JSON.
   - Added a safe no-offer fallback after retry exhaustion.
   - Preserved raw malformed outputs and parser errors in transcript metadata.
   - Added episode summary fields for parse-failure counts.
   - Added aggregate parse-failure metrics.
   - Verified normal LLM, shielded LLM, and best-of-N fake-model paths.

### Next

1. Run real non-fake LLM experiment conditions.
   - Run without `SEGYN_FAKE_MODEL=1` and verify transcript metadata records
     a non-fake provider.

2. Implement LLM judge evaluator.
   - Scenario-aware JSON output.
   - Label, severity, confidence, rationale, mapped facts.
   - No deterministic label leakage outside ensemble/adjudication mode.

3. Implement audit tooling.
   - `scripts/make_audit_sample.py`
   - `scripts/evaluate_audit_labels.py`
   - `data/audit/audit_sample.csv`
   - `paper/tables/audit_agreement.csv`

4. Expand dataset.
   - At least 40 handwritten seed scenarios.
   - Split by scenario family.
   - Add held-out trap-category test split.
   - Add family-level source notes or explicit synthetic-only notes.

5. Add LLM best-of-N scaling.
   - N in `{1, 2, 4, 8, 16}`.
   - Utility-only, ethics-aware, hard-safe, and shielded controls.
   - Bootstrap confidence intervals.
   - `paper/figures/best_of_n_scaling.png`.

6. Make utility dynamics less saturated.
   - Current runs often settle immediately with client utility 1.0.
   - Add harder bargaining cases where truthful, deceptive, and controlled
     behavior create measurable utility differences.

7. Update paper claims and tables.
   - Keep current scripted results as calibration.
   - Add real model tables only after non-fake transcripts exist.
   - Report audit uncertainty and evaluator disagreement.

## Definition Of Done For Next Paper Milestone

- Real LLM transcripts for zero-shot, utility-prompt, ethics-prompt, LLM
  best-of-N utility, LLM best-of-N ethics-aware, and LLM shielded conditions.
- Candidate-level logs for all best-of-N episodes.
- At least one audit sample CSV covering selected and rejected candidate
  utterances.
- Expanded scenario set or explicit positioning as a small benchmark prototype.
- Paper tables generated from non-fake LLM outputs only.
