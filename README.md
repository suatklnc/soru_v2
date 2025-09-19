# 📚 PDF Soru Çıkarma ve Telegram Bot Sistemi

Bu proje, PDF dosyalarından matematik sorularını otomatik olarak çıkarır ve Telegram bot üzerinden rastgele sorular gönderir.

## 🚀 Özellikler

### PDF İşleme
- ✅ **Otomatik PDF Bulma**: Dizindeki tüm PDF dosyalarını otomatik bulur
- ✅ **Çoklu PDF Desteği**: Birden fazla PDF dosyasını toplu olarak işler
- ✅ **Hassas Talimat Kutusu Silme**: 1. sorunun hemen üstünden keser
- ✅ **Akıllı Soru Tespit**: Soru numarası ile içerik doğru eşleştirilir
- ✅ **Şıklar Dahil Çıkarma**: Her soru tam olarak çıkarılır
- ✅ **Organize Çıktı**: Her PDF için ayrı klasör oluşturur

### Telegram Bot
- 🤖 **Rastgele Soru Gönderme**: Output klasöründeki sorulardan rastgele seçer
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

### 3. Telegram Bot Kurulumu

#### 3.1 Bot Token Alın
1. [@BotFather](https://t.me/BotFather) ile konuşun
2. `/newbot` komutunu yazın
3. Bot adınızı ve kullanıcı adınızı girin
4. Bot token'ınızı kopyalayın

#### 3.2 Bot Token'ı Ayarlayın
`bot_config.py` dosyasını düzenleyin:
```python
BOT_CONFIG = {
    'BOT_TOKEN': 'YOUR_ACTUAL_BOT_TOKEN_HERE',
    # ... diğer ayarlar
}
```

#### 3.3 Bot'u Başlatın
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

## 📁 Proje Yapısı

```
soru_v2/
├── question_extractor.py      # Ana PDF işleme scripti
├── telegram_bot.py            # Telegram bot kodu
├── bot_config.py              # Bot konfigürasyonu
├── start_bot.py               # Bot başlatma scripti
├── requirements.txt           # Python gereksinimleri
├── output/                    # İşlenmiş PDF çıktıları
│   ├── 2015-YGS/
│   │   ├── processed_2015-YGS.pdf
│   │   ├── question_list.txt
│   │   └── soru_*.png
│   ├── test1/
│   └── batch_report.txt
└── README.md
```

## 🔧 Konfigürasyon

### Bot Ayarları (`bot_config.py`)
```python
BOT_CONFIG = {
    'BOT_TOKEN': 'your_bot_token',
    'OUTPUT_DIR': 'output',
    'MAX_QUESTIONS_PER_DAY': 50,
    'ADMIN_USER_IDS': [],
}
```

### PDF İşleme Ayarları
- Talimat kutusu silme hassasiyeti: 5 piksel margin
- Soru tespit algoritması: Akıllı pattern matching
- Çıktı formatı: PNG (2x zoom)

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

Başarılar! 🍀
[PNG görsel]
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
