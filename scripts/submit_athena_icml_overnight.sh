#!/usr/bin/env bash
set -euo pipefail

cd /work/joy/seg
mkdir -p slurm paper/tables

KEY_PATH="${SEGYM_ATHENA_KEY_PATH:-/work/joy/.segym_openai_key_overnight}"
OPENROUTER_KEY_PATH="${SEGYM_OPENROUTER_KEY_PATH:-/work/joy/.segym_openrouter_key}"

if [[ ! -s "$KEY_PATH" ]]; then
  echo "Missing OpenAI key file: $KEY_PATH" >&2
  exit 1
fi

submit_experiment() {
  local job_name="$1"
  local config="$2"
  local split="$3"
  local output_dir="$4"
  local seed="$5"
  shift 5
  local dependency_args=("$@")
  sbatch --parsable "${dependency_args[@]}" --export=ALL,SEGYM_ATHENA_KEY_PATH="$KEY_PATH" <<SBATCH
#!/bin/bash
#SBATCH --job-name=${job_name}
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=18:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "\$SEGYM_ATHENA_KEY_PATH"
export OPENAI_API_KEY="\$(cat "\$SEGYM_ATHENA_KEY_PATH")"
export SEGYM_LLM_MODEL="\${SEGYM_LLM_MODEL:-gpt-4.1-mini}"
export SEGYM_HTTP_TRANSPORT="\${SEGYM_HTTP_TRANSPORT:-curl}"

run_with_retry() {
  local label="\$1"
  shift
  for attempt in 1 2 3; do
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

run_with_retry ${job_name} python scripts/run_experiment.py \\
  --config ${config} \\
  --scenario-split ${split} \\
  --output-dir ${output_dir} \\
  --seed ${seed}
SBATCH
}

submit_postprocess() {
  local job_name="$1"
  local seed="$2"
  local output_csv="$3"
  shift 3
  local dependency_args=("$@")
  sbatch --parsable "${dependency_args[@]}" <<SBATCH
#!/bin/bash
#SBATCH --job-name=${job_name}
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
python scripts/export_tables.py \\
  --run-dir runs/overnight_stress_core_seed${seed}_chunk01 \\
  --run-dir runs/overnight_stress_core_seed${seed}_chunk02 \\
  --run-dir runs/overnight_stress_core_seed${seed}_chunk03 \\
  --run-dir runs/overnight_stress_core_seed${seed}_chunk04 \\
  --format csv \\
  --out paper/tables/overnight_stress_core_seed${seed} \\
  --latest-only \\
  --require-real
python scripts/add_wilson_intervals.py \\
  --input paper/tables/overnight_stress_core_seed${seed}/main_results.csv \\
  --out ${output_csv}
SBATCH
}

seed804_jobs=()
for chunk in 01 02 03 04; do
  seed804_jobs+=("$(submit_experiment \
    "seg804-c${chunk}" \
    "configs/exp_llm_stress_core_replication_seed804.yaml" \
    "data/splits/generated_stress_v0_2_48_chunk${chunk}.txt" \
    "runs/overnight_stress_core_seed804_chunk${chunk}" \
    "804")")
done
seed804_dep=$(IFS=:; echo "${seed804_jobs[*]}")
post804=$(submit_postprocess \
  "seg804-post" \
  "804" \
  "paper/tables/overnight_stress_core_seed804_summary_wilson.csv" \
  "--dependency=afterany:${seed804_dep}")

seed805_jobs=()
for chunk in 01 02 03 04; do
  seed805_jobs+=("$(submit_experiment \
    "seg805-c${chunk}" \
    "configs/exp_llm_stress_core_replication_seed805.yaml" \
    "data/splits/generated_stress_v0_2_48_chunk${chunk}.txt" \
    "runs/overnight_stress_core_seed805_chunk${chunk}" \
    "805" \
    "--dependency=afterany:${post804}")")
done
seed805_dep=$(IFS=:; echo "${seed805_jobs[*]}")
post805=$(submit_postprocess \
  "seg805-post" \
  "805" \
  "paper/tables/overnight_stress_core_seed805_summary_wilson.csv" \
  "--dependency=afterany:${seed805_dep}")

verifier913=$(submit_experiment \
  "seg-vs913" \
  "configs/exp_llm_blindspot_verified_shield_seed913.yaml" \
  "data/splits/blindspot_stress_v0_2_24.txt" \
  "runs/overnight_blindspot_verified_shield_seed913" \
  "913" \
  "--dependency=afterany:${post805}")

verifier914=$(submit_experiment \
  "seg-vs914" \
  "configs/exp_llm_blindspot_verified_shield_seed914.yaml" \
  "data/splits/blindspot_stress_v0_2_24.txt" \
  "runs/overnight_blindspot_verified_shield_seed914" \
  "914" \
  "--dependency=afterany:${verifier913}")

nano_jobs=()
for chunk in 01 02 03 04; do
  nano_jobs+=("$(submit_experiment \
    "seg806n-c${chunk}" \
    "configs/exp_llm_stress_core_replication_gpt41_nano_seed806.yaml" \
    "data/splits/generated_stress_v0_2_48_chunk${chunk}.txt" \
    "runs/overnight_stress_core_gpt41_nano_seed806_chunk${chunk}" \
    "806" \
    "--dependency=afterany:${verifier914}")")
done

nonopen_job="skipped"
if [[ -s "$OPENROUTER_KEY_PATH" ]]; then
  nonopen_job=$(sbatch --parsable --dependency=afterany:"${post804}" --export=ALL,SEGYM_OPENROUTER_KEY_PATH="$OPENROUTER_KEY_PATH" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-claude-audit
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "$SEGYM_OPENROUTER_KEY_PATH"
export OPENROUTER_API_KEY="$(cat "$SEGYM_OPENROUTER_KEY_PATH")"
export SEGYM_HTTP_TRANSPORT="${SEGYM_HTTP_TRANSPORT:-curl}"
JUDGE_MODEL="${SEGYM_OPENROUTER_JUDGE_MODEL:-anthropic/claude-sonnet-4}"
JUDGE_BASE_URL="${SEGYM_OPENROUTER_BASE_URL:-https://openrouter.ai/api/v1/chat/completions}"
python scripts/evaluate_audit_labels.py \
  --audit-sample data/audit/blindspot_transcript_gpt41_flagged_multi_judge_rows.csv \
  --out paper/tables/blindspot_transcript_gpt41_flagged_agreement_judge_claude_sonnet4.csv \
  --predictions-out data/audit/blindspot_transcript_gpt41_flagged_predictions_judge_claude_sonnet4.csv \
  --scenario-disagreement-out paper/tables/blindspot_transcript_gpt41_flagged_disagreement_by_scenario_judge_claude_sonnet4.csv \
  --fact-category-disagreement-out paper/tables/blindspot_transcript_gpt41_flagged_disagreement_by_fact_category_judge_claude_sonnet4.csv \
  --llm-judge \
  --judge-model "$JUDGE_MODEL" \
  --judge-api-key-env OPENROUTER_API_KEY \
  --judge-base-url "$JUDGE_BASE_URL" \
  --judge-max-tokens 700 \
  --judge-timeout-seconds 90 \
  --judge-max-request-retries 4 \
  --checkpoint-every 10 \
  --resume-existing-judge
python scripts/evaluate_audit_labels.py \
  --audit-sample data/audit/verifier_shield_transcript_gpt41_flagged_multi_judge_rows.csv \
  --out paper/tables/verifier_shield_transcript_gpt41_flagged_agreement_judge_claude_sonnet4.csv \
  --predictions-out data/audit/verifier_shield_transcript_gpt41_flagged_predictions_judge_claude_sonnet4.csv \
  --scenario-disagreement-out paper/tables/verifier_shield_transcript_gpt41_flagged_disagreement_by_scenario_judge_claude_sonnet4.csv \
  --fact-category-disagreement-out paper/tables/verifier_shield_transcript_gpt41_flagged_disagreement_by_fact_category_judge_claude_sonnet4.csv \
  --llm-judge \
  --judge-model "$JUDGE_MODEL" \
  --judge-api-key-env OPENROUTER_API_KEY \
  --judge-base-url "$JUDGE_BASE_URL" \
  --judge-max-tokens 700 \
  --judge-timeout-seconds 90 \
  --judge-max-request-retries 4 \
  --checkpoint-every 2 \
  --resume-existing-judge
SBATCH
)
fi

echo "queued_seed804_chunks=${seed804_dep}"
echo "queued_seed804_post=${post804}"
echo "queued_seed805_chunks=${seed805_dep}"
echo "queued_seed805_post=${post805}"
echo "queued_verifier_seed913=${verifier913}"
echo "queued_verifier_seed914=${verifier914}"
echo "queued_nano_seed806_chunks=$(IFS=:; echo "${nano_jobs[*]}")"
echo "queued_nonopen_judge=${nonopen_job}"
squeue -u joy -o "%.18i %.9T %.10M %.20R %.40j" | grep -E "JOBID|seg804|seg805|seg-vs|seg806n|seg-claude" || true
