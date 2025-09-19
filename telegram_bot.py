import os
import random
import glob
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import logging

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class QuestionBot:
    def __init__(self, token, output_dir="output"):
        self.token = token
        self.output_dir = output_dir
        self.question_files = []
        self.load_questions()
    
    def load_questions(self):
        """Output klasöründeki tüm soru dosyalarını yükle"""
        try:
            # Tüm PNG dosyalarını bul
            pattern = os.path.join(self.output_dir, "**", "soru_*.png")
            self.question_files = glob.glob(pattern, recursive=True)
            
            logger.info(f"Toplam {len(self.question_files)} soru dosyası yüklendi")
            
            if not self.question_files:
                logger.warning("Hiç soru dosyası bulunamadı!")
                
        except Exception as e:
            logger.error(f"Soru dosyaları yüklenirken hata: {e}")
            self.question_files = []
    
    def get_random_question(self):
        """Rastgele bir soru dosyası seç"""
        if not self.question_files:
            return None
        
        return random.choice(self.question_files)
    
    def get_question_info(self, file_path):
        """Soru dosyasından bilgi çıkar"""
        try:
            # Dosya adından bilgi çıkar
            filename = os.path.basename(file_path)
            # soru_23_sayfa_6_sag.png -> Soru 23, Sayfa 6, Sağ
            parts = filename.replace('.png', '').split('_')
            
            # PDF adını bul (dosya yolundan)
            pdf_name = "Bilinmiyor"
            try:
                # output/2015-YGS/soru_23_sayfa_6_sag.png -> 2015-YGS
                path_parts = file_path.replace(os.sep, '/').split('/')
                for i, part in enumerate(path_parts):
                    if part == 'output' and i + 1 < len(path_parts):
                        pdf_name = path_parts[i + 1]
                        break
            except:
                pass
            
            if len(parts) >= 4:
                question_num = parts[1]
                page_num = parts[3]
                side = parts[4] if len(parts) > 4 else "bilinmiyor"
                
                return {
                    'number': question_num,
                    'page': page_num,
                    'side': side,
                    'filename': filename,
                    'pdf_name': pdf_name
                }
        except Exception as e:
            logger.error(f"Soru bilgisi çıkarılırken hata: {e}")
        
        return {
            'number': '?',
            'page': '?',
            'side': '?',
            'filename': os.path.basename(file_path),
            'pdf_name': 'Bilinmiyor'
        }

# Bot instance
bot_instance = None

