import fitz  # PyMuPDF
import re

def debug_extract_function(pdf_path, page_num):
    """extract_question_as_image fonksiyonunu debug eder"""
    
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    print(f"=== SAYFA {page_num + 1} EXTRACT FUNCTION DEBUG ===")
    
    # Metni al
    page_text = page.get_text()
    lines = page_text.split('\n')
    
    # Soru numarası pattern'leri
    question_patterns = [
        r'^(\d+)\.\s*',  # "1. " gibi
        r'^Soru\s*(\d+)',  # "Soru 1" gibi
        r'^(\d+)\s*-\s*',  # "1 - " gibi
    ]
    
    # Talimat pattern'leri
    instruction_patterns = [
        r'^\d+\.\s*Bu testte \d+ soru vardır',
        r'^\d+\.\s*Cevaplarınızı, cevap kâğıdının Temel Matemati',
        r'^\d+\.\s*Test süresi',
        r'^\d+\.\s*Sınav başlamadan önce',
        r'^\d+\.\s*Talimatlar',
        r'^\d+\.\s*Yönergeler'
    ]
    
    questions = []
    current_question = None
    
    # Soruları tespit et
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Soru numarası var mı kontrol et
        question_number = None
        for pattern in question_patterns:
            match = re.search(pattern, line)
            if match:
                question_number = int(match.group(1))
                break
        
        if question_number:
            # Talimat mı kontrol et
            is_instruction = any(re.search(pattern, line) for pattern in instruction_patterns)
            
            if is_instruction:
                continue
            
            # Önceki soruyu kaydet
            if current_question:
                questions.append(current_question)
            
            # Yeni soru başlat
            current_question = {
                'number': question_number,
                'start_line': line_num,
                'text': line,
                'page': page_num,
                'full_text': line
            }
            
        elif current_question:
            # Mevcut soruya devam et
            current_question['full_text'] += ' ' + line
    
    # Son soruyu kaydet
    if current_question:
        questions.append(current_question)
    
    print(f"Algılanan sorular: {len(questions)}")
    
    # Her soru için extract_question_as_image testi
    for i, question in enumerate(questions):
        print(f"\n=== SORU {question['number']} EXTRACT TESTİ ===")
        
        try:
            # Soru metninin pozisyonunu bul
            question_rect = find_question_rect(page, question)
            
            if question_rect is None:
                print(f"  ❌ Pozisyon bulunamadı")
                continue
            
            print(f"  ✅ Pozisyon bulundu: {question_rect}")
            
            # Soru alanını genişlet
            margin_y = 10
            expanded_rect = fitz.Rect(
                0,  # Sol kenar = 0 (tam genişlik)
                max(0, question_rect.y0 - margin_y),  # Üst margin
                page.rect.width,  # Sağ kenar = sayfa genişliği (tam genişlik)
                min(page.rect.height, question_rect.y1 + margin_y)  # Alt margin
            )
            
            print(f"  ✅ Genişletilmiş alan: {expanded_rect}")
            
            # Dosya adı oluştur
            side = "sol" if (page_num % 2 == 0) else "sag"
            original_page_num = (page_num // 2) + 1
            filename = f"soru_{question['number']}_sayfa_{original_page_num}_{side}.png"
            
            print(f"  ✅ Dosya adı: {filename}")
            
        except Exception as e:
            print(f"  ❌ Hata: {e}")
    
    doc.close()

def find_question_rect(page, question):
    """Soru metninin sayfadaki pozisyonunu bulur"""
    
    try:
        # Sayfa metnini dict formatında al
        text_dict = page.get_text("dict")
        
        # Soru numarasını ara
        question_number = str(question['number'])
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        
                        # Soru numarasını içeren span'ı bul
                        if question_number in text and ('.' in text or 'Soru' in text):
                            # Bu span'ın pozisyonunu al
                            bbox = span["bbox"]
                            
                            # Soru alanını genişlet
                            question_rect = expand_question_area(page, bbox, question)
                            return question_rect
        
        return None
        
    except Exception as e:
        print(f"Soru pozisyon bulma hatası: {e}")
        return None

def expand_question_area(page, start_bbox, question):
    """Soru alanını genişletir - şıklar dahil"""
    
    try:
        # Başlangıç pozisyonu
        x0, y0, x1, y1 = start_bbox
        
        # Şıkları da dahil etmek için daha büyük alan hesapla
        text_length = len(question['full_text'])
        
        # Şıklar için ekstra alan ekle
        estimated_height = max(150, text_length * 0.8 + 100)  # Minimum 150px, şıklar için +100px
        
        # SADECE YÜKSEKLİK GENİŞLET - Genişlik değişmez
        expanded_rect = fitz.Rect(
            x0,  # Sol kenar aynı
            y0,  # Üst kenar aynı
            x1,  # Sağ kenar aynı (genişlik değişmez)
            min(page.rect.height, y0 + estimated_height)  # Şıklar dahil alt kenar genişlet
        )
        
        return expanded_rect
        
    except Exception as e:
        print(f"Alan genişletme hatası: {e}")
        return fitz.Rect(start_bbox)

if __name__ == "__main__":
    # İlk sayfayı debug et
    debug_extract_function("bolunmus_pdf.pdf", 0)
