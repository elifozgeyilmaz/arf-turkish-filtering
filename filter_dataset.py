#!/usr/bin/env python3
"""
FineWeb-2 veya CulturaX Türkçe datasetini SLURM job array ile filtreler.

Her task, toplam shard listesinin 1/num_tasks kadarını işler ve
ayrı bir parquet dosyasına yazar.

Kullanım:
  python filter_dataset.py \\
    --dataset culturax \\
    --task_id $SLURM_ARRAY_TASK_ID \\
    --num_tasks 50 \\
    --output_dir /arf/scratch/proj67/turkish-filtering/culturax_filtered \\
    --hf_token $HF_TOKEN \\
    --num_proc 60
"""
#TODO 4 fasttexti eğitebiliriz, küçük bir etiketlenmiş dataset lazım , örnek:
# Format: __label__good Ankara Türkiye'nin başkentidir. / __label__bad sdfhcshvfsf. -> binary classifier
import argparse
import html
import os
import re
import string
import time
from collections import Counter

from datasets import load_dataset
from huggingface_hub import HfApi, login

# Word listeleri ana dizinden import et
from stopwords_tr import stopwords_tr
from flagged_words_tr import flagged_words_tr

# ---------------------------------------------------------------------------
# Karakter seti
# ---------------------------------------------------------------------------
_main_special = string.punctuation + string.digits + string.whitespace
_other_special = (
    "    　    ￼‘’“”–ー一▬…✦"
    "�\xad\xa3​•€\xab\xbb\xb0\xb7═"
    "\xd7\xb1＾˘⇓↓↑←→（）"
    "\xa7″′\xb4\xbf−\xb1∈﻿\xa2\xf8‚"
    "„\xbd\xbc\xbe\xb9\xb2\xb3―⁃，ˌ\xb8"
    "‹›ʺˈʻ\xa6‐⠀‰‑"
    "≤≥‖◆●■►▼▲▴"
    "∆▻\xa1★☆✱ː\xba。\xaf˜"
    "\xa5ɪ≈†上ン：∼⁄・"
    "♡✓⊕।．⋅\xf7１‟；"
    "،、\xa8"
)

SPECIAL_CHARS = set(_main_special + _other_special)

_STOPWORDS = frozenset(w.lower() for w in stopwords_tr)
_FLAGGED   = frozenset(w.lower() for w in flagged_words_tr)

# ---------------------------------------------------------------------------
# FastText dil tespiti
# ---------------------------------------------------------------------------
_FT_MODEL = None
_FT_MODEL_PATH = None
_FT_THRESHOLD = 0.80


def _get_ft_model():
    global _FT_MODEL
    if _FT_MODEL is None and _FT_MODEL_PATH:
        import fasttext
        fasttext.FastText.eprint = lambda x: None  # model uyarılarını bastır
        _FT_MODEL = fasttext.load_model(_FT_MODEL_PATH)
    return _FT_MODEL


def _is_turkish(text: str) -> bool:
    model = _get_ft_model()
    if model is None:
        return True  # model verilmemişse filtreyi atla
    # lid.176.bin ISO 639-1 kullanır → Türkçe etiketi "tr"
    line = text.replace("\n", " ")
    labels, scores = model.predict(line, k=1)
    return labels[0] == "__label__tr" and scores[0] >= _FT_THRESHOLD


# ---------------------------------------------------------------------------
# Filtreleme fonksiyonları
# ---------------------------------------------------------------------------

def _get_words(text):
    strip_str = "".join(SPECIAL_CHARS)
    return [w for w in (w.strip(strip_str) for w in text.split()) if w]

#html unescape ne yapar --> > bu karakteri html tagi içinde yazamayız, onun yerine  &gt kullanırız, bu fonksiyon onları dönüştürüyor. Diğer örnekler: &amp→& vs.    
def _modify(text):
    text = html.unescape(text)                     # &amp; → &, &lt; → <, &nbsp; → boşluk
    text = re.sub(r"<[^>]+>", " ", text)           # <div>, <p>, <br> gibi tag'leri siler nasıl: re.sub regex ile bul-değiştir yapar. str.replace'den farkı: tam string aramak yerine pattern ile arar. 
    text = " ".join(text.split())                  # whitespace normalize
    bad = ["http", "www", ".com", "href", "//"]
    return " ".join(w for w in text.split() if not any(s in w for s in bad))


