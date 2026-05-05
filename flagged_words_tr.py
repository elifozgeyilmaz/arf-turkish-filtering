"""
Flagged Words nedir?

  Belgede bu kelimelerin oranı belirlenen eşiğin üzerindeyse belge atılır.
  Stopword filtresinin tersidir: bu kelimeler çok geçiyorsa belge uygunsuz
  içerik (pornografi, ağır argo, spam) barındırıyor demektir.

  Parametredeki karşılığı:
    "flagged_words_max_cutoff": 0.05  # kelimelerin en fazla %5'i flagged olabilir
"""

flagged_words_tr = [
    # --- Cinsel içerikli argo ---
    "am", "amcık", "amına", "amını", "amınakoyayım",
    "amcığa", "amcığı", "amcığın", "amcıklar", "amcıklara",
    "amcıklarda", "amcıklardan", "amcıkları", "amcıkların", "amcıkta", "amcıktan",
    "amı", "amlar",
    "göt", "götü", "götüne", "götlek",
    "göte", "götler", "götlerde", "götlerden", "götlere", "götleri", "götlerin",
    "götte", "götten", "götün",
    "götveren", "göt veren",
    "götverende", "götverenden", "götverene", "götvereni", "götverenin",
    "götverenler", "götverenlerde", "götverenlerden", "götverenlere",
    "götverenleri", "götverenlerin",
    "orospu", "orospuçocuğu", "fahişe",
    "orospuda", "orospudan", "orospular", "orospulara", "orospularda",
    "orospulardan", "orospuları", "orospuların", "orospunun", "orospuya", "orospuyu",
    "seks", "sikiş", "sikişmek", "sikmek", "siktir",
    "siktim", "sikeyim", "sikici",
    "sik", "sike", "siker sikmez", "siki", "sikilir sikilmez", "sikin",
    "sikler", "siklerde", "siklerden", "siklere", "sikleri", "siklerin",
    "sikmemek", "sikte", "sikten", "siktir", "siktirir siktirmez",
    "yarrak", "yarak", "yarrağı", "yarrağına",
    "yarağa", "yarağı", "yarağın",
    "yaraklar", "yaraklara", "yaraklarda", "yaraklardan",
    "yarakları", "yarakların", "yarakta", "yaraktan",
    "taşak", "dalyarak",
    "taşağa", "taşağı", "taşağın",
    "taşaklar", "taşaklara", "taşaklarda", "taşaklardan",
    "taşakları", "taşakların", "taşakta", "taşaktan",
    "porno", "pornografi", "pornosu",
    "pik", "piç", "piçlik",
    "döl", "meni",
    "vajina", "penis",
    "escort", "masaj salonu","eskort",
    "erotik", "erotizm",
    "hentai", "japon porno",
    "anal", "oral seks",
    "sakso", "saksocu", "saksocuda", "saksocudan",
    "saksocular", "saksocuya", "saksocuyu",
    "ibne", "ibnelik",
    "otuz birci", "otuz bircide", "otuz birciden",
    "otuz birciler", "otuz bircilerde", "otuz bircilerden",
    "otuz bircilere", "otuz bircileri", "otuz bircilerin",
    "otuz bircinin", "otuz birciye", "otuz birciyi",
    "sıçmak",

    # --- Hakaret / nefret söylemi ---
    "aptal", "salak", "gerizekalı", "geri zekalı",
    "dangalak", "ahmak", "eşek",
    "mal", "malık",
    "bok", "boktan", "boku",
    "it", "köpek", "köpeğin",
    "hıyar",
    "embesil", "budala",
    "oç", "oçluk",
    "şerefsiz", "şerefsizlik",
    "namussuz", "namussuzluk",
    "alçak", "alçaklık",
    "kahpe", "kahpelik",
    "kaltak", "kaltaklık",
    "kaltağa", "kaltağı", "kaltağın",
    "kaltaklar", "kaltaklara", "kaltaklarda", "kaltaklardan",
    "kaltakları", "kaltakların", "kaltakta", "kaltaktan",
    "sürtük",
    "pezevenk", "pezevenklik",

    # --- Irkçı / ayrımcı ifadeler ---
    "zenci", "zenciler",
    "çingene", "çingeneler",
    "çingenede", "çingeneden",
    "çingenelerde", "çingenelerden", "çingenelere", "çingeneleri", "çingenelerin",
    "çingenenin", "çingeneye", "çingeneyi",
    "gavur", "gavurlar",
    "kâfir", "kafir",

    # --- Şiddet içerikli argo ---
    

    # --- Kumar / yasadışı içerik ---
    "kumar", "casinoda", "bahis sitesi",
    "illegal", "kaçakçı", "uyuşturucu satış",
    "eroin", "kokain", "uyuşturucu", "esrar", "bonzai",
    "lsd", "bet", "bahis","slot oyunu","mariuana"
]

flagged_words_tr = list(set(flagged_words_tr))
