"""
Stopword nedir?                                                                
                                                                               
  Bir dilde çok sık geçen ama kendi başına anlam taşımayan kelimeler — "ve",     
  "bir", "bu", "ile", "için" gibi.                                               
                                                                                 
  Bu pipeline'da ne için kullanıyoruz?                                           
                                                                                 
  Burada kalite filtresi olarak kullanıyoruz. Mantığı şu:                        
                                                            
  ▎ Eğer bir belge Türkçeyse, içinde kaçınılmaz olarak Türkçe stopword'ler       
  ▎ geçmesi lazım.                                          
                                                                                 
  "Merhaba bu bir test cümlesidir ve çok güzel."            
             ^^^     ^^^          ^^^                                            
          stopword stopword    stopword  → oran yüksek → KALITELI                
                                                                                 
  "asdfgh zxcvbn qwerty 12345 @@@ http://spam.com"                               
      → hiç stopword yok → oran 0 → ATILIR                                       
                                                                                 
  Yani stopword oranı düşük olan belgeler şunlar oluyor:                         
  - Spam / reklam metinleri                                                      
  - Sadece URL listesi olan sayfalar                                             
  - Kod/sembol çorbası                                      
  - Yabancı dilde yazılmış metinler (Türkçe stopword geçmez)                     
                                                                                 
  Parametredeki karşılığı                                                        
                                                                                 
  parameters.py'de şöyle bir şey olacak:                                         
  "stopwords_min_cutoff": 0.10  # belgenin en az %10'u stopword olmalı           
                                                                                 
  Altında kalan belgeler atılır.                                                 
   
"""



