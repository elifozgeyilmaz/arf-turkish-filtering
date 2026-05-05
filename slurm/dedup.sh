#!/bin/bash
#SBATCH -p smp
#SBATCH -A proj67
#SBATCH -J tr_dedup
#SBATCH -N 1
#SBATCH -n 1
# MinHash icin yuksek RAM gerekli
#SBATCH --mem=250G
#SBATCH -c 112
#SBATCH --time=24:00:00
#SBATCH --output=logs/dedup_%j.out
#SBATCH --error=logs/dedup_%j.err

set -euo pipefail

PROJECT_DIR="/arf/scratch/proj67/turkish-filtering"
cd "$PROJECT_DIR"
source .venv/bin/activate

FINEWEB_DIR="$PROJECT_DIR/fineweb_filtered"
CULTURAX_DIR="$PROJECT_DIR/culturax_filtered"
MERGED_DIR="$PROJECT_DIR/merged"
DEDUP_DIR="$PROJECT_DIR/deduped"
CACHE_DIR="$PROJECT_DIR/.cache_dedup"

mkdir -p "$MERGED_DIR" "$DEDUP_DIR" "$CACHE_DIR" logs/

echo "=== Dedup Job $SLURM_JOB_ID | Node $(hostname) ==="

python3 truba/dedup.py \
    --input_dirs "$FINEWEB_DIR" "$CULTURAX_DIR" \
    --merged_dir "$MERGED_DIR" \
    --output_dir "$DEDUP_DIR" \
    --cache_dir  "$CACHE_DIR" \
    --num_proc   112 \
    --num_perm   128 \
    --threshold  0.80 \
    --batch_size 10000

echo "=== Dedup tamamlandi ==="
echo "Istatistikler: $PROJECT_DIR/dedup_stats.json"