def _drop_reason(text_raw: str) -> str:
    """Belgeyi atmak için sebep döndürür; boş string → tut."""
    lines = [l.strip() for l in text_raw.split("\n") if l.strip()]
    if len(lines) >= 5:
        short = sum(1 for l in lines if len(_get_words(l)) <= 3)
        if (short / len(lines)) > 0.30:
            return "kisa_satir"

    text = _modify(text_raw)
    words = _get_words(text)

    # Kelime sayısı -> 100.000 üstünü atma konusundan emin değilim TODO!
    if not (15 <= len(words) <= 100_000):
        return "kelime_sayisi"

    # FastText dil tespiti
    if not _is_turkish(text):
        return "fasttext_dil"

    # Uzun kelime
    if not all(len(w) <= 40 for w in words):
        return "uzun_kelime"

    # Karakter tekrarı
    chars = list(text)
    n = 10
    if len(chars) >= n:
        ngrams = ["".join(chars[i:i+n]) for i in range(len(chars)-n+1)]
        counts = Counter(ngrams)
        repeated = sum(c for c in counts.values() if c > 1)
        if (repeated / len(ngrams)) > 0.20:
            return "karakter_tekrari"

    # Kelime tekrarı
    n = 5
    if len(words) >= n:
        wgrams = [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]
        counts = Counter(wgrams)
        repeated = sum(c for c in counts.values() if c > 1)
        if (repeated / len(wgrams)) > 0.15:
            return "kelime_tekrari"

    # Özel karakter oranı
    if not text or (sum(1 for c in text if c in SPECIAL_CHARS) / len(text)) > 0.35:
        return "ozel_karakter"

    # Stopword oranı
    sw_ratio = sum(1 for w in words if w.lower() in _STOPWORDS) / len(words)
    if sw_ratio < 0.05:
        return "dusuk_stopword"

    # Flagged word oranı -> TODO 2 : bazı kelimeleri görünce direkt atsak mı?
    fw_ratio = sum(1 for w in words if w.lower() in _FLAGGED) / len(words)
    if fw_ratio > 0.04:
        return "flagged_kelime"

    return ""


def _process(example: dict) -> dict:
    text_raw = example.get("text", "")
    if not isinstance(text_raw, str) or not text_raw.strip():
        return {"text": text_raw, "_keep": False, "_reason": "bos_metin"}
    reason = _drop_reason(text_raw)
    keep = reason == ""
    return {"text": _modify(text_raw) if keep else text_raw, "_keep": keep, "_reason": reason}


