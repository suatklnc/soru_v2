import fitz  # PyMuPDF
import re

def debug_instruction_check(pdf_path, page_num):
    """Talimat kontrolünü debug eder"""
    
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    print(f"=== SAYFA {page_num + 1} TALİMAT KONTROLÜ DEBUG ===")
    
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
    
    print("=== TALİMAT KONTROLÜ TESTİ ===")
    
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
            print(f"\nSatır {line_num+1}: '{line}'")
            print(f"  -> SORU NUMARASI: {question_number}")
            
            # Talimat mı kontrol et
            is_instruction = any(re.search(pattern, line) for pattern in instruction_patterns)
            print(f"  -> TALİMAT MI: {'EVET' if is_instruction else 'HAYIR'}")
            
            if is_instruction:
                print(f"  -> ❌ TALİMAT OLARAK ATLANACAK")
            else:
                print(f"  -> ✅ SORU OLARAK KABUL EDİLECEK")
                
                # Pattern testleri
                for i, pattern in enumerate(instruction_patterns):
                    match = re.search(pattern, line)
                    if match:
                        print(f"    Pattern {i+1} eşleşti: {pattern}")
                        print(f"    Eşleşen: '{match.group()}'")
    
    doc.close()

if __name__ == "__main__":
    # İlk sayfayı debug et
    debug_instruction_check("bolunmus_pdf.pdf", 0)
