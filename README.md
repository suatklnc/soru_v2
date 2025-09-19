# 📚 PDF Soru Çıkarma ve Telegram Bot Sistemi

Bu proje, PDF dosyalarından matematik sorularını otomatik olarak çıkarır, cevap anahtarlarını işler ve Telegram bot üzerinden rastgele sorular gönderir. Mistral AI OCR desteği ile görsel tabanlı PDF'lerden de metin çıkarabilir.

## 🚀 Özellikler

### PDF İşleme
- ✅ **Otomatik PDF Bulma**: Dizindeki tüm PDF dosyalarını otomatik bulur
- ✅ **Çoklu PDF Desteği**: Birden fazla PDF dosyasını toplu olarak işler
- ✅ **Hassas Talimat Kutusu Silme**: 1. sorunun hemen üstünden keser
- ✅ **Akıllı Soru Tespit**: Soru numarası ile içerik doğru eşleştirilir
- ✅ **Şıklar Dahil Çıkarma**: Her soru tam olarak çıkarılır
- ✅ **Organize Çıktı**: Her PDF için ayrı klasör oluşturur

### OCR Desteği
- 🔍 **Mistral AI OCR**: Görsel tabanlı PDF'lerden metin çıkarır
- 🌍 **Çoklu Dil**: Türkçe ve İngilizce dil desteği
- 🎯 **Yüksek Kalite**: 3x büyütme ile daha iyi sonuçlar
- ⚡ **Akıllı Algılama**: Metin çıkarılamadığında otomatik OCR devreye girer

### Cevap Anahtarı Sistemi
- 📋 **Otomatik Cevap Anahtarı İşleme**: PDF adında "cevap" veya "anahtar" geçen dosyaları otomatik bulur
- 🎯 **PDF-Spesifik Eşleştirme**: Her PDF için kendi cevap anahtarını kullanır
- 🔢 **Soru-Cevap Eşleştirme**: Soru numarasına göre doğru cevabı bulur
- 📊 **Çoklu Test Desteği**: Matematik, Fizik gibi farklı test türlerini destekler

### Telegram Bot
- 🤖 **Rastgele Soru Gönderme**: Output klasöründeki sorulardan rastgele seçer
- 🔍 **Cevabı Göster Butonu**: Kullanıcı istediğinde cevabı gösterir
- 📊 **İstatistik Görüntüleme**: Bot durumu ve soru sayısı
- 🎯 **Akıllı Mesaj İşleme**: Matematik kelimelerini algılar
- 📱 **Kullanıcı Dostu Arayüz**: Kolay komutlar ve yardım menüsü

## 📦 Kurulum

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. PDF İşleme
```bash
# PDF dosyalarınızı proje klasörüne koyun
python question_extractor.py
```

### 3. Cevap Anahtarı İşleme
```bash
# Cevap anahtarı PDF'lerini output klasörüne koyun
# Dosya adında "cevap" veya "anahtar" geçmeli
# Örnek: "2013-ygs-cevap anahtarı.pdf"
python answer_key_extractor.py
```

### 4. Telegram Bot Kurulumu

