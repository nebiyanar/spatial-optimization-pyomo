# Multiple Facility Location Problem (MFRLP) - Berlin

Bu proje, Berlin şehrinde belirli kriterlere (nüfus, trafik, sanayi) dayalı olarak **5 yeni akaryakıt istasyonu** için en uygun konumları belirlemek amacıyla geliştirilmiş bir matematiksel optimizasyon modelidir.

## 🚀 Proje Hakkında

Model, talep bölgelerinin ağırlıklarını normalize ederek toplam ağırlıklı L1 (Manhattan) uzaklığını minimize etmeyi hedefler. Ayrıca, yeni açılacak tesislerin birbirine çok yakın olmaması için **10 km minimum mesafe kısıtı** (Euclidean) eklenmiştir.

### Temel Özellikler:
- **Matematiksel Model:** Pyomo kütüphanesi kullanılarak kurulan Mixed-Integer / Non-Convex programlama.
- **Kısıtlar:** Tesis-tesis arası minimum 10 km mesafe kısıtı.
- **Ağırlıklandırma:** Nüfus (%25), Trafik (%40) ve Sanayi (%35) verilerinin ağırlıklı ortalaması.
- **Görselleştirme:** Matplotlib ile Berlin haritası üzerinde talep bölgeleri, mevcut istasyonlar ve önerilen noktaların gösterimi.

## 🛠️ Kullanılan Teknolojiler

* **Python 3.x**
* **Pyomo:** Optimizasyon modelleme dili.
* **Gurobi Solver:** Non-convex kısıtları çözmek için tercih edilen çözücü.
* **Pandas:** Veri işleme ve analizi.
* **Matplotlib:** Sonuçların harita üzerinde görselleştirilmesi.

## 📊 Veri Setleri

Proje iki ana veri kaynağı üzerinden beslenmektedir:
- `stations.csv`: Berlin'deki mevcut akaryakıt istasyonlarının (TotalEnergies vb.) koordinatlarını içerir.
- `proje1.xlsx`: Berlin "Bezirk" (ilçe) bazlı nüfus, trafik ve sanayi puanlarını barındırır.

## 📈 Sonuçlar

Model çalıştırıldığında, Berlin'in stratejik noktalarında birbirine 10 km'den uzak 5 optimal nokta üretir. Aşağıdaki görselde yeşil bölgeler talep yoğunluğunu, mavi noktalar mevcut istasyonları, **kırmızı yıldızlar** ise modelin önerdiği yeni lokasyonları temsil etmektedir.



## 💻 Kurulum ve Çalıştırma

1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install pyomo pandas matplotlib openpyxl
