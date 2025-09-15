import fitz  # PyMuPDF
import re

def debug_full_process(pdf_path, page_num):
    """Tam süreci debug eder"""
    
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    print(f"=== SAYFA {page_num + 1} TAM SÜREÇ DEBUG ===")
    
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
    
    print("=== TAM SÜREÇ SIMULASYONU ===")
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        print(f"\nSatır {line_num+1}: '{line}'")
        
        # Soru numarası var mı?
        question_number = None
        for pattern in question_patterns:
            match = re.search(pattern, line)
            if match:
                question_number = int(match.group(1))
                break
        
        if question_number:
            print(f"  -> SORU NUMARASI: {question_number}")
            
            # Talimat mı?
            is_instruction = any(re.search(pattern, line) for pattern in instruction_patterns)
            print(f"  -> TALİMAT MI: {'EVET' if is_instruction else 'HAYIR'}")
            
            if is_instruction:
                print(f"  -> ❌ TALİMAT OLARAK ATLANACAK")
                continue
            
            # Önceki soruyu kaydet
            if current_question:
                questions.append(current_question)
                print(f"  -> ÖNCEKİ SORU KAYDEDİLDİ: {current_question['number']}")
            
            # Yeni soru başlat
            current_question = {
                'number': question_number,
                'start_line': line_num,
                'text': line,
                'page': page_num,
                'full_text': line
            }
            print(f"  -> ✅ YENİ SORU BAŞLATILDI: {question_number}")
            
        elif current_question:
            # Mevcut soruya devam et
            current_question['full_text'] += ' ' + line
            print(f"  -> SORUYA DEVAM: {current_question['number']}")
    
    # Son soruyu kaydet
    if current_question:
        questions.append(current_question)
        print(f"\nSON SORU KAYDEDİLDİ: {current_question['number']}")
    
    print(f"\n=== SONUÇ ===")
    print(f"Toplam algılanan soru: {len(questions)}")
    for q in questions:
        print(f"  - Soru {q['number']}: '{q['full_text'][:50]}...'")
    
    doc.close()

if __name__ == "__main__":
    # İlk sayfayı debug et
    debug_full_process("bolunmus_pdf.pdf", 0)
