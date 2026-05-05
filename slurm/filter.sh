#!/bin/bash
# ============================================================
# FineWeb-2 veya CulturaX Türkçe filtreleme — SLURM job array
#
# Kullanım:
#   sbatch --export=DATASET=culturax,HF_TOKEN=hf_xxx slurm/filter.sh
#   sbatch --export=DATASET=fineweb               slurm/filter.sh
#
# DATASET ve HF_TOKEN dışarıdan verilmezse aşağıdaki defaults kullanılır.
# ============================================================
#SBATCH -p orfoz
#SBATCH -A proj67
#SBATCH -J tr_filter
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 60
#SBATCH --mem=120G
#SBATCH --time=12:00:00
# 50 paralel task — NUM_TASKS degiskeni ile eslesmeli
#SBATCH --array=0-49
#SBATCH --output=logs/filter_%x_%A_%a.out
#SBATCH --error=logs/filter_%x_%A_%a.err

set -euo pipefail

PROJECT_DIR="/arf/scratch/proj67/turkish-filtering"
cd "$PROJECT_DIR"
source .venv/bin/activate

DATASET="${DATASET:-fineweb}" 
HF_TOKEN="${HF_TOKEN:-}"  # sbatch --export=HF_TOKEN=hf_xxx ile ver
NUM_TASKS=50                    # --array üst sınırı + 1 ile eşleşmeli

OUTPUT_DIR="$PROJECT_DIR/${DATASET}_filtered"
DROPPED_DIR="$PROJECT_DIR/${DATASET}_dropped"
mkdir -p "$OUTPUT_DIR" "$DROPPED_DIR" logs/

echo "=== Job $SLURM_JOB_ID | Array task $SLURM_ARRAY_TASK_ID/$((NUM_TASKS-1)) | Node $(hostname) ==="
echo "Dataset : $DATASET"
echo "Output  : $OUTPUT_DIR"

python3 truba/filter_dataset.py \
    --dataset     "$DATASET" \
    --task_id     "$SLURM_ARRAY_TASK_ID" \
    --num_tasks   "$NUM_TASKS" \
    --output_dir  "$OUTPUT_DIR" \
    --dropped_dir "$DROPPED_DIR" \
    --hf_token    "$HF_TOKEN" \
    --num_proc    60

echo "=== Task $SLURM_ARRAY_TASK_ID tamamlandı ==="
