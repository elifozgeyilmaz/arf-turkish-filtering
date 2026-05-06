# Oturum Özeti — 7 Mayıs 2026

Bu belgede oturumda yapılan tüm değişiklikler ve **neden** yapıldıkları açıklanmaktadır.

---

## 1. FastText Dil Tespiti Eklenmesi

### Ne yaptık?
`filter_dataset.py`'e fasttext tabanlı Türkçe dil filtresi ekledik.

### Neden?
Daha önce scriptte bir TODO vardı:
```
#TODO 3 fasttext ile skor < 0.80 olanları filtreleyelim mi?
```
FineWeb-2 ve HPLT2 her ne kadar Türkçe etiketli olsa da içlerinde başka dillerde belgeler bulunabiliyor. Mevcut filtreler (stopword oranı, özel karakter oranı vb.) bunu yakalamak için yeterince güçlü değil. FastText'in dil tespit modeli bir metni okuyup "bu hangi dil ve ne kadar eminim?" diye bir skor döndürüyor. Biz Türkçe skoru 0.80'in altında olan belgeleri atıyoruz.

### Nasıl çalışıyor?
FastText, `lid.176.bin` adlı önceden eğitilmiş bir model kullanıyor. Bu model 176 dili tanıyabiliyor. Türkçe için `__label__tr` etiketini kullanıyor (ISO 639-1, 2 harfli kod — `__label__tur` değil).

```python
labels, scores = model.predict(line, k=1)
return labels[0] == "__label__tr" and scores[0] >= _FT_THRESHOLD
```

### Multiprocessing sorunu ve çözümü
`datasets.map()` birden fazla CPU core'u kullanıyor (bizde 56). Her core ayrı bir Python process'i. Eğer modeli global olarak yüklersek, fork sırasında her process kendi kopyasını alır — bu iyi. Ama modeli doğrudan yükleyip saklamak yerine **lazy loading** (tembel yükleme) yaptık:

```python
_FT_MODEL = None  # başlangıçta yok

def _get_ft_model():
    global _FT_MODEL
    if _FT_MODEL is None and _FT_MODEL_PATH:
        _FT_MODEL = fasttext.load_model(_FT_MODEL_PATH)
    return _FT_MODEL
```

Yani model, ilk kez ihtiyaç duyulduğunda yükleniyor. Her worker process bunu ayrı ayrı yapıyor. Bu multiprocessing ile uyumlu.

### Neden tam metne bakıyoruz, kırpmıyoruz?
İlk başta ilk 2000 karaktere bakıyorduk. Ama:
- FastText çok hızlı, uzun metinler için de milisaniye mertebesinde
- Kırpmak, başı farklı dilde (örn. İngilizce başlık) olan Türkçe belgeleri ıskalayabilir
- Doğruluk > hız önceliği bu filtrede

---

## 2. `_keep()` → `_drop_reason()` Dönüşümü ve Detaylı Loglama

### Ne yaptık?
`_keep(text)` fonksiyonu `True/False` döndürüyordu. Bunu `_drop_reason(text)` olarak değiştirdik — boş string döndürürse belgeyi tut, aksi halde atılma sebebini döndür.

### Neden?
Eski sistemde logda sadece şunu görüyorduk:
```
Shard 2: 45,231 → 31,847 kalan (70.4%)
```
Hangi filtrenin ne kadar belge attığını bilmiyorduk. FastText gerçekten çalışıyor mu? Stopword filtresi çok agresif mi? Bunları göremiyorduk.

Yeni sistemde her shard için şunu görüyoruz:
```
[task 3]  toplam: 45,231  kalan: 31,847  atılan: 13,384 (29.6%)
[task 3]    fasttext_dil          8,201  (18.1%)
[task 3]    kelime_sayisi         2,913   (6.4%)
[task 3]    dusuk_stopword        1,204   (2.7%)
[task 3]    kisa_satir              612   (1.4%)
[task 3]    flagged_kelime          234   (0.5%)
[task 3]    karakter_tekrari        130   (0.3%)
[task 3]    kelime_tekrari           90   (0.2%)
```

Eğer `fasttext_dil` satırı 0 görünürse model yüklenmemiş demektir, hemen fark ederiz.

### `_reason` kolonu neden dataset'e eklendi?
`shard["_reason"]` ile tüm belgelerin atılma sebeplerini bir liste olarak okuyabiliriz. `Counter()` ile sayıyoruz. Bu multiprocessing'de güvenli çünkü map işlemi bittikten sonra ana process'te yapılıyor.

```python
shard_reasons = Counter(shard["_reason"])
```

Son olarak `_keep` ve `_reason` kolonlarını parquet'e yazmadan önce siliyoruz — bunlar sadece iç hesaplama için.

---

## 3. HPLT2 Dataset Desteği

### Ne yaptık?
`DATASETS` sözlüğüne `hplt2` girişi ekledik, `--dataset` argümanına `hplt2` seçeneği ekledik.

### HPLT2 nedir?
High Performance Language Technologies 2.0 — büyük çok dilli web corpus'u. HuggingFace'de `HPLT/HPLT2.0_cleaned` repo'sunda. Türkçe dosyalar `tr_Latn` config'i altında (FineWeb-2'de `tur_Latn`, HPLT2'de `tr_Latn` — farklı kod, dikkat).