# ---------------------------------------------------------------------------
# Dataset konfigürasyonları
# ---------------------------------------------------------------------------
DATASETS = {
    "fineweb": {
        "repo_id": "HuggingFaceFW/fineweb-2",
        "file_filter": lambda f: "tur_Latn" in f and f.endswith(".parquet"),
        "needs_token": False,
    },
    "culturax": {
        "repo_id": "uonlp/CulturaX",
        "file_filter": lambda f: f.startswith("tr/") and f.endswith(".parquet"),
        "needs_token": True,
    },
    "hplt2": {
        "repo_id": "HPLT/HPLT2.0_cleaned",
        "file_filter": lambda f: "tr_Latn" in f and f.endswith(".parquet"),
        "needs_token": False,
    },
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset",   choices=["fineweb", "culturax", "hplt2"], required=True)
    parser.add_argument("--task_id",   type=int, required=True) # shell task_id atayıp çağırıyor, python scriptlerini
    parser.add_argument("--num_tasks", type=int, required=True)
    parser.add_argument("--output_dir",  type=str, required=True)
    parser.add_argument("--dropped_dir", type=str, default=None,
                        help="Atılan belgelerin kaydedileceği dizin (verilmezse kaydedilmez)")
    parser.add_argument("--hf_token",   type=str, default=None) # culturax icin lazım da ama onu kullanmayalım diyorum, bu satır gereksiz oldu simdi -> fineweb ve hplt icin
    parser.add_argument("--num_proc",   type=int, default=os.cpu_count())
    parser.add_argument("--ft_model",     type=str, default=None,
                        help="FastText dil tespit modeli yolu (ör: /path/to/lid.176.bin)")
    parser.add_argument("--ft_threshold", type=float, default=0.80,
                        help="FastText Türkçe skor eşiği (varsayılan: 0.80)")
    args = parser.parse_args()

    if args.hf_token:
        login(token=args.hf_token, add_to_git_credential=False)

    global _FT_MODEL_PATH, _FT_THRESHOLD
    if args.ft_model:
        _FT_MODEL_PATH = args.ft_model
        _FT_THRESHOLD  = args.ft_threshold
        print(f"FastText modeli: {_FT_MODEL_PATH}  eşik: {_FT_THRESHOLD}")
    else:
        print("FastText filtresi devre dışı (--ft_model verilmedi)")

    os.makedirs(args.output_dir, exist_ok=True)
    if args.dropped_dir:
        os.makedirs(args.dropped_dir, exist_ok=True)

    cfg = DATASETS[args.dataset]
    api = HfApi()

    print(f"[task {args.task_id}] Shard listesi alınıyor: {cfg['repo_id']}")
    all_files  = sorted(api.list_repo_files(cfg["repo_id"], repo_type="dataset")) # hugging face'den repo isimlerini çek + parçala
    data_files = [f for f in all_files if cfg["file_filter"](f)]
    my_files   = data_files[args.task_id::args.num_tasks] # task id'den başla , num_tasks kadar adım at 

    if not my_files:
        print(f"[task {args.task_id}] Bu task için shard yok.")
        return

    base_url        = f"https://huggingface.co/datasets/{cfg['repo_id']}/resolve/main/"
    total_kept      = 0
    total_before    = 0
    total_reasons   = Counter()
    t0              = time.time()

    def _log_reasons(reasons: Counter, n_before: int, prefix: str):
        kept = reasons.get("", 0)
        dropped = n_before - kept
        print(f"{prefix}  toplam: {n_before:,}  kalan: {kept:,}  atılan: {dropped:,} ({dropped/n_before*100:.1f}%)")
        for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
            if reason == "":
                continue
            print(f"{prefix}    {reason:<20} {count:>8,}  ({count/n_before*100:.1f}%)")

    for shard_idx, fname in enumerate(my_files):
        # Her shard için ayrı çıktı dosyası — restart'ta mevcut olanlar atlanır
        shard_tag     = f"task_{args.task_id:05d}_shard_{shard_idx:04d}"
        out_path      = os.path.join(args.output_dir, f"{shard_tag}.parquet")
        dropped_path  = os.path.join(args.dropped_dir, f"{shard_tag}.parquet") if args.dropped_dir else None

        if os.path.exists(out_path):
            print(f"[task {args.task_id}] Shard {shard_idx}/{len(my_files)-1} zaten mevcut, atlıyor.")
            continue

        url = base_url + fname
        print(f"[task {args.task_id}] Shard {shard_idx}/{len(my_files)-1} yükleniyor: {fname}")

        shard = load_dataset("parquet", data_files=[url], split="train", num_proc=args.num_proc) # num_proc -> bölünecek çekirdek sayısı
        n_before      = len(shard)
        total_before += n_before

        #burada verilen cpu sayısına belgeyi bölüyor
        shard   = shard.map(_process, num_proc=args.num_proc, desc=f"Shard {shard_idx}")

        shard_reasons = Counter(shard["_reason"])
        total_reasons += shard_reasons

        kept    = shard.filter(lambda x:     x["_keep"], num_proc=args.num_proc)
        dropped = shard.filter(lambda x: not x["_keep"], num_proc=args.num_proc)
        kept    = kept.remove_columns(["_keep", "_reason"])
        dropped = dropped.remove_columns(["_keep", "_reason"])

        kept.to_parquet(out_path)
        if dropped_path:
            dropped.to_parquet(dropped_path)

        total_kept += len(kept)
        elapsed     = time.time() - t0
        print(f"[task {args.task_id}] Shard {shard_idx}/{len(my_files)-1}  süre={elapsed:.0f}s  → {out_path}")
        _log_reasons(shard_reasons, n_before, prefix=f"[task {args.task_id}]")

    elapsed  = time.time() - t0
    print(f"\n[task {args.task_id}] === TAMAMLANDI  toplam süre={elapsed:.0f}s ===")
    _log_reasons(total_reasons, total_before, prefix=f"[task {args.task_id}] TOPLAM")


if __name__ == "__main__":
    main()