def create_main_keyboard():
    """Ana menü butonlarını oluştur"""
    keyboard = [
        [
            InlineKeyboardButton("🎲 Yeni Soru", callback_data="new_question"),
            InlineKeyboardButton("📊 İstatistik", callback_data="stats")
        ],
        [
            InlineKeyboardButton("🆘 Yardım", callback_data="help"),
            InlineKeyboardButton("ℹ️ Bot Bilgisi", callback_data="info")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_question_keyboard():
    """Soru menüsü butonlarını oluştur"""
    keyboard = [
        [
            InlineKeyboardButton("🎲 Başka Soru", callback_data="new_question"),
            InlineKeyboardButton("📊 İstatistik", callback_data="stats")
        ],
        [
            InlineKeyboardButton("🏠 Ana Menü", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot başlatma komutu"""
    welcome_message = """
🎓 **Matematik Soru Botu** 🎓

Merhaba! Ben matematik soruları gönderen bir botum.

Aşağıdaki butonları kullanarak kolayca navigasyon yapabilirsiniz! 🚀
    """
    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rastgele soru gönder"""
    global bot_instance
    
    if not bot_instance:
        await update.message.reply_text("❌ Bot henüz hazır değil. Lütfen daha sonra tekrar deneyin.")
        return
    
    # Rastgele soru seç
    question_file = bot_instance.get_random_question()
    
    if not question_file:
        await update.message.reply_text("❌ Hiç soru bulunamadı. Output klasörünü kontrol edin.")
        return
    
    try:
        # Soru bilgisini al
        question_info = bot_instance.get_question_info(question_file)
        
        # Dosyayı gönder
        with open(question_file, 'rb') as photo:
            caption = f"📚 **Soru {question_info['number']}**\n"
            caption += f"📄 Sayfa: {question_info['page']}\n"
            caption += f"📁 Kaynak: {question_info['pdf_name']}\n\n"
            caption += "Başarılar! 🍀"
            
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=create_question_keyboard()
            )
            
        logger.info(f"Soru gönderildi: {question_info['filename']}")
        
    except Exception as e:
        logger.error(f"Soru gönderilirken hata: {e}")
        await update.message.reply_text("❌ Soru gönderilirken bir hata oluştu.")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot istatistiklerini göster"""
    global bot_instance
    
    if not bot_instance:
        await update.message.reply_text("❌ Bot henüz hazır değil.")
        return
    
    total_questions = len(bot_instance.question_files)
    
    # PDF klasörlerini say
    pdf_folders = []
    if os.path.exists(bot_instance.output_dir):
        for item in os.listdir(bot_instance.output_dir):
            item_path = os.path.join(bot_instance.output_dir, item)
            if os.path.isdir(item_path) and item != "__pycache__":
                pdf_folders.append(item)
    
    stats_message = f"""
📊 **Bot İstatistikleri**

📚 Toplam Soru: {total_questions}
📁 PDF Klasörü: {len(pdf_folders)}
📂 Klasörler: {', '.join(pdf_folders[:5])}{'...' if len(pdf_folders) > 5 else ''}

Bot durumu: ✅ Aktif
    """
    
    await update.message.reply_text(stats_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım komutu"""
    help_message = """
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

Sorularınız için: @your_username
    """
    await update.message.reply_text(help_message, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buton tıklama işleyicisi"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "new_question":
        await send_question(update, context)
    elif query.data == "stats":
        await show_stats(update, context)
    elif query.data == "help":
        help_message = """
🆘 **Yardım Menüsü**

**Butonlar:**
🎲 Yeni Soru - Rastgele matematik sorusu gönder
📊 İstatistik - Bot istatistiklerini göster
🆘 Yardım - Bu yardım menüsü
ℹ️ Bot Bilgisi - Bot hakkında bilgi

**Nasıl Kullanılır:**
1. "Yeni Soru" butonuna tıklayın
2. Bot size rastgele bir matematik sorusu gönderir
3. Soruyu çözmeye çalışın!

**Not:** Bot, output klasöründeki tüm soruları rastgele seçer.
        """
        await query.edit_message_text(help_message, parse_mode='Markdown', reply_markup=create_main_keyboard())
    elif query.data == "info":
        info_message = """
ℹ️ **Bot Bilgisi**

🤖 **Matematik Soru Botu**
📚 **Toplam Soru:** 134 soru
📁 **PDF Kaynakları:** 3 farklı PDF
🔄 **Güncelleme:** Otomatik
⚡ **Hız:** Anında yanıt

**Özellikler:**
✅ Rastgele soru seçimi
✅ PDF kaynak bilgisi
✅ Kolay navigasyon
✅ Hızlı erişim

**Geliştirici:** @suatklnc
        """
        await query.edit_message_text(info_message, parse_mode='Markdown', reply_markup=create_main_keyboard())
    elif query.data == "main_menu":
        welcome_message = """
🎓 **Matematik Soru Botu** 🎓

Merhaba! Ben matematik soruları gönderen bir botum.

Aşağıdaki butonları kullanarak kolayca navigasyon yapabilirsiniz! 🚀
        """
        await query.edit_message_text(
            welcome_message, 
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genel mesaj işleyici"""
    message_text = update.message.text.lower()
    
    if any(word in message_text for word in ['soru', 'question', 'matematik', 'math']):
        await send_question(update, context)
    else:
        await update.message.reply_text(
            "Merhaba! /soru komutu ile matematik sorusu alabilirsiniz. 🎓"
        )

def main():
    """Bot ana fonksiyonu"""
    global bot_instance
    
    # Bot token'ını al
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable bulunamadı!")
        print("Lütfen bot token'ınızı ayarlayın:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
    
    # Bot instance oluştur
    bot_instance = QuestionBot(token)
    
    # Application oluştur
    application = Application.builder().token(token).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("soru", send_question))
    application.add_handler(CommandHandler("istatistik", show_stats))
    application.add_handler(CommandHandler("yardim", help_command))
    
    # Callback query handler (butonlar için)
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Bot'u başlat
    print("🤖 Telegram Bot başlatılıyor...")
    print(f"📚 {len(bot_instance.question_files)} soru yüklendi")
    
    application.run_polling()

if __name__ == '__main__':
    main()
