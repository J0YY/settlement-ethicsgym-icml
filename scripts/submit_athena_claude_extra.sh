#!/usr/bin/env bash
set -euo pipefail

cd /work/joy/seg
mkdir -p slurm paper/tables

ANTHROPIC_KEY_PATH="${SEGYM_ANTHROPIC_KEY_PATH:-/work/joy/.segym_anthropic_key}"
AFTER_JOB="${SEGYM_AFTER_JOB:-}"
if [[ ! -s "$ANTHROPIC_KEY_PATH" ]]; then
  echo "Missing Anthropic key file: $ANTHROPIC_KEY_PATH" >&2
  exit 1
fi

dependency_arg=()
if [[ -n "$AFTER_JOB" ]]; then
  dependency_arg=("--dependency=afterany:${AFTER_JOB}")
fi

submit_experiment() {
  local job_name="$1"
  local config="$2"
  local split="$3"
  local output_dir="$4"
  local seed="$5"
  shift 5
  local dependency_args=("$@")
  sbatch --parsable "${dependency_args[@]}" --export=ALL,SEGYM_ANTHROPIC_KEY_PATH="$ANTHROPIC_KEY_PATH" <<SBATCH
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

run_with_retry ${job_name} python scripts/run_experiment.py --config ${config} --scenario-split ${split} --output-dir ${output_dir} --seed ${seed}
SBATCH
}

submit_postprocess() {
  local job_name="$1"
  local seed="$2"
  local table_dir="$3"
  local output_csv="$4"
  shift 4
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
  --run-dir runs/overnight_stress_core_claude_sonnet_seed${seed}_chunk01 \\
  --run-dir runs/overnight_stress_core_claude_sonnet_seed${seed}_chunk02 \\
  --run-dir runs/overnight_stress_core_claude_sonnet_seed${seed}_chunk03 \\
  --run-dir runs/overnight_stress_core_claude_sonnet_seed${seed}_chunk04 \\
  --format csv \\
  --out ${table_dir} \\
  --latest-only \\
  --require-real
python scripts/add_wilson_intervals.py \\
  --input ${table_dir}/main_results.csv \\
  --out ${output_csv}
SBATCH
}

seed902_jobs=()
for chunk in 01 02 03 04; do
  seed902_jobs+=("$(submit_experiment \
    "seg-c902-c${chunk}" \
    "configs/exp_llm_stress_core_replication_claude_sonnet_seed902.yaml" \
    "data/splits/generated_stress_v0_2_48_chunk${chunk}.txt" \
    "runs/overnight_stress_core_claude_sonnet_seed902_chunk${chunk}" \
    "902" \
    "${dependency_arg[@]}")")
done
seed902_dep=$(IFS=:; echo "${seed902_jobs[*]}")
post902=$(submit_postprocess \
  "seg-c902-post" \
  "902" \
  "paper/tables/overnight_stress_core_claude_sonnet_seed902" \
  "paper/tables/overnight_stress_core_claude_sonnet_seed902_summary_wilson.csv" \
  "--dependency=afterany:${seed902_dep}")

seed903_jobs=()
for chunk in 01 02 03 04; do
  seed903_jobs+=("$(submit_experiment \
    "seg-c903-c${chunk}" \
    "configs/exp_llm_stress_core_replication_claude_sonnet_seed903.yaml" \
    "data/splits/generated_stress_v0_2_48_chunk${chunk}.txt" \
    "runs/overnight_stress_core_claude_sonnet_seed903_chunk${chunk}" \
    "903" \
    "--dependency=afterany:${post902}")")
done
seed903_dep=$(IFS=:; echo "${seed903_jobs[*]}")
post903=$(submit_postprocess \
  "seg-c903-post" \
  "903" \
  "paper/tables/overnight_stress_core_claude_sonnet_seed903" \
  "paper/tables/overnight_stress_core_claude_sonnet_seed903_summary_wilson.csv" \
  "--dependency=afterany:${seed903_dep}")

blindspot_job=$(submit_experiment \
  "seg-c904-blind" \
  "configs/exp_llm_blindspot_stress_bon_claude_sonnet_seed904.yaml" \
  "data/splits/blindspot_stress_v0_2_24.txt" \
  "runs/overnight_blindspot_stress_bon_claude_sonnet_seed904" \
  "904" \
  "--dependency=afterany:${post903}")

verified_job=$(submit_experiment \
  "seg-c915-vs" \
  "configs/exp_llm_blindspot_verified_shield_claude_sonnet_seed915.yaml" \
  "data/splits/blindspot_stress_v0_2_24.txt" \
  "runs/overnight_blindspot_verified_shield_claude_sonnet_seed915" \
  "915" \
  "--dependency=afterany:${blindspot_job}")

echo "queued_claude_seed902_chunks=${seed902_dep}"
echo "queued_claude_seed902_post=${post902}"
echo "queued_claude_seed903_chunks=${seed903_dep}"
echo "queued_claude_seed903_post=${post903}"
echo "queued_claude_blindspot_seed904=${blindspot_job}"
echo "queued_claude_verified_shield_seed915=${verified_job}"
squeue -j "${seed902_dep//:/,},${post902},${seed903_dep//:/,},${post903},${blindspot_job},${verified_job}" -o "%.18i %.9T %.10M %.20R %.40j"
