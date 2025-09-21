#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Matematik testi çıkarma modülü
Birden fazla ders içeren PDF'lerden sadece matematik testini çıkarır
"""

import fitz  # PyMuPDF
import os
import re
from typing import Tuple, Optional

class MathTestExtractor:
    def __init__(self, pdf_path: str):
        """PDF dosyasını yükle"""
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def find_math_test_boundaries(self) -> Tuple[Optional[int], Optional[int]]:
        """Matematik testinin başlangıç ve bitiş sayfalarını bulur"""
        
        print(f"Matematik testi sınırları aranıyor: {self.pdf_path}")
        
        start_page = None
        end_page = None
        
        # Matematik testi başlangıç metni
        math_start_text = "2. Cevaplarınızı, cevap kâğıdının Temel Matematik Testi için ayrılan kısmına işaretleyiniz."
        
        # Fen bilimleri testi başlangıç metni (matematik testi bitişi)
        fen_start_text = "2. Cevaplarınızı, cevap kâğıdının Fen Bilimleri Testi için ayrılan kısmına işaretleyiniz."
        
        # Tüm sayfaları tara
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_text = page.get_text()
            
            # Matematik testi başlangıcını bul
            if math_start_text in page_text and start_page is None:
                start_page = page_num
                print(f"✅ Matematik testi başlangıcı bulundu: Sayfa {page_num + 1}")
                print(f"   Metin: {math_start_text}")
            
            # Fen bilimleri testi başlangıcını bul (matematik testi bitişi)
            if fen_start_text in page_text and end_page is None:
                end_page = page_num
                print(f"✅ Matematik testi bitişi bulundu: Sayfa {page_num + 1}")
                print(f"   Metin: {fen_start_text}")
                break  # İlk fen bilimleri testi bulunduğunda dur
        
        if start_page is not None and end_page is not None:
            print(f"📊 Matematik testi: Sayfa {start_page + 1} - {end_page} (toplam {end_page - start_page} sayfa)")
            return start_page, end_page
        else:
            print("❌ Matematik testi sınırları bulunamadı!")
            if start_page is None:
                print("   - Matematik testi başlangıcı bulunamadı")
            if end_page is None:
                print("   - Fen bilimleri testi başlangıcı bulunamadı")
            return None, None
    
    def extract_math_test(self, output_path: str) -> bool:
        """Matematik testini ayrı PDF olarak çıkarır"""
        
        try:
            # Matematik testi sınırlarını bul
            start_page, end_page = self.find_math_test_boundaries()
            
            if start_page is None or end_page is None:
                print("❌ Matematik testi çıkarılamadı - sınırlar bulunamadı")
                return False
            
            # Yeni PDF oluştur
            math_doc = fitz.open()
            
            # Matematik testi sayfalarını kopyala (ilk sayfa dahil, son sayfa hariç)
            for page_num in range(start_page, end_page):
                page = self.doc[page_num]
                new_page = math_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.show_pdf_page(new_page.rect, self.doc, page_num)
                print(f"   Sayfa {page_num + 1} kopyalandı")
            
            # Matematik testi PDF'ini kaydet
            math_doc.save(output_path)
            math_doc.close()
            
            print(f"✅ Matematik testi çıkarıldı: {output_path}")
            print(f"📄 Sayfa sayısı: {end_page - start_page}")
            
            return True
            
        except Exception as e:
            print(f"❌ Matematik testi çıkarılırken hata: {e}")
            return False
    
    def close(self):
        """PDF dosyasını kapat"""
        if hasattr(self, 'doc'):
            self.doc.close()

def extract_math_test_from_pdf(pdf_path: str, output_path: str = None) -> bool:
    """PDF'den matematik testini çıkarır"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF dosyası bulunamadı: {pdf_path}")
        return False
    
    # Çıktı dosya adını oluştur
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = f"{base_name}_matematik_testi.pdf"
    
    # Matematik testi çıkarıcı oluştur
    extractor = MathTestExtractor(pdf_path)
    
    try:
        # Matematik testini çıkar
        success = extractor.extract_math_test(output_path)
        return success
        
    finally:
        extractor.close()

if __name__ == "__main__":
    # Test
    pdf_path = "InternetKitapcigi29032018.pdf"
    
    if os.path.exists(pdf_path):
        print(f"🔍 Test: {pdf_path}")
        success = extract_math_test_from_pdf(pdf_path)
        
        if success:
            print("\n🎉 Matematik testi başarıyla çıkarıldı!")
        else:
            print("\n💥 Matematik testi çıkarılamadı!")
    else:
        print(f"❌ Test dosyası bulunamadı: {pdf_path}")
