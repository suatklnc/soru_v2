"""
Telegram Bot Konfigürasyon Dosyası
"""

# Bot ayarları
BOT_CONFIG = {
    # Bot token'ınızı buraya yazın
    'BOT_TOKEN': '8412008382:AAHzHiNkgZiF4_L5_NbQ43SSczIgo5Emj6E',
    
    # Mistral AI API Key (opsiyonel - OCR için)
    'MISTRAL_API_KEY': None,  # Mistral AI API key'inizi buraya yazın
    
    # Output klasörü yolu
    'OUTPUT_DIR': 'output',
    
    # Bot ayarları
    'MAX_QUESTIONS_PER_DAY': 50,  # Kullanıcı başına günlük maksimum soru
    'ADMIN_USER_IDS': [],  # Admin kullanıcı ID'leri
    
    # Mesaj ayarları
    'WELCOME_MESSAGE': """
🎓 **Matematik Soru Botu** 🎓

Merhaba! Ben matematik soruları gönderen bir botum.

**Komutlar:**
/soru - Rastgele bir matematik sorusu gönder
/istatistik - Bot istatistiklerini göster
/yardim - Yardım menüsü

Hazır mısın? /soru komutu ile başlayalım! 🚀
    """,
    
    'HELP_MESSAGE': """
🆘 **Yardım Menüsü**

**Komutlar:**
/soru - Rastgele matematik sorusu gönder
/istatistik - Bot istatistiklerini göster
/yardim - Bu yardım menüsünü göster

**Nasıl Kullanılır:**
1. /soru komutunu yazın
2. Bot size rastgele bir matematik sorusu gönderir
3. Soruyu çözmeye çalışın!

**Not:** Bot, output klasöründeki tüm soruları rastgele seçer.
    """,
    
    'ERROR_MESSAGES': {
        'no_questions': "❌ Hiç soru bulunamadı. Output klasörünü kontrol edin.",
        'bot_not_ready': "❌ Bot henüz hazır değil. Lütfen daha sonra tekrar deneyin.",
        'send_error': "❌ Soru gönderilirken bir hata oluştu.",
        'token_missing': "❌ Bot token bulunamadı! Lütfen bot_config.py dosyasını düzenleyin."
    }
}

# Kullanım talimatları
USAGE_INSTRUCTIONS = """
🤖 **Telegram Bot Kurulum Talimatları**

1. **Bot Token Alın:**
   - @BotFather'a gidin
   - /newbot komutunu yazın
   - Bot adınızı ve kullanıcı adınızı girin
   - Bot token'ınızı kopyalayın

2. **Bot Token'ı Ayarlayın:**
   - bot_config.py dosyasını açın
   - 'YOUR_BOT_TOKEN_HERE' yerine bot token'ınızı yazın
   - Dosyayı kaydedin

3. **Bot'u Çalıştırın:**
   python telegram_bot.py

4. **Bot'u Test Edin:**
   - Telegram'da botunuzu bulun
   - /start komutunu yazın
   - /soru komutu ile test edin

**Not:** Bot çalışmadan önce en az bir PDF işlemiş olmanız gerekiyor!
"""
