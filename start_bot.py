#!/usr/bin/env python3
"""
Telegram Bot Başlatma Scripti
"""

import os
import sys
from bot_config import BOT_CONFIG, USAGE_INSTRUCTIONS

def check_requirements():
    """Gerekli dosyaları kontrol et"""
    print("🔍 Gerekli dosyalar kontrol ediliyor...")
    
    # Bot token kontrolü
    if BOT_CONFIG['BOT_TOKEN'] == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Bot token ayarlanmamış!")
        print(USAGE_INSTRUCTIONS)
        return False
    
    # Output klasörü kontrolü
    if not os.path.exists(BOT_CONFIG['OUTPUT_DIR']):
        print(f"❌ Output klasörü bulunamadı: {BOT_CONFIG['OUTPUT_DIR']}")
        print("Lütfen önce PDF işleme yapın: python question_extractor.py")
        return False
    
    # Soru dosyaları kontrolü
    import glob
    question_files = glob.glob(os.path.join(BOT_CONFIG['OUTPUT_DIR'], "**", "soru_*.png"), recursive=True)
    
    if not question_files:
        print("❌ Hiç soru dosyası bulunamadı!")
        print("Lütfen önce PDF işleme yapın: python question_extractor.py")
        return False
    
    print(f"✅ {len(question_files)} soru dosyası bulundu")
    return True

def main():
    """Ana fonksiyon"""
    print("🤖 Telegram Bot Başlatılıyor...")
    print("=" * 50)
    
    # Kontrolleri yap
    if not check_requirements():
        sys.exit(1)
    
    # Environment variable ayarla
    os.environ['TELEGRAM_BOT_TOKEN'] = BOT_CONFIG['BOT_TOKEN']
    
    # Bot'u başlat
    try:
        from telegram_bot import main as bot_main
        print("🚀 Bot başlatılıyor...")
        bot_main()
    except KeyboardInterrupt:
        print("\n👋 Bot durduruldu.")
    except Exception as e:
        print(f"❌ Bot başlatılırken hata: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
