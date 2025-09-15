import fitz  # PyMuPDF
import re

def debug_question_detection(pdf_path, page_num):
    """Soru algılama sürecini debug eder"""
    
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    print(f"=== SAYFA {page_num + 1} SORU ALGILAMA DEBUG ===")
    
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
    
    print("=== SORU ALGILAMA SÜRECİ ===")
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        print(f"\nSatır {i+1}: '{line}'")
        
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
            
            if not is_instruction:
                print(f"  -> ✅ SORU OLARAK KABUL EDİLECEK")
            else:
                print(f"  -> ❌ TALİMAT OLARAK ATLANACAK")
        else:
            print(f"  -> Soru numarası yok")
    
    doc.close()

if __name__ == "__main__":
    # İlk sayfayı debug et
    debug_question_detection("bolunmus_pdf.pdf", 0)
