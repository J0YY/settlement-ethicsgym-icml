#!/usr/bin/env bash
set -euo pipefail

cd /work/joy/seg
mkdir -p slurm paper/tables

ANTHROPIC_KEY_PATH="${SEGYM_ANTHROPIC_KEY_PATH:-/work/joy/.segym_anthropic_key}"
if [[ ! -s "$ANTHROPIC_KEY_PATH" ]]; then
  echo "Missing Anthropic key file: $ANTHROPIC_KEY_PATH" >&2
  exit 1
fi

judge_job=$(sbatch --parsable --export=ALL,SEGYM_ANTHROPIC_KEY_PATH="$ANTHROPIC_KEY_PATH" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-claude-judge
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=06:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "$SEGYM_ANTHROPIC_KEY_PATH"
export ANTHROPIC_API_KEY="$(cat "$SEGYM_ANTHROPIC_KEY_PATH")"
export SEGYM_HTTP_TRANSPORT="${SEGYM_HTTP_TRANSPORT:-curl}"
JUDGE_MODEL="${SEGYM_CLAUDE_JUDGE_MODEL:-claude-sonnet-4-5}"

python scripts/evaluate_audit_labels.py \
  --audit-sample data/audit/blindspot_transcript_gpt41_flagged_multi_judge_rows.csv \
  --out paper/tables/blindspot_transcript_gpt41_flagged_agreement_judge_claude_sonnet.csv \
  --predictions-out data/audit/blindspot_transcript_gpt41_flagged_predictions_judge_claude_sonnet.csv \
  --scenario-disagreement-out paper/tables/blindspot_transcript_gpt41_flagged_disagreement_by_scenario_judge_claude_sonnet.csv \
  --fact-category-disagreement-out paper/tables/blindspot_transcript_gpt41_flagged_disagreement_by_fact_category_judge_claude_sonnet.csv \
  --llm-judge \
  --judge-provider anthropic \
  --judge-model "$JUDGE_MODEL" \
  --judge-api-key-env ANTHROPIC_API_KEY \
  --judge-base-url https://api.anthropic.com/v1/messages \
  --judge-max-tokens 900 \
  --judge-timeout-seconds 90 \
  --judge-max-request-retries 4 \
  --checkpoint-every 10 \
  --resume-existing-judge

python scripts/evaluate_audit_labels.py \
  --audit-sample data/audit/verifier_shield_transcript_gpt41_flagged_multi_judge_rows.csv \
  --out paper/tables/verifier_shield_transcript_gpt41_flagged_agreement_judge_claude_sonnet.csv \
  --predictions-out data/audit/verifier_shield_transcript_gpt41_flagged_predictions_judge_claude_sonnet.csv \
  --scenario-disagreement-out paper/tables/verifier_shield_transcript_gpt41_flagged_disagreement_by_scenario_judge_claude_sonnet.csv \
  --fact-category-disagreement-out paper/tables/verifier_shield_transcript_gpt41_flagged_disagreement_by_fact_category_judge_claude_sonnet.csv \
  --llm-judge \
  --judge-provider anthropic \
  --judge-model "$JUDGE_MODEL" \
  --judge-api-key-env ANTHROPIC_API_KEY \
  --judge-base-url https://api.anthropic.com/v1/messages \
  --judge-max-tokens 900 \
  --judge-timeout-seconds 90 \
  --judge-max-request-retries 4 \
  --checkpoint-every 2 \
  --resume-existing-judge
SBATCH
)

agent_jobs=()
for chunk in 01 02 03 04; do
  agent_jobs+=("$(sbatch --parsable --dependency=afterany:"$judge_job" --export=ALL,SEGYM_ANTHROPIC_KEY_PATH="$ANTHROPIC_KEY_PATH" <<SBATCH
#!/bin/bash
#SBATCH --job-name=seg-claude-c${chunk}
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=18:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "\$SEGYM_ANTHROPIC_KEY_PATH"
export ANTHROPIC_API_KEY="\$(cat "\$SEGYM_ANTHROPIC_KEY_PATH")"
export SEGYM_HTTP_TRANSPORT="\${SEGYM_HTTP_TRANSPORT:-curl}"
export SEGYM_CLAUDE_MODEL="\${SEGYM_CLAUDE_MODEL:-claude-sonnet-4-5}"

run_with_retry() {
  local label="\$1"
  shift
  for attempt in 1 2; do
    echo "START \${label} attempt=\${attempt} \$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if "\$@"; then
      echo "DONE \${label} attempt=\${attempt} \$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      return 0
    fi
    rc=\$?
    echo "FAILED \${label} attempt=\${attempt} rc=\${rc} \$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    sleep \$((120 * attempt))
  done
  return 1
}

run_with_retry claude-c${chunk} python scripts/run_experiment.py \\
  --config configs/exp_llm_stress_core_replication_claude_sonnet_seed901.yaml \\
  --scenario-split data/splits/generated_stress_v0_2_48_chunk${chunk}.txt \\
  --output-dir runs/overnight_stress_core_claude_sonnet_seed901_chunk${chunk} \\
  --seed 901
SBATCH
)")
done

agent_dep=$(IFS=:; echo "${agent_jobs[*]}")
post_job=$(sbatch --parsable --dependency=afterany:"$agent_dep" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-claude-post
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
python scripts/export_tables.py \
  --run-dir runs/overnight_stress_core_claude_sonnet_seed901_chunk01 \
  --run-dir runs/overnight_stress_core_claude_sonnet_seed901_chunk02 \
  --run-dir runs/overnight_stress_core_claude_sonnet_seed901_chunk03 \
  --run-dir runs/overnight_stress_core_claude_sonnet_seed901_chunk04 \
  --format csv \
  --out paper/tables/overnight_stress_core_claude_sonnet_seed901 \
  --latest-only \
  --require-real
python scripts/add_wilson_intervals.py \
  --input paper/tables/overnight_stress_core_claude_sonnet_seed901/main_results.csv \
  --out paper/tables/overnight_stress_core_claude_sonnet_seed901_summary_wilson.csv
SBATCH
)

echo "queued_claude_judge=${judge_job}"
echo "queued_claude_agent_chunks=${agent_dep}"
echo "queued_claude_post=${post_job}"
squeue -j "${judge_job},${agent_dep//:/,},${post_job}" -o "%.18i %.9T %.10M %.20R %.40j"