#### 4.1 Bot Token Alın
1. [@BotFather](https://t.me/BotFather) ile konuşun
2. `/newbot` komutunu yazın
3. Bot adınızı ve kullanıcı adınızı girin
4. Bot token'ınızı kopyalayın

#### 4.2 Mistral AI API Key Alın (Opsiyonel)
1. [Mistral AI](https://console.mistral.ai/) hesabı oluşturun
2. API key'inizi alın

#### 4.3 Konfigürasyon
`bot_config.py` dosyasını düzenleyin:
```python
BOT_CONFIG = {
    'BOT_TOKEN': 'YOUR_ACTUAL_BOT_TOKEN_HERE',
    'MISTRAL_API_KEY': 'YOUR_MISTRAL_API_KEY_HERE',  # Opsiyonel
    # ... diğer ayarlar
}
```

#### 4.4 Bot'u Başlatın
```bash
python start_bot.py
```

## 🎯 Kullanım

### PDF İşleme
```bash
# Tek PDF işleme
python question_extractor.py

# Çıktı: output/klasör_adı/soru_*.png
```

### Telegram Bot Komutları
- `/start` - Bot'u başlat
- `/soru` - Rastgele matematik sorusu gönder
- `/istatistik` - Bot istatistiklerini göster
- `/yardim` - Yardım menüsü

### Cevap Anahtarı Kullanımı
1. **Cevap Anahtarı PDF'ini Yükleyin**: Dosya adında "cevap" veya "anahtar" geçmeli
2. **Otomatik İşleme**: Bot başlatıldığında otomatik olarak işlenir
3. **Cevabı Görüntüleme**: Soru gönderildikten sonra "🔍 Cevabı Göster" butonuna tıklayın

## 📁 Proje Yapısı

```
soru_v2/
├── question_extractor.py      # Ana PDF işleme scripti
├── answer_key_extractor.py    # Cevap anahtarı işleme scripti
├── telegram_bot.py            # Telegram bot kodu
├── bot_config.py              # Bot konfigürasyonu
├── start_bot.py               # Bot başlatma scripti
├── requirements.txt           # Python gereksinimleri
├── output/                    # İşlenmiş PDF çıktıları
│   ├── 2013-ygs/
│   │   ├── processed_2013-ygs.pdf
│   │   ├── question_list.txt
│   │   ├── 2013-ygs_answers.json
│   │   └── soru_*.png
│   ├── 2015-YGS/
│   │   ├── processed_2015-YGS.pdf
│   │   ├── question_list.txt
│   │   ├── 2015-YGS_answers.json
│   │   └── soru_*.png
│   ├── yks_tyt_2025_kitapcik_d250/
│   │   ├── processed_yks_tyt_2025_kitapcik_d250.pdf
│   │   ├── question_list.txt
│   │   ├── yks_tyt_2025_kitapcik_d250_answers.json
│   │   └── soru_*.png
│   └── batch_report.txt
└── README.md
```

## 🔧 Konfigürasyon

### Bot Ayarları (`bot_config.py`)
```python
BOT_CONFIG = {
    'BOT_TOKEN': 'your_bot_token',
    'MISTRAL_API_KEY': 'your_mistral_api_key',  # Opsiyonel
    'OUTPUT_DIR': 'output',
    'MAX_QUESTIONS_PER_DAY': 50,
    'ADMIN_USER_IDS': [],
}
```

### PDF İşleme Ayarları
- Talimat kutusu silme hassasiyeti: 5 piksel margin
- Soru tespit algoritması: Akıllı pattern matching
- Çıktı formatı: PNG (2x zoom)

### OCR Ayarları
- OCR motoru: Mistral AI (pixtral-12b-2409)
- Çözünürlük: 3x büyütme
- Dil desteği: Türkçe + İngilizce
- Güven eşiği: Otomatik

### Cevap Anahtarı Ayarları
- Otomatik algılama: Dosya adında "cevap" veya "anahtar" geçmeli
- PDF-spesifik eşleştirme: Her PDF kendi cevap anahtarını kullanır
- Soru aralığı: 1-50 arası sorular
- Test türü önceliği: Matematik > Diğer

## 📊 Örnek Çıktı

### PDF İşleme Sonucu
```
Toplam 3 PDF dosyası bulundu:
  1. 2015-YGS.pdf
  2. test1.pdf
  3. test2.pdf

TOPLU İŞLEM TAMAMLANDI
Toplam PDF: 3
Başarılı: 3
Başarısız: 0
Toplam Soru: 120
Süre: 10.12 saniye
```

### Bot Mesajı
```
📚 Soru 23
📄 Sayfa: 6
📍 Konum: sag
📁 Kaynak: 2013-ygs

Başarılar! 🍀
[PNG görsel]

[🔍 Cevabı Göster] [🎲 Başka Soru]
[📊 İstatistik] [🏠 Ana Menü]
```

### Cevap Anahtarı İşleme Sonucu
```
Cevap anahtarı bulundu: output\2013-ygs\2013-ygs-cevap anahtarı.pdf
Ana PDF: 2013-ygs
Cevap anahtarı işleniyor: output\2013-ygs\2013-ygs-cevap anahtarı.pdf
  TEMEL MATEMAT K TEST: 40 soru bulundu
Toplam 1 test bulundu
  TEMEL MATEMAT K TEST: 40 soru
Cevaplar kaydedildi: output\2013-ygs\2013-ygs_answers.json
```

### OCR İşleme Sonucu
```
Sayfa 1: Metin çıkarılamadı, OCR kullanılıyor...
    Mistral AI OCR kullanılıyor...
    Mistral AI ile 230 karakter çıkarıldı
  GENEL: 40 soru bulundu
```

## 🐛 Sorun Giderme

### Bot Token Hatası
```
❌ Bot token bulunamadı!
```
**Çözüm**: `bot_config.py` dosyasında token'ı doğru ayarlayın.

### Soru Bulunamadı
```
❌ Hiç soru bulunamadı.
```
**Çözüm**: Önce `python question_extractor.py` ile PDF işleme yapın.

### Bot Başlatılamıyor
```
❌ Bot başlatılırken hata
```
**Çözüm**: 
1. Token'ın doğru olduğundan emin olun
2. İnternet bağlantınızı kontrol edin
3. `requirements.txt` dosyasındaki paketleri yükleyin

### OCR Çalışmıyor
```
❌ Mistral AI API key bulunamadı!
```
**Çözüm**: 
1. `bot_config.py` dosyasında `MISTRAL_API_KEY`'i ayarlayın
2. Mistral AI hesabı oluşturun ve API key alın
3. API key'in doğru olduğundan emin olun

### Cevap Anahtarı Bulunamıyor
```
❌ Cevap bulunamadı
```
**Çözüm**:
1. Cevap anahtarı PDF'inin adında "cevap" veya "anahtar" geçtiğinden emin olun
2. PDF'in doğru klasörde olduğunu kontrol edin
3. PDF'in okunabilir olduğundan emin olun

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

- GitHub: [@suatklnc](https://github.com/suatklnc)
- Telegram: [@your_username](https://t.me/your_username)

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
