import fitz  # PyMuPDF
import re

def analyze_page_content(pdf_path, page_num):
    """Sayfa içeriğini detaylı analiz eder"""
    
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    
    print(f"=== SAYFA {page_num + 1} ANALİZİ ===")
    print(f"Sayfa boyutu: {page.rect.width} x {page.rect.height}")
    print()
    
    # Metni al
    page_text = page.get_text()
    lines = page_text.split('\n')
    
    print("=== SATIR SATIR ANALİZ ===")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        print(f"Satır {i+1}: '{line}'")
        
        # Soru numarası var mı?
        patterns = [
            r'^(\d+)\.\s*',  # "1. " gibi
            r'^Soru\s*(\d+)',  # "Soru 1" gibi
            r'^(\d+)\s*-\s*',  # "1 - " gibi
        ]
        
        question_number = None
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                question_number = int(match.group(1))
                break
        
        if question_number:
            print(f"  -> SORU NUMARASI TESPİT EDİLDİ: {question_number}")
            
            # Matematik içeriği var mı?
            math_indicators = [
                r'[0-9]',  # Sayılar
                r'[+\-*/]',  # Matematik operatörleri
                r'kaçtır\?', r'bulunuz', r'hesaplayınız',  # Soru kelimeleri
                r'olduğuna göre', r'eşittir', r'çarpım', r'toplam',  # Matematik terimleri
                r'[A-E]\)',  # Şık işaretleri
                r'şekilde', r'grafik', r'diyagram',  # Görsel terimler
                r'cm', r'kg', r'm', r'°', r'%'  # Birimler
            ]
            
            has_math = any(re.search(pattern, line) for pattern in math_indicators)
            print(f"  -> MATEMATİK İÇERİĞİ: {'VAR' if has_math else 'YOK'}")
            
            # Talimat mı?
            instruction_patterns = [
                r'Bu testte \d+ soru vardır',
                r'Cevaplarınızı, cevap kâğıdının',
                r'Test süresi',
                r'Sınav başlamadan önce',
                r'Talimatlar',
                r'Yönergeler'
            ]
            
            is_instruction = any(re.search(pattern, line) for pattern in instruction_patterns)
            print(f"  -> TALİMAT MI: {'EVET' if is_instruction else 'HAYIR'}")
            
        print()
    
    doc.close()

if __name__ == "__main__":
    # İlk sayfayı analiz et
    analyze_page_content("bolunmus_pdf.pdf", 0)
