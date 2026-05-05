# Kod İnceleme Notları — Gökçenaz & Murat

Bu dosya pipeline'ı ilk kez inceleyenler için hazırlanmıştır. Açık sorular ve tartışılması gereken tasarım kararları aşağıda listelenmiştir.

---

## Pipeline'a Genel Bakış

```
FineWeb-2 (tur_Latn shardları)  ──┐
                                   ├─→ filter_dataset.py ──→ dedup.py ──→ final dataset
CulturaX (tr/ shardları)       ──┘
```

1. `sbatch slurm/filter.sh` — 50 paralel SLURM task'ı başlatır, her task kendi shard grubunu indirir ve filtreler, sonucu parquet olarak diske yazar. Job yarıda kesilirse kaldığı yerden devam eder (checkpoint var). SORU: 30 tane fineweb dosyası var, 50 task açmak mantıksız oldu, hplt'ye bakmadım kaç dosya var diye!
2. `sbatch slurm/dedup.sh` — Filtrelenen iki kaynağı birleştirir, MinHash (eşik 0.80) ile tekrarları atar, istatistikleri `dedup_stats.json`'a yazar.

Çıktı dizinleri: `/arf/scratch/proj67/turkish-filtering/`

---

## Filtreleme Kriterleri (`filter_dataset.py`)

| Filtre | Eşik | Notlar |
|--------|------|--------|
| Kısa satır oranı | > %30 satırda ≤ 3 kelime → at | Sadece ≥ 5 satırlı belgeler için geçerli |
| Kelime sayısı | 15 – 100.000 | Alt sınır net, **üst sınır tartışmalı** (bkz. Açık Sorular) |
| Uzun kelime | > 40 karakter → at | Encoding bozuklukları ve URL kalıntıları için |
| Karakter n-gram tekrarı | > %20 tekrar (n=10) → at | Boilerplate/spam tespiti |
| Kelime n-gram tekrarı | > %15 tekrar (n=5) → at | Boilerplate/spam tespiti |
| Özel karakter oranı | > %35 → at | |
| Stopword oranı | < %5 → at | Türkçe stopword listesi: `stopwords_tr.py` |
| Flagged word oranı | > %5 → at | Küfür/spam listesi: `flagged_words_tr.py` |

Metin ön işleme (`_modify`): HTML unescape → HTML tag temizleme → whitespace normalize → URL içeren token'ları at.

---

## Açık Sorular — Görüşünüzü Bekliyorum

### 1. Üst kelime sayısı sınırı (100.000)
`filter_dataset.py:87`'de `TODO` olarak işaretli.  
100.000 kelimelik belgeler web metninde nadiren meşru içerik olur (forum dump, concatenated pages).  
**Soru:** Bu sınırı daha agresif (örn. 50.000) yapalım mı, yoksa olduğu gibi bıraksın mı?

### 2. Flagged word oranı vs. kesin eşleşme (`filter_dataset.py:122`)
Şu an flagged kelime **oranı** kullanılıyor (%5 eşiği). Bazı çok kötü kelimeler için tek geçiş bile yeterliyken oranla kaçıyor olabilir.  
**Soru:** Bazı kelimeler için oran yerine "bu kelime varsa direkt at" mantığı eklenmeli mi? Hangi kelimeler?

### 3. FastText dil filtresi (`filter_dataset.py:17-19`)
Türkçe stopword oranı bir tür dil tespiti yapıyor ama ham bir yaklaşım. FastText `lid.176.bin` modeliyle skor < 0.80 olan belgeler atılabilir.  
**Soru:** Ekleyelim mi? Eğer eklenirse mevcut stopword filtresi gereksiz hale gelir mi?

### 4. FastText kalite sınıflandırıcısı (eğitim gerektirir)
İleride `__label__good / __label__bad` şeklinde ikili bir sınıflandırıcı eğitilebilir. Bunun için küçük etiketlenmiş bir Türkçe dataset lazım.  
**Soru:** Bunu önceliklendirelim mi? Varsa etiketleme için kaynak önerin?

### 5. Dedup eşiği (0.80 Jaccard)
`dedup.sh` → `dedup.py:128` — eşik şu an 0.80. Düşürürsek daha agresif dedup olur ama meşru benzer metinleri de atabiliriz.  
**Soru:** 0.80 uygun görünüyor mu? Literatürde Turkish corpora için öneri var mı?

---

## SLURM Kurulumu -> BU SEÇİMLERDEN HİÇ EMİN DEĞİLİM !!

| Script | Partition | Core | RAM | Süre |
|--------|-----------|------|-----|------|
| `slurm/filter.sh` | orfoz | 60 | 120 GB | 12 saat |
| `slurm/dedup.sh` | smp | 112 | 250 GB | 24 saat |

**Göndermek için:**
```bash
# FineWeb (token gerektirmez)
sbatch slurm/filter.sh

# CulturaX (HF token gerekli)
sbatch --export=DATASET=culturax,HF_TOKEN=hf_xxx slurm/filter.sh

# Filtreleme bittikten sonra
sbatch slurm/dedup.sh
```

**Log izlemek için:**
```bash
tail -f logs/filter_tr_filter_<JOB_ID>_<TASK_ID>.out
```

---

## Kodda Kalmış TODO'lar

| Dosya | Satır | Konu |
|-------|-------|------|
| `filter_dataset.py` | 86 | 100.000 kelime üst sınırı doğru mu? |
| `filter_dataset.py` | 122 | Flagged word: oran mı, kesin eşleşme mi? |
| `filter_dataset.py` | 17 | FastText dil filtresi eklenmeli mi? |
| `filter_dataset.py` | 18 | FastText kalite sınıflandırıcısı (eğitim gerektirir) |
