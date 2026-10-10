# Aşama sonuçları

Rapor tarihi: 10 Ekim 2026. Tekrarlanabilir altyapı ve sunum dosyaları üretildi.
Gerçek yer seçimi araştırması aşağıdaki kanıt boşlukları nedeniyle tamamlanmış sayılmaz.

## Aşama 1 — İnceleme ve kaynak araştırması

Tamamlananlar: `reports/legacy_inventory.json`, `reports/legacy_workbooks.json`,
`data/raw/legacy/`, `sources.csv`, `data_dictionary.csv`, `config/` ve manuel şablonlar.
Özgün iki Excel dosyası aynı içerik karmasına sahip. Özgün reçete, finans girdileri
ve üç sebzeli LP açıkça varsayımsal. Bunlar resmî gözlem kabul edilmedi.

Çalıştırılan komutlar: `python scripts/inspect_legacy.py`,
`python scripts/bootstrap_project.py`, kayıtlı kamusal dosyalar için collection çağrısı.
Kopyaların SHA-256 eşleşmesi doğrulandı. Dört Bakanlık PDF’i, üç OSB sayfası,
KGM kaynak sayfası ve iki resmî mesafe Excel’i korundu.

Eksikler: FE401 PDF, ilçe/ürün resmî kodları ve ilçe geçmişi. MGM üyelik/izinli sipariş,
EPİAŞ yetkili erişim ve TÜİK portalından manuel dışa aktarım süreçleri kaydedildi.
Giriş veya koruma aşılmadı, bilinmeyen API adresi üretilmedi.

## Aşama 2 — Normalizasyon ve kalite

Tamamlananlar: `src/collection.py`, `src/data.py`, `src/common.py`,
`data/processed/historical_observations.csv`, `missing_data.csv`,
`calculated_yields.csv`, `product_trends.csv`, `distance_matrix.csv`,
`reports/data_quality.json`, `data_quality.md`, `distance_quality.json`.

Çalıştırılan komut: `python -m src.pipeline validate`; tam çalıştırmada yeniden doğrulandı.
Sonuç: 38 doğrulanmış il düzeyi gözlem, 45 ilçe merkezi karayolu vekili, sıfır yinelenen
gözlem. Bir olası aykırılık işaretlendi ve korunarak raporlandı. İlçe düzeyindeki
2.904 hedef ölçüm eksik. Eksikler sıfır yapılmadı, genel salçalık biber kapya ile eşlenmedi.

Engeller: resmî yıllık deflatör, yayımlanma tarihleri, kodlar ve ilçe serisi.
2026 tam yıl TÜFE düzeyi rapor tarihinde henüz gözlenemez. Üretim/alan/yıl/birim
karıştırılmadı. Normalizasyon ve eksik/veri kalitesi testleri nihai pakette geçti.

## Aşama 3 — İstatistik ve tahmin altyapısı

Tamamlananlar: `src/statistics.py`, `model_validation.csv`, `forecasts.csv`,
`backtest_predictions.csv`, `regression_coefficients.csv`, istatistik durum raporları.
Çalıştırılan komut: `python -m src.pipeline regress`.

Yedi model seçeneği için 112 değerlendirme satırı, 2026–2030 için 880 ilçe/ürün/hedef
satırı üretildi. Bunlar **NOT_ESTIMABLE** durum kayıtlarıdır; sayısal sonuç değildir.
Geçerli gözlem olmadığı için katsayı, p-değeri, MAE, R², gerçek/tahmin ve artık grafiği yoktur.

Testler zamanında erişilemeyen lag gözlemlerinin dışlanmasını doğruladı. Ölçekleme
eğitim içinde, kronolojik değerlendirme geleceğe doğru. Yetersiz örneklemde modeller
durdurulur. Çok yıllı aralık kalibrasyonu, hava özellikleri ve arz senaryoları eksik
veri gerektiren geliştirme alanları olarak açıkça bırakıldı.

## Aşama 4 — Kütle, lojistik ve finans

