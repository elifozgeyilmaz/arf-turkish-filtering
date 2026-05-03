# ARF Türkçe Filtreleme Pipeline — Terimler ve Kullanım

## Terimler

### SLURM
ARF'taki iş kuyruğu sistemi. Kime ne kadar CPU/RAM/süre verileceğini yönetir.
Sen iş gönderirsin, SLURM sıraya koyar, kaynak boşalınca otomatik başlatır.

### sbatch
SLURM'a iş göndermek için kullanılan komut.
```bash
sbatch slurm/filter.sh   # filter.sh'ı kuyruğa gönder
```
Komutu çalıştırınca terminal sana bir job ID verir ve biter — iş artık ARF'ta,
sen bağlantını kesebilirsin.

### Job
SLURM'a gönderdiğin bir çalışma birimi. Her `sbatch` komutu bir job oluşturur.
```
squeue -u $USER   # aktif job'larını listele
```

### Job Array
Tek bir `sbatch` komutuyla aynı scriptin birden fazla kopyasını çalıştırma yöntemi.
```bash
#SBATCH --array=0-49   # 50 kopya başlat (0, 1, 2, ..., 49)
```
Her kopya aynı script ama farklı `$SLURM_ARRAY_TASK_ID` değeriyle çalışır.
Biz bunu 50 farklı shard grubunu aynı anda işlemek için kullanıyoruz.

### Task
Job array'deki her bir kopya. `--array=0-49` dersen 50 task oluşur.
Her task kendi `SLURM_ARRAY_TASK_ID`'sini bilir (0, 1, 2, ..., 49)
ve bu numaraya göre hangi shard'ları işleyeceğine karar verir.

### Shard
HuggingFace'deki büyük datasetler yüzlerce küçük parquet dosyasına bölünmüş olarak saklanır.
Bu dosyaların her birine shard denir.

```
CulturaX Türkçe:
  tr/train-00000-of-01452.parquet   ← shard 0
  tr/train-00001-of-01452.parquet   ← shard 1
  ...
  tr/train-01451-of-01452.parquet   ← shard 1451
```

### Parquet
Kolonlu veri saklama formatı. CSV gibi ama çok daha hızlı ve sıkıştırılmış.
HuggingFace datasetleri parquet olarak dağıtılır.

### Partition
ARF'ta node gruplarının adı. Farklı donanımlara (GPU, CPU, yüksek RAM) göre ayrılmış.
```bash
#SBATCH -p kolyoz-cuda   # bu partition'a gönder
sinfo                    # mevcut partition'ları listele
```

---

## Pipeline Akışı

```
1. sbatch filter.sh (DATASET=fineweb)   ]
                                         }→ paralel çalışır
2. sbatch filter.sh (DATASET=culturax)  ]

        Her biri 50 task başlatır.
        Her task kendi shard grubunu işler.
        Her shard bitince hemen diske yazar (checkpoint).
        Job kesilirse aynı komutla kaldığı yerden devam eder.

3. sbatch dedup.sh
        fineweb_filtered/ + culturax_filtered/ → birleştirir → tekrarları atar
```

## Çıktı Dizin Yapısı

```
/arf/scratch/proj67/turkish-filtering/
├── fineweb_filtered/          ← filtreyi geçen belgeler (FineWeb)
│   ├── task_00000_shard_0000.parquet
│   ├── task_00000_shard_0001.parquet
│   └── ...
├── fineweb_dropped/           ← atılan belgeler (FineWeb)
├── culturax_filtered/         ← filtreyi geçen belgeler (CulturaX)
├── culturax_dropped/          ← atılan belgeler (CulturaX)
├── merged/                    ← ikisi birleştirilmiş
└── deduped/                   ← tekrar giderme sonrası final dataset
```

## Sık Kullanılan Komutlar

```bash
squeue -u $USER                      # aktif job'larını gör
scancel <JOB_ID>                     # job'ı iptal et
tail -f logs/filter_tr_filter_*.out  # canlı log izle
sinfo                                # partition'ları listele
```
