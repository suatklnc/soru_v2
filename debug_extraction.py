import fitz  # PyMuPDF
import re

def debug_extraction(pdf_path, page_num):
    """Soru çıkarma sürecini debug eder"""
    
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    print(f"=== SAYFA {page_num + 1} ÇIKARMA DEBUG ===")
    
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
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Soru numarası var mı?
        question_number = None
        for pattern in question_patterns:
            match = re.search(pattern, line)
            if match:
                question_number = int(match.group(1))
                break
        
        if question_number:
            # Talimat mı?
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
    
    # Her soru için pozisyon bulma testi
    for i, question in enumerate(questions):
        print(f"\n=== SORU {question['number']} POZİSYON TESTİ ===")
        
        try:
            # Sayfa metnini dict formatında al
            text_dict = page.get_text("dict")
            
            # Soru numarasını ara
            question_number = str(question['number'])
            
            found_position = False
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"]
                            
                            # Soru numarasını içeren span'ı bul
                            if question_number in text and ('.' in text or 'Soru' in text):
                                # Bu span'ın pozisyonunu al
                                bbox = span["bbox"]
                                print(f"  Pozisyon bulundu: {bbox}")
                                found_position = True
                                break
                        if found_position:
                            break
                    if found_position:
                        break
            
            if not found_position:
                print(f"  ❌ Pozisyon bulunamadı!")
                
        except Exception as e:
            print(f"  ❌ Hata: {e}")
    
    doc.close()

if __name__ == "__main__":
    # İlk sayfayı debug et
    debug_extraction("bolunmus_pdf.pdf", 0)
