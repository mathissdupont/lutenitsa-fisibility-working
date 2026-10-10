# Lütenitsa fabrikası: istatistiksel fizibilite ve yer seçimi

Rapor tarihi: 10 Ekim 2026. Çalışma FE401 akademik tasarım senaryosudur.

## Sonuç

Bursa–Mustafakemalpaşa OSB, Manisa–Salihli OSB ve Balıkesir–Gönen Deri İhtisas ve Karma OSB arasında doğrulanmış bir kârlılık sıralaması yapılamaz. Üç adayın gıda üretimine uygun parsel, tahsis edilebilir su/atıksu/enerji kapasitesi ve arazi/afet uygunluğu **DOĞRULANMADI** durumundadır. Kurumsal altyapı açıklaması parsel uygunluk onayı yerine geçmez.

Koşullu seçim kuralı: zorunlu uygunluk koşullarını sağlayan adaylar arasında, eşdeğer üretim ve talep koşullarında, gerçek sözleşmeler ve yatırım teklifleriyle hesaplanan risk düzeltilmiş 10 yıllık reel NPV en yüksek olan yer seçilmelidir. Mevcut kanıt hiçbir adayı kesin olarak desteklemiyor.

## Doğrulanan veri ve kapsam

Toplam 38 resmî tarım gözlemi alındı. TEPGE Domates 2024 Ek Tablo 11 (PDF sayfa 34, basılı sayfa 26), Bursa, Manisa ve Balıkesir için 2019–2023 salçalık domates alanı ve üretimini içeriyor. Bin dekar ve bin ton değerleri hektar/tona dönüştürüldü; kaynağın yuvarlaması korundu. 2025 yatırım rehberlerindeki 2024 salçalık domates ve salçalık biber üretimleri, Bursa/Balıkesir patlıcan üretimleri özgün PDF’den doğrulandı. Manisa’da seçilmiş tabloda patlıcan yoktur; yokluğu sıfır kabul edilmedi.

Salçalık biber sınıfı kapya ile eşlenmedi. Tüm bu sayılar **il toplamıdır**; ilçelere paylaştırılmadı ve satın alınabilir arz sayılmadı. Kaynak/vintaj değişikliği 2023–2024 büyüme yorumunda dikkate alınmalıdır. Resmî ürün kodları, ilçe kodları ve kesin yayımlanma tarihleri eksiktir.

KGM’nin kendi sayfasında yayımladığı ilçe mesafe dosyasından 33 gelen ve 12 giden güzergâh çıkarıldı. İstanbul için Fatih, Ankara için Çankaya, İzmir için Konak, Bandırma ihracatı için Bandırma ilçe merkezi vekili kullanıldı. Bunlar karayolu **ilçe merkezi vekilleridir**. OSB kapısı, müşterinin deposu, liman terminali, ağır vasıta kısıtı ve son kilometre mesafesi ayrıca doğrulanmalıdır. Aynı ilçe için 0 km OSB iç transferi değildir. Bölgesel dağıtıcı ve İzmir liman terminali adresleri henüz eksiktir.

## İstatistiksel sonuçlar

Hedeflenen 11 ilçe × 11 yıl × 6 ürün × 4 ölçüm = 2904 kayıt eksiktir. 2015–2025 ilçe üretim, alan, verim ve çiftlik çıkış fiyat serileri alınamadı. İlgili regresyon/tahminler **NOT_ESTIMABLE** olarak kaydedildi. Katsayı, p-değeri, R² ve 2026–2030 miktarları uydurulmadı.

Kod; önceki yıl, üç yıllık ortalama, trend, OLS, Ridge, panel sabit etkiler ve örneklem uygunsa Random Forest seçeneklerini içeriyor. 2023–2025 değerlendirmesi ve genişleyen pencere kullanılıyor. Lag verisinin 1 Ocak tahmin tarihinde erişilebilir olması gerekiyor. Gerçekleşmiş aynı yıl verimi, hedef üretim ve gelecek iklim verileri özellik olarak kullanılmıyor. Ölçekleme yalnız eğitimde yapılıyor. OLS en az 30 eğitim satırı, beş yıl ve üç ilçe; panel çıkarımı en az sekiz ilçe kümesi; RF en az 200 satır ve on ilçe gerektiriyor. Bunlar proje güvenlik eşikleri olup yeterliliği tek başına kanıtlamaz. Model naif yöntemi geçmezse açıkça işaretlenir.

Çok yıllı belirsizlik aralıkları için tahmin ufkuna özgü kalibrasyon eksiktir. İyimser/kötümser arz senaryoları ve satın alınabilir üretim payları da veri/varsayım bekliyor. Bu nedenle boş değerler başarı sonucu gibi gösterilmedi.

## Reçete, lojistik ve ekonomi

Özgün reçete 1 kg ürün başına 2,513 kg brüt girdi varsayar. 10 ton/gün ve 250 gün için 2.500.000 kg ürün, 6.282,5 ton brüt girdi ve 5.000.000 adet 500 g kavanoz planlanır. Brüt girdi ile nihai ürün farkı 3.782,5 tondur. Bu farkın ne kadarının ayıklama, közleme veya buharlaşma olduğu bilinmiyor; tamamı buharlaşma diye etiketlenmedi. Pilot proses verimi, mevsimsel alım, raf ömrü ve depolama kapasitesi gerekli.

