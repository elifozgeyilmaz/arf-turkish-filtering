#!/bin/bash
# ARF'ta ilk kurulum — login node'da bir kez çalıştır.
# GPU gerekmez, CPU'da çalışır.

set -euo pipefail

PROJECT_DIR="/arf/scratch/proj67/turkish-filtering"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Python sanal ortam
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install \
    "numpy<2" \
    datasets \
    huggingface_hub \
    pyarrow \
    fasttext-wheel \
    text-dedup

echo "Kurulum tamamlandı."
echo ""
echo "Sonraki adımlar:"
echo "  1. Proje dosyalarını kopyala:"
echo "     rsync -av --exclude='__pycache__' --exclude='.git' \\"
echo "       /local/turkish-oscar-cleaning/ $PROJECT_DIR/"
echo ""
echo "  2. FineWeb filtreleme başlat:"
echo "     sbatch --export=DATASET=fineweb slurm/filter.sh"
echo ""
echo "  3. CulturaX filtreleme başlat:"
echo "     sbatch --export=DATASET=culturax,HF_TOKEN=hf_xxx slurm/filter.sh"
echo ""
echo "  4. İkisi bitince dedup:"
echo "     sbatch slurm/dedup.sh"
