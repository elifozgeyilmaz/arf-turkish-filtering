#!/usr/bin/env python3
"""
Merge + MinHash deduplication + istatistik raporu.

Kullanım:
  python dedup.py \\
    --input_dirs /arf/scratch/proj67/turkish-filtering/fineweb_filtered \\
                 /arf/scratch/proj67/turkish-filtering/culturax_filtered \\
    --merged_dir /arf/scratch/proj67/turkish-filtering/merged \\
    --output_dir /arf/scratch/proj67/turkish-filtering/deduped \\
    --cache_dir  /arf/scratch/proj67/turkish-filtering/.cache_dedup \\
    --num_proc   60
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime


def merge(input_dirs, merged_dir, num_proc):
    """Filtrelenmiş shard dosyalarını tek bir dataset'e birleştir."""
    from datasets import load_dataset

    all_files = []
    for d in input_dirs:
        files = sorted(glob.glob(os.path.join(d, "task_*_shard_*.parquet")))
        print(f"  {d}: {len(files)} shard dosyası")
        all_files.extend(files)

    if not all_files:
        raise RuntimeError("Hiç parquet dosyası bulunamadı. Filtreleme tamamlandı mı?")

    print(f"  Toplam {len(all_files)} dosya yükleniyor...")
    dataset = load_dataset("parquet", data_files=all_files, split="train", num_proc=num_proc)
    print(f"  Toplam örnek: {len(dataset):,}")

    os.makedirs(merged_dir, exist_ok=True)
    dataset.save_to_disk(merged_dir, num_proc=num_proc)
    return len(dataset)


def run_minhash(merged_dir, output_dir, cache_dir, num_perm, threshold, batch_size, num_proc):
    """text-dedup MinHash deduplication'ı subprocess olarak çalıştır."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    cmd = [
        sys.executable, "-m", "text_dedup.minhash",
        "--path",       merged_dir,
        "--split",      "train",
        "--cache_dir",  cache_dir,
        "--output",     output_dir,
        "--column",     "text",
        "--num_perm",   str(num_perm),
        "--threshold",  str(threshold),
        "--batch_size", str(batch_size),
        "--num_proc",   str(num_proc),
    ]

    print(f"  Komut: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True)
    return result.returncode


def print_stats(merged_dir, output_dir, input_dirs, elapsed, stats_path):
    """Dedup öncesi/sonrası istatistikleri hesapla, yazdır ve JSON'a kaydet."""
    from datasets import load_from_disk

    merged  = load_from_disk(merged_dir)
    deduped = load_from_disk(output_dir)

    n_merged  = len(merged)
    n_deduped = len(deduped)
    n_removed = n_merged - n_deduped
    dup_rate  = n_removed / n_merged * 100 if n_merged else 0

    # Kaynak bazlı belge sayıları (filtreleme çıktısından)
    source_counts = {}
    for d in input_dirs:
        files = sorted(glob.glob(os.path.join(d, "task_*_shard_*.parquet")))
        name  = os.path.basename(d).replace("_filtered", "")
        source_counts[name] = len(files)

    stats = {
        "tarih"              : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "toplam_sure_sn"     : round(elapsed, 1),
        "merge_oncesi"       : n_merged,
        "dedup_sonrasi"      : n_deduped,
        "atilan"             : n_removed,
        "tekrar_orani_yuzde" : round(dup_rate, 2),
        "minhash_esigi"      : 0.80,
        "kaynaklar"          : source_counts,
    }

    print("\n" + "=" * 50)
    print("  DEDUPLICATION SONUÇLARI")
    print("=" * 50)
    print(f"  Birleşik dataset   : {n_merged:>12,}")
    print(f"  Dedup sonrası      : {n_deduped:>12,}")
    print(f"  Atılan (tekrar)    : {n_removed:>12,}  ({dup_rate:.1f}%)")
    print(f"  Toplam süre        : {elapsed:.0f}s")
    print("=" * 50)

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\n  İstatistikler kaydedildi → {stats_path}")


def main():
    parser = argparse.ArgumentParser(description="Merge + MinHash dedup + istatistik")
    parser.add_argument("--input_dirs",  nargs="+", required=True,
                        help="Filtrelenmiş shard dosyalarının dizinleri")
    parser.add_argument("--merged_dir",  type=str, required=True,
                        help="Birleştirilmiş dataset'in kaydedileceği dizin")
    parser.add_argument("--output_dir",  type=str, required=True,
                        help="Dedup sonrası final dataset")
    parser.add_argument("--cache_dir",   type=str, required=True,
                        help="MinHash ara dosyaları için cache dizini")
    parser.add_argument("--num_proc",    type=int, default=os.cpu_count())
    parser.add_argument("--num_perm",    type=int, default=128,
                        help="MinHash permutasyon sayısı (yüksek = daha doğru, yavaş)")
    parser.add_argument("--threshold",   type=float, default=0.80,
                        help="Jaccard benzerlik eşiği (0.80 = %%80 benzer → tekrar say)")
    parser.add_argument("--batch_size",  type=int, default=10000)
    parser.add_argument("--skip_merge",  action="store_true",
                        help="Merge zaten yapıldıysa atla, doğrudan dedup'a geç")
    args = parser.parse_args()

    stats_path = os.path.join(os.path.dirname(args.output_dir), "dedup_stats.json")
    t0         = time.time()

    # ---- 1. Merge ----
    if args.skip_merge:
        print("[1/3] Merge atlanıyor (--skip_merge).")
    else:
        print("[1/3] Shard dosyaları birleştiriliyor...")
        n = merge(args.input_dirs, args.merged_dir, args.num_proc)
        print(f"  Merge tamamlandı: {n:,} örnek\n")

    # ---- 2. MinHash Deduplication ----
    print("[2/3] MinHash deduplication çalışıyor...")
    print(f"  Eşik (threshold) : {args.threshold}  (Jaccard benzerliği)")
    print(f"  Permutasyon      : {args.num_perm}")
    run_minhash(
        args.merged_dir, args.output_dir, args.cache_dir,
        args.num_perm, args.threshold, args.batch_size, args.num_proc,
    )
    print()

    # ---- 3. İstatistikler ----
    print("[3/3] İstatistikler hesaplanıyor...")
    elapsed = time.time() - t0
    print_stats(args.merged_dir, args.output_dir, args.input_dirs, elapsed, stats_path)


if __name__ == "__main__":
    main()