stopwords_tr = [
    # --- Kişi zamirleri ---
    "ben", "sen", "o", "biz", "siz", "onlar",
    "benim", "senin", "onun", "bizim", "sizin", "onların",
    "beni", "seni", "onu", "bizi", "sizi", "onları",
    "bana", "sana", "ona", "bize", "size", "onlara",
    "bende", "sende", "onda", "bizde", "sizde", "onlarda",
    "benden", "senden", "ondan", "bizden", "sizden", "onlardan",
    "benimle", "seninle", "onunla", "bizimle", "sizinle", "onlarla",

    # --- İşaret zamirleri ---
    "bu", "şu",
    "bunu", "şunu",
    "bunlar", "şunlar",
    "bunları", "şunları",
    "buna", "şuna",
    "bunlara", "şunlara",
    "bunda", "şunda",
    "bunlarda", "şunlarda",
    "bundan", "şundan",
    "bunlardan", "şunlardan",
    "bunun", "şunun",
    "bunların", "şunların",
    "bunla", "şunla",
    "bunlarla", "şunlarla",

    # --- Soru kelimeleri ---
    "ne", "kim", "kimi", "kime", "kimde", "kimden", "kimin", "kimle",
    "nerede", "nereye", "nereden", "nerede", "neresi", "neresiyle",
    "nasıl", "neden", "niçin", "niye",
    "kaç", "kaçı", "kaçına", "kaçıncı",
    "hangi", "hangisi", "hangisini", "hangisine",
    "ne zaman", "nereye", "kim",
    "mı", "mi", "mu", "mü",
    "acaba", "yoksa",

    # --- Bağlaçlar ---
    "ve", "ile", "veya", "ya", "ya da",
    "ama", "fakat", "lakin", "ancak", "yalnız",
    "oysa", "oysaki", "halbuki", "hâlbuki",
    "çünkü", "zira", "madem", "mademki",
    "ki", "de", "da",
    "hem", "hem de",
    "ne", "ne de",
    "gerek", "ister",
    "sanki", "güya",
    "üstelik", "ayrıca", "bunun yanı sıra",
    "yani", "demek ki", "dolayısıyla",
    "eğer", "şayet", "şart ki",
    "ta ki", "diye",

    # --- Edatlar / ilgeçler ---
    "için", "gibi", "kadar", "göre", "karşı",
    "doğru", "rağmen", "beri", "önce", "sonra",
    "üzere", "aracılığıyla", "sayesinde",
    "nedeniyle", "yüzünden", "dolayı",
    "itibaren", "başlayarak",
    "hakkında", "ilişkin", "dair",
    "üzerinde", "üzerinden", "altında", "altından",
    "yanında", "yanından", "yanına",
    "arasında", "arasından", "arasına",
    "içinde", "içinden", "içine",
    "dışında", "dışından", "dışına",
    "karşısında", "karşısından", "karşısına",
    "boyunca", "süresince", "esnasında",
    "sırasında", "sırasınca",
    "tarafından", "tarafınca",
    "ile birlikte", "birlikte",

    # --- Belirteçler / zarflar ---
    "çok", "daha", "en", "az", "biraz",
    "oldukça", "epey", "fazla", "pek",
    "gayet", "son", "derece",
    "hiç", "hiçbir", "hiçbirini", "hiçbirine",
    "zaten", "artık", "hâlâ", "halâ", "hala",
    "henüz", "hemen", "şimdi", "şimdiden",
    "bugün", "dün", "yarın", "önceki", "sonraki",
    "burada", "şurada", "orada",
    "buraya", "şuraya", "oraya",
    "buradan", "şuradan", "oradan",
    "böyle", "şöyle", "öyle",
    "böylece", "şöylece", "öylece",
    "belki", "sanki", "elbette",
    "tabii", "tabiki", "tabii ki",
    "kesinlikle", "mutlaka", "illa",
    "bile", "dahi",
    "sadece", "yalnızca", "salt",
    "tam", "tamamen", "bütünüyle",
    "özellikle", "genellikle", "çoğunlukla",
    "bazen", "zaman zaman", "kimi zaman",
    "nadiren", "sık sık", "her zaman",
    "hep", "daima", "herzaman",
    "birden", "aniden", "birdenbire",
    "önce", "sonra", "ardından", "akabinde",
    "hemen", "derhal", "vakit",

    # --- Belirleyiciler / sıfatlar ---
    "bir", "bu", "şu",
    "her", "bütün", "tüm",
    "bazı", "birkaç", "birçok",
    "herhangi", "herhangi bir",
    "kendi", "kendisi", "kendileri", "kendim", "kendin",
    "bütün", "hepsi", "hepimiz", "hepiniz",
    "diğer", "öteki", "öbür",
    "aynı", "benzer",
    "tek", "yalnız",
    "birinci", "ikinci", "üçüncü",

    # --- Sayılar (yaygın) ---
    "iki", "üç", "dört", "beş",
    "altı", "yedi", "sekiz", "dokuz", "on",
    "yüz", "bin",

    # --- Yardımcı fiil kalıpları / ekler ---
    "var", "yok", "değil",
    "ise", "imiş", "idi", "olan",
    "oldu", "olacak", "olmuş",
    "olmak", "olmaya", "olması",
    "olduğu", "olduğunu", "olduğunu",
    "olarak", "olup", "olsa",
    "olsun", "olsunlar",
    "oluyor", "oluşu", "oluşuna",
    "olabilir", "olamaz",
    "edildi", "edilecek", "edilmiş",
    "edilmesi", "edilmek", "edilerek",
    "yapıldı", "yapılacak", "yapılmış",

    # --- Yaygın kısaltmalar / bağlantı kelimeleri ---
    "vb", "vb.", "vs", "vs.", "vbg",
    "örn", "örn.", "örneğin",
    "yani", "kısacası", "özetle",
    "aslında", "esasen", "gerçekte",
    "öncelikle", "ilk olarak", "son olarak",
    "birincisi", "ikincisi", "üçüncüsü",
    "bir yandan", "öte yandan",
    "buna göre", "buna karşın", "buna rağmen",
    "bunun için", "bunun yanı sıra",
    "bununla birlikte", "bununla beraber",
    "her ne kadar", "her ne olursa",
    "söz konusu",
]

stopwords_tr = list(set(stopwords_tr))
