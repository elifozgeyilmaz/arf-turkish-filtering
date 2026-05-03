#!/usr/bin/env python3
"""
Filtrelenmiş parquet dosyalarını HuggingFace dataset formatında birleştirir.

Kullanım:
  python merge.py \\
    --input_dirs /arf/scratch/.../fineweb_filtered /arf/scratch/.../culturax_filtered \\
    --output_dir /arf/scratch/.../merged \\
    --num_proc 60
"""

import argparse
import glob
import os

from datasets import concatenate_datasets, load_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dirs", nargs="+", required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--num_proc",   type=int, default=os.cpu_count())
    args = parser.parse_args()

    all_files = []
    for d in args.input_dirs:
        # task_XXXXX_shard_YYYY.parquet formatını yakala
        files = sorted(glob.glob(os.path.join(d, "task_*_shard_*.parquet")))
        print(f"{d}: {len(files)} shard dosyası bulundu")
        all_files.extend(files)

    if not all_files:
        raise RuntimeError("Hiç parquet dosyası bulunamadı.")

    print(f"Toplam {len(all_files)} dosya yükleniyor...")
    dataset = load_dataset("parquet", data_files=all_files, split="train", num_proc=args.num_proc)
    print(f"Toplam örnek: {len(dataset):,}")

    os.makedirs(args.output_dir, exist_ok=True)
    dataset.save_to_disk(args.output_dir, num_proc=args.num_proc)
    print(f"Kaydedildi → {args.output_dir}")


if __name__ == "__main__":
    main()