```python
"hplt2": {
    "repo_id": "HPLT/HPLT2.0_cleaned",
    "file_filter": lambda f: "tr_Latn" in f and f.endswith(".parquet"),
    "needs_token": False,
},
```

Token gerektirmiyor, herkese açık.

---

## 4. TRUBA Kurulumu

### Dosya transferi
TRUBA'ya dosya göndermek için `rsync` kullandık. Önemli nokta: `rsync` **yerel Mac terminalinden** çalıştırılır, TRUBA'dan değil.

```bash
rsync -avz /yerel/kaynak/ kullanici@sunucu:/uzak/hedef/
```

`-a` → arşiv modu (izinleri, zamanları korur)  
`-v` → verbose (ne transfer ettiğini göster)  
`-z` → sıkıştırarak gönder (daha hızlı)

### Home vs Scratch farkı
| | `/arf/home/eliyilmaz` | `/arf/scratch/proj67` |
|---|---|---|
| Amaç | Kodlar, config | Büyük veri, iş çıktıları |
| Kapasite | Küçük (~100GB) | Büyük (TB) |
| Kalıcılık | Kalıcı | 1 ay sonra silinir |

Kodları scratch'e koyduk çünkü çıktılarla aynı yerde olması kolaylık sağlıyor.

### Sanal ortam (virtual environment) nedir?
Python'da her proje için ayrı bir "izole paket kutusu". Sistem Python'una dokunmadan istediğin paketleri kurarsın. `ozge-venv` adını seçtik.

```bash
python3 -m venv ozge-venv     # oluştur
source ozge-venv/bin/activate  # aktif et (terminalde (ozge-venv) görünür)
pip install ...                # paket kur
```

---

## 5. Karşılaşılan Hatalar ve Çözümleri

### Hata 1: `rsync` yanlış yerden çalıştırıldı
**Sebep:** TRUBA terminalinde çalıştırıldı. Yerel Mac'teki dosyaları bulamadı.  
**Çözüm:** Mac terminalinde çalıştır.

### Hata 2: `rsync` hedef dizin yok
```
mkdir "/arf/scratch/.../truba" failed: No such file or directory
```
**Sebep:** rsync hedef dizini kendisi oluşturamaz.  
**Çözüm:** Önce `ssh` ile dizin oluştur, sonra rsync.
```bash
ssh eliyilmaz@172.16.6.11 "mkdir -p /arf/scratch/proj67/turkish-filtering/truba"
```

### Hata 3: sbatch — 56/112 çekirdek hatası
```
Orfoz kuyruguna gonderilen isleride node basina 56/112 cekirdek talep ediniz.
```
**Sebep:** Scriptte `-c 60` yazıyordu, orfoz partitionu 56 veya 112 istiyor.  
**Çözüm:** `-c 56` ve `--mem=112G` yaptık, `--num_proc 56`.

### Hata 4: sbatch — geçersiz account
```
Invalid account or account/partition combination specified
```
**Sebep:** Scriptte `-A proj67` yazıyordu ama gerçek account adı `eliyilmaz`.  
**Çözüm:** `-A eliyilmaz` yaptık. Account'ı öğrenmek için:
```bash
sacctmgr show user eliyilmaz withassoc format=account,partition
```

---

## 6. Gönderilen Job'lar

| Job ID | Dataset | Durum |
|--------|---------|-------|
| 5746341 | fineweb (FineWeb-2 tur_Latn) | Gönderildi |
| 5746344 | hplt2 (HPLT2.0 tr_Latn) | Gönderildi |

Her ikisi de 50 paralel task (`--array=0-49`), orfoz partitionu, 56 core, 112GB RAM, 12 saat limit.

### Job takibi
```bash
squeue -u eliyilmaz                          # durum
tail -f logs/filter_tr_filter_5746341_0.out  # canlı log (task 0)
scancel 5746341                              # iptal (gerekirse)
```

---

## 7. Mevcut Dizin Yapısı (TRUBA)

```
/arf/scratch/proj67/turkish-filtering/
├── truba/                   # kod repo'su
│   ├── filter_dataset.py    # ana filtreleme scripti
│   ├── slurm/filter.sh      # SLURM job scripti
│   ├── stopwords_tr.py
│   └── flagged_words_tr.py
├── ozge-venv/               # Python sanal ortamı
├── lid.176.bin              # FastText dil tespit modeli (125MB)
├── fineweb_filtered/        # FineWeb-2 filtrelenmiş çıktılar
├── fineweb_dropped/         # FineWeb-2 atılan belgeler
├── hplt2_filtered/          # HPLT2 filtrelenmiş çıktılar
├── hplt2_dropped/           # HPLT2 atılan belgeler
└── logs/                    # SLURM log dosyaları
```

---

## 8. Önemli Notlar

- **Restart güvenliği:** Bir shard'ın çıktısı zaten varsa script onu atlıyor. Job kesilse bile `sbatch` ile tekrar gönderince kaldığı yerden devam eder.
- **FastText modeli:** `--ft_model` verilmezse fasttext filtresi sessizce devre dışı kalıyor — geriye dönük uyumluluk bozulmuyor.
- **HPLT2 dosya yapısı:** İlk çalıştırmada `list_repo_files()` ile gerçek dosya yolları görünecek. Eğer `tr_Latn` pattern'i tutturmazsa log'da "Bu task için shard yok" yazar — `file_filter`'ı güncellemek gerekebilir.
