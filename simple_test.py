import fitz  # PyMuPDF
import os

def simple_test():
    """Basit test"""
    
    print("=== BASİT TEST ===")
    
    # QuestionExtractor'ı import et
    from question_extractor import QuestionExtractor
    
    # Extractor oluştur
    extractor = QuestionExtractor("bolunmus_pdf.pdf")
    
    # Sadece ilk sayfayı test et
    page = extractor.doc.load_page(0)
    page_text = page.get_text()
    
    print(f"Sayfa metni uzunluğu: {len(page_text)}")
    
    # Soruları tespit et
    questions_on_page = extractor.detect_questions_on_page(page, page_text, 0)
    
    print(f"Algılanan soru sayısı: {len(questions_on_page)}")
    
    for i, question in enumerate(questions_on_page):
        print(f"Soru {question['number']}: '{question['full_text'][:50]}...'")
        
        # Çıkarma testi
        try:
            extractor.extract_question_as_image(page, question, 0, i, "test_output")
            print(f"  ✅ Çıkarma başarılı")
        except Exception as e:
            print(f"  ❌ Çıkarma hatası: {e}")
    
    extractor.doc.close()

if __name__ == "__main__":
    simple_test()
