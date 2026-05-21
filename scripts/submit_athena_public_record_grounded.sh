#!/usr/bin/env bash
set -euo pipefail

cd /work/joy/seg
mkdir -p slurm paper/tables

KEY_PATH="${SEGYM_ATHENA_KEY_PATH:-/work/joy/.segym_openai_key_overnight}"
if [[ ! -s "$KEY_PATH" ]]; then
  echo "Missing OpenAI key file: $KEY_PATH" >&2
  exit 1
fi

run_job=$(sbatch --parsable --export=ALL,SEGYM_ATHENA_KEY_PATH="$KEY_PATH" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-public-record
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=10:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "$SEGYM_ATHENA_KEY_PATH"
export OPENAI_API_KEY="$(cat "$SEGYM_ATHENA_KEY_PATH")"
export SEGYM_LLM_MODEL="${SEGYM_LLM_MODEL:-gpt-4.1-mini}"
export SEGYM_HTTP_TRANSPORT="${SEGYM_HTTP_TRANSPORT:-curl}"

run_with_retry() {
  local label="$1"
  shift
  for attempt in 1 2 3; do
    echo "START ${label} attempt=${attempt} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if "$@"; then
      echo "DONE ${label} attempt=${attempt} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      return 0
    fi
    rc=$?
    echo "FAILED ${label} attempt=${attempt} rc=${rc} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    sleep $((120 * attempt))
  done
  return 1
}

run_with_retry public-record python scripts/run_experiment.py --config configs/exp_llm_public_record_grounded_seed720.yaml --scenario-split data/splits/public_record_grounded_v0_1_12.txt --output-dir runs/llm_public_record_grounded_seed720 --seed 720
SBATCH
)

post_job=$(sbatch --parsable --dependency=afterany:"$run_job" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-public-post
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=01:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
python scripts/export_tables.py --run-dir runs/llm_public_record_grounded_seed720 --format csv --out paper/tables/llm_public_record_grounded_seed720 --latest-only --require-real
python scripts/add_wilson_intervals.py --input paper/tables/llm_public_record_grounded_seed720/main_results.csv --out paper/tables/llm_public_record_grounded_seed720_summary_wilson.csv
SBATCH
)

echo "queued_public_record_run=${run_job}"
echo "queued_public_record_post=${post_job}"
squeue -j "${run_job},${post_job}" -o "%.18i %.9T %.10M %.20R %.40j"
