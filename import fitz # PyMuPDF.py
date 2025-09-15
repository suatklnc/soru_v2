import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import os
import io
import pytesseract
import re

class PDFImageExtractor:
    def __init__(self, pdf_path, split_pages=True):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.split_pages = split_pages
        if split_pages:
            self.split_pdf_vertically()
        
    def split_pdf_vertically(self):
        """PDF'in her sayfasını dikine ortadan ikiye böler"""
        print("PDF sayfaları ortadan ikiye bölünüyor...")
        
        new_doc = fitz.open()  # Yeni boş PDF
        
        for page_num in range(len(self.doc)):
            original_page = self.doc.load_page(page_num)
            page_rect = original_page.rect
            
            # Sayfa boyutları
            width = page_rect.width
            height = page_rect.height
            mid_x = width / 2
            
            # Sol yarım için crop alanı
            left_rect = fitz.Rect(0, 0, mid_x, height)
            # Sağ yarım için crop alanı  
            right_rect = fitz.Rect(mid_x, 0, width, height)
            
            # Sol yarımı yeni sayfaya ekle
            left_page = new_doc.new_page(width=mid_x, height=height)
            left_page.show_pdf_page(left_page.rect, self.doc, page_num, clip=left_rect)
            
            # Sağ yarımı yeni sayfaya ekle
            right_page = new_doc.new_page(width=mid_x, height=height)
            right_page.show_pdf_page(right_page.rect, self.doc, page_num, clip=right_rect)
            
            print(f"Sayfa {page_num+1} -> Sol yarım: Sayfa {len(new_doc)-1}, Sağ yarım: Sayfa {len(new_doc)}")
        
        # Eski PDF'i kapat, yenisini kullan
        self.doc.close()
        self.doc = new_doc
        
        print(f"Toplam {len(self.doc)} yarım sayfa oluşturuldu.")
        
    def save_split_pdf(self, output_path="split_pdf.pdf"):
        """Bölünmüş PDF'i kaydet (isteğe bağlı)"""
        self.doc.save(output_path)
        print(f"Bölünmüş PDF kaydedildi: {output_path}")
        
    def extract_all_images_with_context(self, output_dir="extracted_images"):
        """PDF'den tüm görselleri context bilgisiyle çıkarır"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        extracted_count = 0
        results = []
        
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            
            # Yöntem 1: Gömülü görselleri çıkar
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    # Görsel verisini al
                    xref = img[0]
                    pix = fitz.Pixmap(self.doc, xref)
                    
                    # RGB/GRAYSCALE kontrolü
                    if pix.n - pix.alpha < 4:  # GRAY veya RGB
                        img_data = pix.tobytes("png")
                        
                        # Minimum boyut kontrolü (çok küçük görselleri atla)
                        if pix.width > 50 and pix.height > 50:
                            # Dosya adını sayfa bölümüne göre ayarla
                            if self.split_pages:
                                side = "sol" if (page_num % 2 == 0) else "sag"
                                original_page_num = (page_num // 2) + 1
                                filename = f"sayfa_{original_page_num}_{side}_gorsel_{img_index+1}.png"
                            else:
                                filename = f"page_{page_num+1}_image_{img_index+1}.png"
                                
                            filepath = os.path.join(output_dir, filename)
                            
                            # Dosyayı kaydet
                            with open(filepath, "wb") as f:
                                f.write(img_data)
                            
                            # Context bilgisini topla
                            context = self.get_image_context(page, img, page_num)
                            
                            results.append({
                                'filename': filename,
                                'filepath': filepath,
                                'page': page_num + 1,
                                'dimensions': (pix.width, pix.height),
                                'context': context
                            })
                            
                            extracted_count += 1
                            print(f"Çıkarıldı: {filename} - {pix.width}x{pix.height}")
                    
                    pix = None  # Memory cleanup
                
                except Exception as e:
                    print(f"Sayfa {page_num+1}, Görsel {img_index+1} hatası: {e}")
                    continue
            
            # Yöntem 2: Sayfa screenshot'ı al (diyagramlar için)
            page_screenshot = self.extract_page_as_image(page, page_num, output_dir)
            if page_screenshot:
                results.append(page_screenshot)
                extracted_count += 1
        
        print(f"\nToplam {extracted_count} görsel çıkarıldı.")
        return results
    
    def get_image_context(self, page, img_info, page_num):
        """Görsel etrafındaki text context'ini çıkarır"""
        
        # Görsel pozisyonu
        img_rect = fitz.Rect(img_info[1:5])  # bbox
        
        # Görsel etrafındaki metni bul (genişletilmiş alan)
        expanded_rect = fitz.Rect(
            img_rect.x0 - 50,  # Sol
            img_rect.y0 - 100,  # Üst
            img_rect.x1 + 50,   # Sağ
            img_rect.y1 + 50    # Alt
        )
        
        # Bu alandaki metni çıkar
        text_blocks = page.get_text("dict", clip=expanded_rect)
        context_text = ""
        
        for block in text_blocks["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        context_text += span["text"] + " "
        
        # Soru numarasını tespit et
        question_number = self.extract_question_number(context_text)
        
        return {
            'surrounding_text': context_text.strip()[:200],  # İlk 200 karakter
            'question_number': question_number,
            'position': img_rect
        }
    
    def extract_question_number(self, text):
        """Metinden soru numarasını çıkarır"""
        patterns = [
            r'(\d+)\.',  # "8." gibi
            r'Soru\s*(\d+)',  # "Soru 8" gibi
            r'(\d+)\s*-',  # "8 -" gibi
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return None
    
    def extract_page_as_image(self, page, page_num, output_dir):
        """Sayfayı tamamen görsel olarak çıkarır (el çizimi diyagramlar için)"""
        
        try:
            # Yüksek çözünürlük matrix
            mat = fitz.Matrix(3.0, 3.0)  # 3x zoom
            pix = page.get_pixmap(matrix=mat)
            
            # PIL Image'a çevir
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            
            # Sadece matematik içeriği olan sayfaları kaydet
            page_text = page.get_text()
            if self.has_mathematical_content(page_text):
                if self.split_pages:
                    side = "sol" if (page_num % 2 == 0) else "sag"
                    original_page_num = (page_num // 2) + 1
                    filename = f"tam_sayfa_{original_page_num}_{side}.png"
                else:
                    filename = f"fullpage_{page_num+1}.png"
                    
                filepath = os.path.join(output_dir, filename)
                pil_image.save(filepath, "PNG", quality=95)
                
                return {
                    'filename': filename,
                    'filepath': filepath,
                    'page': page_num + 1,
                    'type': 'full_page',
                    'dimensions': pil_image.size,
                    'context': {'page_text_preview': page_text[:300]}
                }
        
        except Exception as e:
            print(f"Sayfa {page_num+1} screenshot hatası: {e}")
        
        return None
    
    def has_mathematical_content(self, text):
        """Sayfanın matematik içeriği olup olmadığını kontrol eder"""
        math_indicators = [
            'işleminin sonucu', 'kaçtır', 'olduğuna göre', 
            'eşittir', 'bulunuz', 'hesaplayınız', '°',
            'cm', 'kg', 'TL', '%', 'grafik', 'şekil',
            'daire', 'üçgen', 'alan', 'çevre'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in math_indicators)
    
    def filter_by_question_numbers(self, results, target_questions):
        """Belirli soru numaralarındaki görselleri filtreler"""
        filtered = []
        
        for result in results:
            q_num = result.get('context', {}).get('question_number')
            if q_num in target_questions:
                filtered.append(result)
        
        return filtered
    
    def analyze_and_categorize(self, results):
        """Çıkarılan görselleri analiz eder ve kategorize eder"""
        categorized = {
            'geometric_shapes': [],
            'graphs_charts': [],
            'diagrams': [],
            'text_heavy': [],
            'other': []
        }
        
        for result in results:
            filepath = result['filepath']
            if os.path.exists(filepath):
                # Görsel analizi
                img = cv2.imread(filepath)
                category = self.classify_image(img, result['context'])
                categorized[category].append(result)
        
        return categorized
    
    def classify_image(self, img, context):
        """Görseli içeriğine göre kategorize eder"""
        
        if img is None:
            return 'other'
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Daire tespiti
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                  param1=50, param2=30, minRadius=10, maxRadius=200)
        
        # Çizgi tespiti  
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        # Kategorilendirme
        context_text = context.get('surrounding_text', '').lower()
        
        if circles is not None and len(circles[0]) > 0:
            return 'geometric_shapes'
        elif lines is not None and len(lines) > 10:
            if 'grafik' in context_text or 'chart' in context_text:
                return 'graphs_charts'
            else:
                return 'geometric_shapes'
        elif any(word in context_text for word in ['şekil', 'diyagram', 'çizim']):
            return 'diagrams'
        elif len(context_text) > 100:
            return 'text_heavy'
        else:
            return 'other'

# Kullanım örneği
def main():
    # PDF dosya yolu
    pdf_path = "sorular.pdf"  # Gerçek PDF dosyanızın yolu
    
    # Extractor oluştur (split_pages=True ile otomatik bölme aktif)
    extractor = PDFImageExtractor(pdf_path, split_pages=True)
    
    # İsteğe bağlı: Bölünmüş PDF'i kaydet
    extractor.save_split_pdf("bolunmus_pdf.pdf")
    
    # Tüm görselleri çıkar
    print("Görsel çıkarma başlıyor...")
    results = extractor.extract_all_images_with_context()
    
    # Analiz et ve kategorize et
    print("\nGörseller analiz ediliyor...")
    categorized = extractor.analyze_and_categorize(results)
    
    # Sonuçları göster
    print(f"\n=== SONUÇLAR ===")
    for category, items in categorized.items():
        print(f"{category}: {len(items)} adet")
        for item in items[:3]:  # İlk 3 örnegi göster
            print(f"  - {item['filename']}")
    
    # Belirli sorular için filtrele (örnek)
    target_questions = [6, 8, 18, 37]  # Attığınız örneklerdeki soru numaraları
    filtered = extractor.filter_by_question_numbers(results, target_questions)
    print(f"\nHedef sorulardaki görseller: {len(filtered)} adet")
    
    return results, categorized

# Sadece bölme işlemi için ayrı fonksiyon
def split_pdf_only(pdf_path, output_path="split_pdf.pdf"):
    """Sadece PDF bölme işlemini yapar"""
    extractor = PDFImageExtractor(pdf_path, split_pages=True)
    extractor.save_split_pdf(output_path)
    print(f"PDF başarıyla bölündü: {output_path}")

if __name__ == "__main__":
    # Kullanım seçenekleri:
    
    # 1. Sadece PDF'i böl
    # split_pdf_only("matematik_sorulari.pdf", "bolunmus_matematik.pdf")
    
    # 2. PDF'i böl ve görselleri çıkar
    results, categorized = main()