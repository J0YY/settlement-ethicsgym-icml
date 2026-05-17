#!/usr/bin/env bash
set -euo pipefail

cd /work/joy/seg
mkdir -p slurm

KEY_PATH="${SEGYM_ATHENA_KEY_PATH:-/work/joy/.segym_openai_key_overnight}"

export SEGYM_ATHENA_KEY_PATH="$KEY_PATH"

jid1=$(sbatch --parsable --export=ALL,SEGYM_ATHENA_KEY_PATH="$KEY_PATH" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-n16-retry
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=30:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "$SEGYM_ATHENA_KEY_PATH"
export OPENAI_API_KEY="$(cat "$SEGYM_ATHENA_KEY_PATH")"
export SEGYM_LLM_MODEL="${SEGYM_LLM_MODEL:-gpt-4.1-mini}"
python - <<'PY'
from segym.agents.llm import OpenAICompatibleClient
OpenAICompatibleClient(model="gpt-4.1-mini", temperature=0, max_tokens=20).complete("Return only JSON.", "Return JSON: {\"ok\": true}")
print("model_probe_ok gpt-4.1-mini")
PY
run_with_retry() {
  label="$1"; shift
  for attempt in 1 2; do
    echo "START ${label} attempt=${attempt} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if "$@"; then
      echo "DONE ${label} attempt=${attempt} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      return 0
    fi
    rc=$?
    echo "FAILED ${label} attempt=${attempt} rc=${rc} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    sleep 120
  done
  return 1
}
run_with_retry n16_retry python scripts/run_experiment.py \
  --config configs/exp_llm_stress_best_of_n_scaling_n16.yaml \
  --scenario-split data/splits/generated_stress_v0_2_48.txt \
  --output-dir runs/paper48_bon_scaling_n16_retry \
  --seed 511
SBATCH
)

jid2=$(sbatch --parsable --dependency=afterany:"$jid1" --export=ALL,SEGYM_ATHENA_KEY_PATH="$KEY_PATH" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-shield-retry
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=18:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "$SEGYM_ATHENA_KEY_PATH"
export OPENAI_API_KEY="$(cat "$SEGYM_ATHENA_KEY_PATH")"
export SEGYM_LLM_MODEL="${SEGYM_LLM_MODEL:-gpt-4.1-mini}"
python scripts/run_experiment.py \
  --config configs/exp_llm_stress_shield_ablation.yaml \
  --scenario-split data/splits/generated_stress_v0_2_48.txt \
  --output-dir runs/paper48_shield_ablation \
  --seed 312
SBATCH
)

jid3=$(sbatch --parsable --dependency=afterany:"$jid2" --export=ALL,SEGYM_ATHENA_KEY_PATH="$KEY_PATH" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-lambda-retry
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=24:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "$SEGYM_ATHENA_KEY_PATH"
export OPENAI_API_KEY="$(cat "$SEGYM_ATHENA_KEY_PATH")"
export SEGYM_LLM_MODEL="${SEGYM_LLM_MODEL:-gpt-4.1-mini}"
python scripts/run_experiment.py \
  --config configs/exp_llm_stress_ethics_lambda_sweep_n8.yaml \
  --scenario-split data/splits/generated_stress_v0_2_48.txt \
  --output-dir runs/paper48_lambda_sweep_n8 \
  --seed 313
SBATCH
)

jid4=$(sbatch --parsable --dependency=afterany:"$jid3" --export=ALL,SEGYM_ATHENA_KEY_PATH="$KEY_PATH" <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=seg-cross-nano-retry
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=30:00:00
#SBATCH --output=/work/joy/seg/slurm/%x-%j.out
set -euo pipefail
cleanup() { rm -f "$SEGYM_ATHENA_KEY_PATH"; }
trap cleanup EXIT
cd /work/joy/seg
source ~/miniconda3/etc/profile.d/conda.sh
conda activate segym
test -s "$SEGYM_ATHENA_KEY_PATH"
export OPENAI_API_KEY="$(cat "$SEGYM_ATHENA_KEY_PATH")"
if python - <<'PY'
from segym.agents.llm import OpenAICompatibleClient
OpenAICompatibleClient(model="gpt-4.1-nano", temperature=0, max_tokens=20).complete("Return only JSON.", "Return JSON: {\"ok\": true}")
print("model_probe_ok gpt-4.1-nano")
PY
then
  python scripts/run_experiment.py \
    --config configs/exp_llm_stress_cross_model_gpt41_nano_core.yaml \
    --scenario-split data/splits/generated_stress_v0_2_48.txt \
    --output-dir runs/paper48_cross_model_gpt41_nano_core \
    --seed 314
else
  echo "SKIP cross_model_gpt41_nano_core: model probe failed"
fi
SBATCH
)

echo "queued_n16_retry=${jid1}"
echo "queued_shield_retry=${jid2}"
echo "queued_lambda_retry=${jid3}"
echo "queued_cross_nano_retry=${jid4}"
squeue -j "${jid1},${jid2},${jid3},${jid4}" -o "%.18i %.9T %.10M %.20R %.40j"
