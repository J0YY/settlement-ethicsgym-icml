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

The early LLM-labeled local runs are fake-model smoke tests. The zero-shot
transcripts record `provider: fake`; the ethics-prompt and LLM best-of-N
metadata record `fake_model_env: "1"`. They should not be used as empirical LLM
results.

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

Real non-fake LLM matrix launched on Athena on 2026-05-13 completed as Slurm job
`677359` with exit code `0:0`. The run used `gpt-4.1-mini` through the
OpenAI-compatible provider and did not set fake mode. The result directories are:

- `/work/joy/seg/runs/llm_zero_shot/2026-05-13T134704Z_seed101`
- `/work/joy/seg/runs/llm_utility_prompt/2026-05-13T134949Z_seed104`
- `/work/joy/seg/runs/llm_ethics_prompt/2026-05-13T135151Z_seed102`
- `/work/joy/seg/runs/llm_shield/2026-05-13T135348Z_seed105`
- `/work/joy/seg/runs/llm_best_of_n/2026-05-13T135547Z_seed103`

## Current Evidence Quality

Current results are still prototype-scale evidence.

- Scripted deceptive agents trigger deterministic violations as expected.
- Utility-only scripted best-of-N selects unsafe actions at N=4.
- Ethics-aware scripted best-of-N avoids deterministic violations.
- The rewrite shield avoids violations but currently loses substantial utility.
- The first real LLM matrix ran successfully with zero parser failures, but it
  has only eight scenarios per condition.
- Utility-only best-of-N produced a material/severe violation in one of eight
  episodes while ethics-aware best-of-N produced none.
- The shield condition did not trigger in the first real matrix, so it is not
  yet an informative control.
- Utility and settlement dynamics remain noisy; the utility prompt underperformed
  in several episodes and needs prompt/opponent diagnostics before making claims.

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
5. Real LLM smoke and matrix execution.
   - Ran non-fake zero-shot, utility-prompt, ethics-prompt, shield, and
     best-of-N conditions on Athena.
   - Verified provider/model metadata and zero parse-failure rate.
   - Removed the temporary key file used for the run.
6. Real-run analysis guard.
   - Added analyzer support for multiple run roots.
   - Added `--latest-only` for timestamped experiment roots.
   - Added `--require-real` to reject missing metadata, fake-mode metadata,
     fake providers, and fake model configs before paper-table export.
7. LLM judge evaluator.
   - Added an OpenAI-compatible judge that returns validated `EthicsFinding`
     objects.
   - The judge prompt includes scenario facts but omits forbidden-pattern
     expected labels.
   - Added parser and prompt-boundary tests without external API calls.

### Next

1. Implement audit tooling.
   - `scripts/make_audit_sample.py`
   - `scripts/evaluate_audit_labels.py`
   - `data/audit/audit_sample.csv`
   - `paper/tables/audit_agreement.csv`

2. Improve stress/control conditions.
   - Add an adversarial utility prompt or stress configuration that reliably
     elicits unsafe candidate actions.
   - Ensure the shield has measurable trigger opportunities.
   - Add prompt/opponent diagnostics for utility-prompt episodes with low client
     utility.

3. Expand dataset.
   - At least 40 handwritten seed scenarios.
   - Split by scenario family.
   - Add held-out trap-category test split.
   - Add family-level source notes or explicit synthetic-only notes.

4. Add LLM best-of-N scaling.
   - N in `{1, 2, 4, 8, 16}`.
   - Utility-only, ethics-aware, hard-safe, and shielded controls.
   - Bootstrap confidence intervals.
   - `paper/figures/best_of_n_scaling.png`.

5. Make utility dynamics less saturated.
   - Current runs often settle immediately with client utility 1.0 or fail for
     reasons unrelated to truthfulness pressure.
   - Add harder bargaining cases where truthful, deceptive, and controlled
     behavior create measurable utility differences.

6. Update paper claims and tables.
   - Keep current scripted results as calibration.
   - Add real model tables only through `--require-real` exports.
   - Report audit uncertainty and evaluator disagreement.

7. Expand judge calibration once audit labels exist.
   - LLM judge precision/recall against audit.
   - Disagreement table by trap category.
   - Sensitivity table comparing deterministic-only, judge-only, and ensemble
     labels.

## Definition Of Done For Next Paper Milestone

- Real LLM transcripts for zero-shot, utility-prompt, ethics-prompt, LLM
  best-of-N utility, LLM best-of-N ethics-aware, and LLM shielded conditions.
- Candidate-level logs for all best-of-N episodes.
- At least one audit sample CSV covering selected and rejected candidate
  utterances.
- Expanded scenario set or explicit positioning as a small benchmark prototype.
- Paper tables generated from non-fake LLM outputs only.