Tamamlananlar: `src/materials.py`, `optimization.py`, `finance.py`, `decision.py`,
`scenarios.py`, kütle dengesi, tedarik/finans durum ve kapasite çıktıları.
Çalıştırılan komutlar: `python -m src.pipeline optimize`, `finance`, `demo`.

Mevsimsel LP/MILP; taşıma kaybı, ortak depo, kalite, katılım payı ve tam kamyon
kısıtları için test edildi. İlk test turu 19 başarı/1 hata verdi; kayıplı sevkiyatta
tedarikçi payı sınırı teslim edilen kullanılabilir miktara düzeltilip tekrar doğrulandı.
Sonraki çekirdek turunda 20 test geçti. Nihai kapsam daha sonra 30 teste genişletildi.

Vergi zararı için anlık iade yok; zarar devri, yenileme amortismanı, terminal defter
değeri ve işletme sermayesi geri dönüşü hesaplanır. Gelen navlun tek kez sayılır.
Üretim, talep ve satış ayrı. Gerçek finans girdileri eksik olduğundan gerçek NPV,
IRR ve yer sıralaması hesaplanmadı. Üç adayın zorunlu parsel koşulları UNVERIFIED.

Eski üç sebzeli LP maliyetleri ayrı varsayımsal örnekte birebir yeniden üretildi.
`output/demo/` altında finans, duyarlılık ve sabit tohumlu Monte Carlo örnekleri var.
Ana veriye veya yer önerisine aktarılmadı. Hasat açığı çekilişleri fizibil değil
olarak raporlanır; NPV dağılımı fizibil çekilişlere koşulludur.

Engeller: gerçek teklifler, mevsimsel arz, proses kayıpları, depo/raf ömrü, pazar
talebi, OSB/parsel onayları ve kapasiteye özel yatırım bütçeleri. Raf ömrü, karışık
araç yükü, tam çıkış pazarı ağı ve kalibre edilmiş stokastik tedarik uygulamaları
henüz geliştirilmedi; bunların sonuçları varmış gibi sunulmadı.

## Aşama 5 — Excel ve son doğrulama

Tamamlananlar: `src/reporting.py`, 24 sayfalı Türkçe Excel, Türkçe nihai rapor,
README, manuel içe aktarım kılavuzu, kanıt boşlukları ve test dosyaları.
Son Excel: 932 bağlı formül, 18 filtrelenebilir tablo, bir doğrulanmış üretim
eğilimi grafiği, görünür varsayımlar, kaynak bağlantıları ve dondurulmuş başlıklar.

Çalıştırılan komutlar:

```text
python -m src.pipeline all
python -m src.pipeline demo
python -m scripts.check_workbook
node scripts/recalculate_artifact.mjs
python -m scripts.verify_formula_caches
python -m pytest -q
node scripts/preview_workbook.mjs
```

Nihai sonuç: **30 test geçti**. 932 formülün önbelleği bağımsız yeniden hesaplamayla
eşleşti; formül hatası bulunmadı. Baz, düşük talep ve kısa amortisman/ufuk senaryolarında
Excel NPV, EBITDA, başabaş fiyatı, nakit akışı, vergi ve amortismanı Python ile eşleşti.
Dashboard, reçete ve finans görünümleri render edilip incelendi; kesilen aday etiketi
ve reçete oranlarının görünüm hassasiyeti düzeltildi. Özgün dosya karmaları korundu.

Yerel Excel COM `Workbooks.Open` çağrısı bu yürütme ortamında başarısız oldu.
Bağımsız spreadsheet motoru kullanıldı; ana XlsxWriter dosyası yeniden dışa aktarılarak
özellik kaybına uğratılmadı. Bu sınırlama `formula_verification.json` içinde kayıtlıdır.

**Nihai karar:** Kanıt eksikleri kapanmadan üç yer arasında kesin tercih yapılamaz.
Koşullu seçim kuralı uygun adaylar arasında risk düzeltilmiş reel NPV’yi maksimize etmektir.
