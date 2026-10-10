# Lütenitsa tesis yeri – ilçe bazlı lojistik / kaynak optimizasyonu

Bu paket FE401 gıda fabrikası yer seçimi için SENARYO modelidir.
Resmî ilçe bazlı, aynı yıl için eksiksiz üretim veri serisi ve gerçek satın alma teklifleri henüz yoktur.
**Sıralama yatırım kararı değildir.**

## Kullanım
1. `pip install scipy`
2. `python optimize_logistics.py --folder .`
3. Çıktı: `optimum_akis.csv` ve `sonuclar.csv`.
4. `tedarik_senaryosu.csv` dosyasındaki varsayımsal fiyat/kapasiteyi, `rota_mesafeleri.csv` dosyasındaki ilçeler arası yaklaşık mesafeleri gerçek tedarikçi/OSB adresleriyle güncelleyin.
5. Yeni Python sonucu Excel'in `LOJ_AKIS` sayfasına aktarılmadıkça Excel'deki tahsisler **eski senaryoda kalır**.

## Model
Her fabrika yeri ayrı çözülür:
min toplam(ton * [satın alma TL/ton + km * navlun TL/(ton·km) + yükleme TL/ton])
koşul: her ham madde için toplam sevk tonajı = talep tonajı,
        her ilçe/hammadde eşleşmesinde sevk <= senaryo kapasitesi.

Bu aşamada sadece biber, domates ve patlıcan tahsis edilir.
Sarımsak, rafine ayçiçek yağı ve baharatlar reçete/finans modelinde tutulur;
somut tedarikçi ve teslim noktaları belli olunca aynı modele eklenebilir.

## Yöntem sınırlamaları
- İlçe üretimi ≠ sözleşmeyle satın alınabilir ürün.
- Biber, domates, patlıcan fiyatları ve ilçe kapasitesi TEMSİLİDİR.
- 4 TL/(ton·km) ve 250 TL/ton yükleme SENARYODUR; gerçek navlun teklifi değildir.
- Salihli iç transferi 12 km TEMSİLİDİR.
- Kamyon yol yasağı, sezon, hasat, kalite, parsel girişi, boş dönüş maliyeti, depolama, kayıplar ayrı araştırılmalı.
- Regresyon 10+ yıllık ilçe/ürün/yıl veri serileri olmadan çalıştırılmadı.

## Kaynaklar (araştırma)
Karacabey Ticaret Borsası: https://www.karacabeytb.org.tr/inc/KTB_stratejik_plan4.pdf
Manisa İl Tarım: https://manisa.tarimorman.gov.tr/Haber/814/Manisada-Domates-Dikimi-Basladi
Balıkesir Valiliği: https://balikesir.gov.tr/sofradaki-balikesir
KGM mesafe cetveli: https://www.kgm.gov.tr/Sayfalar/KGM/SiteTr/Root/Uzakliklar.aspx
Her rota URL'si rota_mesafeleri.csv içinde bulunur.