Mevsimsel LP/MILP; brüt satın alma, taşıma kaybı sonrası teslim, aylık stok dengesi, ortak depo kapasitesi, tedarikçi katılımı, kalite uygunluğu ve isteğe bağlı tam kamyon sayısını içeriyor. Tarımsal üretim tedarikçi teklifi yerine kullanılmıyor. Rafine yağ, baharat, tuz ve sirke ayrı tedarik ürünleridir. Ambalaj finans modelinde ayrı tutuluyor.

Finans hesapları üretim, talep ve satışı ayrı izler. Üretilip satılmayan ürünün üretim maliyeti korunur. Gelen navlun tüm teslim maliyetinde bir kez sayılır. Sabit reel fiyatlar ve reel iskonto birlikte kullanılır. Gerçek TÜFE endeks seviyeleri eksik olduğu için tarihsel reel fiyat dönüşümü yapılmadı; 2026 tam yıl TÜFE ortalaması rapor tarihinde henüz tamamlanmamıştır. Tarım-ÜFE yerel tedarikçi fiyatı sayılmadı.

Kod EBITDA, EBIT, amortisman, zarar devri, vergi, yenileme yatırımı, terminal defter değeri/satış vergisi, işletme sermayesi geri dönüşü, serbest nakit, NPV, uygun işaretlerde IRR, geri ödeme ve başabaş fiyat/hacim hesabını içerir. Vergi kaybına anlık nakit iadesi varsayılmaz. Başabaş hacim üretimin satışa uyduğu EBITDA eşiğidir; yatırım getirisini ölçmez. 5/10/25/50 ton kapasite tabloları var; kapasiteye özgü teklifler olmadan NPV ölçeklenmedi.

Gerçek finans girdileri eksik olduğundan gerçek NPV veya Monte Carlo sonucu yoktur. `output/demo/` altındaki açıkça varsayımsal örnekler eski maliyetleri kullanır. Bunlar ana Excel'e, resmî tarihsel veriye veya yer önerisine aktarılmaz. Üçgensel şoklar ampirik kalibre edilmemiş, bağımsız uzman varsayımlarıdır. Hasat nedeniyle sözleşmeli arz yetmediğinde çekiliş fizibil değil olarak sayılır; NPV istatistikleri fizibil çekilişlere koşulludur. Bu koşullu puan yatırım sıralaması olarak kullanılmaz.

## Kanıt boşlukları ve veri edinme

1. TÜİK/MEDAS: 2015–2025, belirtilen 11 ilçe, salçalık domates, kapya sınıfı, patlıcan, kuru sarımsak, yağlık ayçiçeği ve ayrıştırılmış baharatlar. Resmî ürün/ilçe kodları ve veri yayımlanma tarihleriyle CSV/Excel dışa aktarım.
2. MGM/MEVBİS: istasyon eşlemesi, yetişme dönemi yağış/sıcaklık ve erişilebilirlik tarihleri; üyelik/izinli sipariş. Gelecek gerçekleşmiş iklim gözlemleri tahmin girdisi olamaz.
3. Tedarikçiler: gerçek fiyat teklifi, kalite, aylık miktar, katılım sınırı, sezon, kayıp ve rafine yağ/ambalaj teslim noktaları.
4. Nakliyeciler: OSB/depo/liman adresleri, son kilometre, araç kapasitesi, boş dönüş, yükleme, navlun ve ağır vasıta uygunluğu.
5. OSB yönetimleri: gıda faaliyeti/parsel onayı, su kalitesi ve tahsis, deşarj kapasitesi, elektrik/ısı tahsis ve tarifeleri, arazi fiyatı ve zemin/sel/yangın etütleri.
6. Müşteriler: İstanbul, Ankara, İzmir, bölgesel dağıtım ve ihracat için fiyat, ürün/ambalaj, yıllık talep ve pazar payları.
7. Yatırım/işletme teklifleri: 5/10/25/50 ton ekipman, arazi, bina, yardımcı tesis, bakım ve su/enerji tüketim normları.
8. FE401 PDF: 12 faktör kullanıcı talebinden alınmıştır; özgün PDF sayfa ve yöntem kontrolü yapılamadı. Puanlar eksik, ağırlıklar varsayım, kârlılık ayrı hesap.

## Kaynak bağlantıları

- [TEPGE Domates 2024](https://arastirma.tarimorman.gov.tr/tepge/Belgeler/PDF%20%C3%9Cr%C3%BCn%20Raporlar%C4%B1/2024%20%C3%9Cr%C3%BCn%20Raporlar%C4%B1/Domates%20%C3%9Cr%C3%BCn%20Raporu%202024-396%20TEPGE.pdf)
- [KGM Mesafeler](https://www.kgm.gov.tr/Sayfalar/KGM/SiteTr/Root/Uzakliklar.aspx)
- [Mustafakemalpaşa OSB](https://www.mkposb.org.tr/tarihce), [Salihli OSB](https://salihliosb.org.tr/hizmetler/), [Gönen OSB](https://www.gonenosb.org.tr/)

Tam kayıt, erişim tarihi ve özgün dosyalar `sources.csv`, `reports/collection_log.json` ve `data/raw/` altında tutulur. Orijinal çalışma dosyaları değiştirilmemiştir.
