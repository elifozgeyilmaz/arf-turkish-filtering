#!/bin/bash
# ============================================================
# MinHash deduplication — filtrelenmiş FineWeb + CulturaX birleşimi
# text-dedup kütüphanesi kullanır.
#
# Kullanım (filtreleme job'ları bittikten sonra):
#   sbatch slurm/dedup.sh
# ============================================================
# CPU partition varsa degistir
#SBATCH -p kolyoz-cuda
#SBATCH -A proj67
#SBATCH -J tr_dedup
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 60
# MinHash icin yuksek RAM gerekli
#SBATCH --mem=250G
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

# ---- 1. Merge ----
echo "[1/3] FineWeb + CulturaX birleştiriliyor → $MERGED_DIR"
python3 truba/merge.py \
    --input_dirs "$FINEWEB_DIR" "$CULTURAX_DIR" \
    --output_dir "$MERGED_DIR" \
    --num_proc 60

# ---- 2. MinHash deduplication ----
echo "[2/3] MinHash deduplication çalışıyor..."
python -m text_dedup.minhash \
    --path        "$MERGED_DIR" \
    --split       train \
    --cache_dir   "$CACHE_DIR" \
    --output      "$DEDUP_DIR" \
    --column      text \
    --num_perm    128 \
    --threshold   0.80 \
    --batch_size  10000 \
    --num_proc    60

# ---- 3. Özet ----
echo "[3/3] Tamamlandı."
python3 -c "
from datasets import load_from_disk
merged = load_from_disk('$MERGED_DIR')
deduped = load_from_disk('$DEDUP_DIR')
removed = len(merged) - len(deduped)
print(f'Birleşik  : {len(merged):,}')
print(f'Dedup sonrası: {len(deduped):,}')
print(f'Atılan    : {removed:,}  ({removed/len(merged)*100:.1f}%)')
"
