# Yer seçimi için eksik kanıtlar

Mevcut resmî kanıtlar üç il için kısmi tarım gözlemleri ve ilçe merkezi karayolu
mesafeleriyle sınırlıdır. İlçe üretimi veya bağlayıcı tedarik sözleşmesi bulunmuyor.
Kesin tesis yeri önerisi yoktur.

| Eksik | İstenen kapsam / kaynak | Etkisi |
|---|---|---|
| İlçe tarım geçmişi | TÜİK MEDAS; 2015–2025; 11 ilçe; sınıfları ayrı ürünler; miktar, alan, verim, yerel fiyat | Regresyon ve 2026–2030 arz tahmini hesaplanamaz |
| Resmî kod ve yayımlanma tarihi | TÜİK özgün ihracı / metaveri | İdari eşleme ve tahmin anında erişilebilirlik doğrulanamaz |
| Reel fiyat deflatörü | Aynı vintaj TÜİK TÜFE aylık endeks seviyeleri; tam yıl ortalamaları | Tarihsel sabit fiyat serisi hesaplanamaz |
| İklim | MGM MEVBİS yetkili sipariş; istasyon, yetişme dönemi, erişim tarihi | İklim açıklayıcıları modele alınamaz |
| Tedarikçi teklifleri | Kapya, salçalık domates, patlıcan, sarımsak, rafine yağ, baharat, tuz, sirke; aylık miktar, fiyat, kalite | Gerçek tedarik tahsisi hesaplanamaz |
| Kavanoz ve ambalaj | Üretici teklifi; ürün, kapak, etiket, koli, teslimat ve kapasite | Ambalaj maliyeti varsayım olarak kalır |
| Proses verimi ve stok | Pilot reçete, temizleme/közleme, buharlaşma, hasat dönemi, raf ömrü, depo | Kütle dengesi aşamaları ve depolama tasarımı doğrulanamaz |
| Tam rota ve nakliye | OSB/depo/müşteri/liman adresi, kamyon uygunluğu, yük kapasitesi, boş dönüş, navlun | KGM merkez vekili gerçek sevk rotası sayılmaz |
| Müşteri talebi | İstanbul, Ankara, İzmir, bölgesel ve ihracat sözleşmeleri, fiyat ve talep dağılımı | Üretimin tamamının satılacağı söylenemez |
| OSB ve parsel onayları | Gıda kullanım izni, su kalitesi/kapasitesi, atıksu, enerji, zemin/sel/yangın | Üç aday da UNVERIFIED kalır |
| Kapasiteye özel yatırım | 5/10/25/50 ton/gün arazi, bina, proses ve yardımcı tesis teklifleri | Gerçek NPV/IRR ve kapasite sıralaması yok |
| FE401 PDF ve puan kanıtı | Özgün PDF, uzman gerekçeleri ve nesnel puan dayanakları | 12 kriter kullanıcı metnine dayanır; ağırlıklar varsayım |

Kaynak adresleri `sources.csv` ve `reports/manual_import.md` içinde listelenmiştir.
Manuel şablonlar `data/manual/` altındadır. Eksikler sıfırla veya sentetik tarihle
doldurulmamıştır. Varsayımsal örnekler ana araştırma sonuçlarına aktarılmamıştır.
