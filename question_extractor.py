import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import os
import io
import pytesseract
import re
from typing import List, Dict, Tuple

class QuestionExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.questions = []
        self.processed_doc = None  # İşlenmiş PDF için
    
    def preprocess_pdf(self):
        """PDF'i ön işleme tabi tutar: çizgi bulma, üst kısım silme, sayfa bölme"""
        
        print("PDF ön işleme başlıyor...")
        
        # 1. İlk sayfada dikey çizgiyi bul ve üst kısmı sil
        self.remove_top_section_from_first_page()
        
        # 2. Tüm sayfaları ortadan ikiye böl
        self.split_all_pages_in_half()
        
        print("PDF ön işleme tamamlandı.")
        return self.processed_doc
    
    def find_instruction_box_bottom(self):
        """Talimat kutusunun alt sınırını bulur - 1. ve 3. soruların hizasından"""
        
        first_page = self.doc.load_page(0)
        
        # Sayfa metnini al ve talimat satırlarını bul
        page_text = first_page.get_text()
        lines = page_text.split('\n')
        
        # Talimat satırlarını bul
        instruction_lines = []
        for i, line in enumerate(lines):
            line = line.strip()
            if any(keyword in line for keyword in ['Bu testte', 'Cevaplarınızı', 'Temel Matemati', 'Test süresi', 'Talimatlar']):
                instruction_lines.append((i, line))
        
        if not instruction_lines:
            print("Talimat satırları bulunamadı")
            return None
        
        # Son talimat satırını bul
        last_instruction_line = max(instruction_lines, key=lambda x: x[0])
        print(f"Son talimat satırı: '{last_instruction_line[1]}' (satır {last_instruction_line[0]})")
        
        # İlk 3 soruyu bul
        question_positions = []
        text_dict = first_page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        # Soru numaralarını bul (1., 2., 3.)
                        if re.match(r'^[123]\.\s*$', text) or re.match(r'^[123]\.\s*\d', text):
                            question_num = int(text.split('.')[0])
                            if question_num <= 3:
                                question_positions.append((question_num, span["bbox"][1]))
                                print(f"Soru {question_num} pozisyonu bulundu: y={span['bbox'][1]}")
        
        if len(question_positions) < 2:
            print("Yeterli soru pozisyonu bulunamadı")
            return None
        
        # 1. ve 3. soruların pozisyonlarını al
        question_positions.sort(key=lambda x: x[0])  # Soru numarasına göre sırala
        
        first_question_y = None
        third_question_y = None
        
        for q_num, y_pos in question_positions:
            if q_num == 1:
                first_question_y = y_pos
            elif q_num == 3:
                third_question_y = y_pos
        
        if first_question_y is None:
            print("1. soru pozisyonu bulunamadı")
            return None
        
        # 3. soru yoksa 1. sorudan hesapla, varsa ortalamasını al
        if third_question_y is None:
            # 3. soru yoksa, 1. sorudan yaklaşık 2 soru yüksekliği kadar aşağıda olacağını varsay
            estimated_third_y = first_question_y + 200  # Yaklaşık 2 soru yüksekliği
            print(f"3. soru bulunamadı, tahmini pozisyon: y={estimated_third_y}")
            reference_y = estimated_third_y
        else:
            reference_y = third_question_y
            print(f"3. soru pozisyonu kullanılıyor: y={reference_y}")
        
        # Talimat kutusunun alt sınırı = 1. ve 3. soruların hizasından biraz yukarı
        instruction_bottom_y = min(first_question_y, reference_y) - 30  # 30 piksel margin
        
        print(f"Talimat kutusu alt sınırı hesaplandı: y={instruction_bottom_y}")
        print(f"(1. soru: y={first_question_y}, referans: y={reference_y})")
        return instruction_bottom_y
    
    def remove_top_section_from_first_page(self):
        """İlk sayfadan talimat kutusunun alt sınırından itibaren keser"""
        
        print("İlk sayfadan talimat kutusu siliniyor...")
        
        # Talimat kutusunun alt sınırını bul
        instruction_bottom_y = self.find_instruction_box_bottom()
        
        if instruction_bottom_y is None:
            print("Talimat kutusu bulunamadı, üst kısım silinmiyor.")
            return
        
        # PDF koordinatları zaten doğru (zoom faktörü gerekmez)
        pdf_y_cut = instruction_bottom_y
        
        print(f"Talimat kutusu alt sınırı bulundu: y={pdf_y_cut}")
        print(f"Talimat kutusundan itibaren sayfa enine kesiliyor...")
        
        # İlk sayfayı al
        first_page = self.doc.load_page(0)
        page_rect = first_page.rect
        
        # Talimat kutusundan itibaren kes (dikdörtgen oluştur)
        crop_rect = fitz.Rect(0, pdf_y_cut, page_rect.width, page_rect.height)
        
        # Yeni PDF oluştur
        self.processed_doc = fitz.open()  # Boş PDF
        
        # İlk sayfa - talimat kutusu kesilmiş
        new_page = self.processed_doc.new_page(width=page_rect.width, height=page_rect.height - pdf_y_cut)
        new_page.show_pdf_page(new_page.rect, self.doc, 0, clip=crop_rect)
        
        # Diğer sayfaları ekle (kesilmeden)
        for page_num in range(1, len(self.doc)):
            original_page = self.doc.load_page(page_num)
            new_page = self.processed_doc.new_page(width=original_page.rect.width, height=original_page.rect.height)
            new_page.show_pdf_page(new_page.rect, self.doc, page_num)
        
        print(f"Talimat kutusu silindi. Yeni sayfa yüksekliği: {page_rect.height - pdf_y_cut}")
        print(f"Toplam {len(self.processed_doc)} sayfa oluşturuldu")
    
    def split_all_pages_in_half(self):
        """Tüm sayfaları ortadan ikiye böler"""
        
        print("Sayfalar ortadan ikiye bölünüyor...")
        
        # Yeni PDF oluştur
        split_doc = fitz.open()
        
        # İşlenmiş PDF'den sayfaları al (eğer varsa)
        source_doc = self.processed_doc if self.processed_doc else self.doc
        
        for page_num in range(len(source_doc)):
            page = source_doc.load_page(page_num)
            page_rect = page.rect
            
            # Sayfa genişliğinin yarısı
            half_width = page_rect.width / 2
            
            # Sol yarı
            left_rect = fitz.Rect(0, 0, half_width, page_rect.height)
            left_page = split_doc.new_page(width=half_width, height=page_rect.height)
            left_page.show_pdf_page(left_page.rect, source_doc, page_num, clip=left_rect)
            
            # Sağ yarı
            right_rect = fitz.Rect(half_width, 0, page_rect.width, page_rect.height)
            right_page = split_doc.new_page(width=half_width, height=page_rect.height)
            right_page.show_pdf_page(right_page.rect, source_doc, page_num, clip=right_rect)
            
            print(f"Sayfa {page_num + 1} ikiye bölündü")
        
        # İşlenmiş PDF'i güncelle
        if self.processed_doc:
            self.processed_doc.close()
        self.processed_doc = split_doc
        
        print(f"Toplam {len(self.processed_doc)} sayfa oluşturuldu (orijinal: {len(self.doc)})")
        
    def extract_all_questions(self, output_dir="individual_questions"):
        """Bölünmüş PDF'deki tüm soruları ayrı ayrı çıkarır"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        print("Soru algılama ve çıkarma başlıyor...")
        
        # Önce PDF'i ön işleme tabi tut
        if self.processed_doc is None:
            self.preprocess_pdf()
        
        # İşlenmiş PDF'i kullan
        doc_to_use = self.processed_doc if self.processed_doc else self.doc
        
        for page_num in range(len(doc_to_use)):
            page = doc_to_use.load_page(page_num)
            
            # Sayfa metnini al
            page_text = page.get_text()
            
            # Soruları tespit et
            questions_on_page = self.detect_questions_on_page(page, page_text, page_num)
            
            # Her soruyu ayrı görsel olarak kaydet
            for i, question in enumerate(questions_on_page):
                self.extract_question_as_image(page, question, page_num, i, output_dir)
        
        print(f"Toplam {len(self.questions)} soru çıkarıldı.")
        return self.questions
    
    def detect_questions_on_page(self, page, page_text, page_num):
        """Sayfadaki soruları tespit eder"""
        
        questions = []
        
        # Soru numarası pattern'leri
        question_patterns = [
            r'^(\d+)\.\s*',  # "1. " gibi
            r'^Soru\s*(\d+)',  # "Soru 1" gibi
            r'^(\d+)\s*-\s*',  # "1 - " gibi
        ]
        
        # Metni satırlara böl
        lines = page_text.split('\n')
        
        current_question = None
        
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
                if self.is_instruction(line):
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
        
        return questions
    
    def has_math_content(self, line):
        """Satırda matematik içeriği var mı kontrol eder - talimatları hariç tutar"""
        
        # Önce talimat mı kontrol et
        if self.is_instruction(line):
            return False
        
        # Matematik içeriği kontrolü
        math_indicators = [
            r'[+\-*/]',  # Matematik operatörleri
            r'kaçtır\?', r'bulunuz', r'hesaplayınız',  # Soru kelimeleri
            r'olduğuna göre', r'eşittir', r'çarpım', r'toplam',  # Matematik terimleri
            r'[A-E]\)',  # Şık işaretleri
            r'şekilde', r'grafik', r'diyagram',  # Görsel terimler
            r'cm', r'kg', r'm', r'°', r'%'  # Birimler
        ]
        
        # Sayılar + matematik terimleri birlikte olmalı
        has_numbers = bool(re.search(r'[0-9]', line))
        has_math_terms = any(re.search(pattern, line) for pattern in math_indicators)
        
        return has_numbers and has_math_terms
    
    def is_instruction(self, line):
        """Satırın talimat mı soru mu olduğunu kontrol eder"""
        
        # Çok spesifik talimat pattern'leri
        instruction_patterns = [
            r'^\d+\.\s*Bu testte \d+ soru vardır',
            r'^\d+\.\s*Cevaplarınızı, cevap kâğıdının Temel Matemati',
            r'^\d+\.\s*Test süresi',
            r'^\d+\.\s*Sınav başlamadan önce',
            r'^\d+\.\s*Talimatlar',
            r'^\d+\.\s*Yönergeler'
        ]
        
        # Sadece tam eşleşme kontrol et
        return any(re.search(pattern, line) for pattern in instruction_patterns)
    
    def is_end_of_question(self, line, lines, line_num):
        """Soru bitti mi kontrol eder - şıklar dahil"""
        
        # Şık pattern'leri kontrol et
        choice_patterns = [
            r'^[A-E]\)\s*',  # A) B) C) D) E)
            r'^[A-E]\.\s*',  # A. B. C. D. E.
            r'^[A-E]\s*\)',  # A ) B ) C ) D ) E )
        ]
        
        # Bu satır bir şık mı?
        is_choice = any(re.search(pattern, line) for pattern in choice_patterns)
        
        if is_choice:
            # Şık bulundu, sonraki satırları kontrol et
            for i in range(line_num + 1, min(line_num + 5, len(lines))):
                next_line = lines[i].strip()
                
                # Sonraki şık var mı?
                if any(re.search(pattern, next_line) for pattern in choice_patterns):
                    continue
                
                # Yeni soru numarası var mı?
                if re.search(r'(\d+)\.\s*|Soru\s*(\d+)|(\d+)\s*-\s*', next_line):
                    return True
                
                # Boş satır veya sayfa sonu
                if not next_line or i == len(lines) - 1:
                    return True
            
            return False
        
        # Şık değilse, sonraki satırlarda yeni soru numarası var mı?
        for i in range(line_num + 1, min(line_num + 3, len(lines))):
            next_line = lines[i].strip()
            if re.search(r'(\d+)\.\s*|Soru\s*(\d+)|(\d+)\s*-\s*', next_line):
                return True
        
        # Sayfa sonuna yakın mı?
        if line_num > len(lines) * 0.8:
            return True
            
        return False
    
    def extract_question_as_image(self, page, question, page_num, question_index, output_dir):
        """Tek bir soruyu görsel olarak çıkarır - sadece yatay kesim"""
        
        try:
            # Soru metninin pozisyonunu bul
            question_rect = self.find_question_rect(page, question)
            
            if question_rect is None:
                print(f"Sayfa {page_num+1}, Soru {question['number']}: Pozisyon bulunamadı")
                return
            
            # SADECE YATAY KESİM - Sayfa genişliğini kullan, sadece yükseklik ayarla
            margin_y = 10  # Sadece üst-alt margin
            expanded_rect = fitz.Rect(
                0,  # Sol kenar = 0 (tam genişlik)
                max(0, question_rect.y0 - margin_y),  # Üst margin
                page.rect.width,  # Sağ kenar = sayfa genişliği (tam genişlik)
                min(page.rect.height, question_rect.y1 + margin_y)  # Alt margin
            )
            
            # Yüksek çözünürlük matrix
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
            
            # Soru alanını crop et
            pix = page.get_pixmap(matrix=mat, clip=expanded_rect)
            
            # Dosya adı oluştur
            side = "sol" if (page_num % 2 == 0) else "sag"
            original_page_num = (page_num // 2) + 1
            filename = f"soru_{question['number']}_sayfa_{original_page_num}_{side}.png"
            
            filepath = os.path.join(output_dir, filename)
            
            # PNG olarak kaydet
            pix.save(filepath)
            
            # Soru bilgisini kaydet
            question_info = {
                'number': question['number'],
                'page': page_num + 1,
                'original_page': original_page_num,
                'side': side,
                'filename': filename,
                'filepath': filepath,
                'dimensions': (pix.width, pix.height),
                'text_preview': question['full_text'][:100] + '...' if len(question['full_text']) > 100 else question['full_text']
            }
            
            self.questions.append(question_info)
            print(f"Çıkarıldı: {filename} - Soru {question['number']}")
            
            pix = None  # Memory cleanup
            
        except Exception as e:
            print(f"Sayfa {page_num+1}, Soru {question['number']} hatası: {e}")
    
    def find_question_rect(self, page, question):
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
                                
                                # Soru alanını genişlet (tüm soru metni için)
                                question_rect = self.expand_question_area(page, bbox, question)
                                return question_rect
            
            return None
            
        except Exception as e:
            print(f"Soru pozisyon bulma hatası: {e}")
            return None
    
    def expand_question_area(self, page, start_bbox, question):
        """Soru alanını genişletir - şıklar dahil"""
        
        try:
            # Başlangıç pozisyonu
            x0, y0, x1, y1 = start_bbox
            
            # Şıkları da dahil etmek için daha büyük alan hesapla
            text_length = len(question['full_text'])
            
            # Şıklar için ekstra alan ekle
            # A) B) C) D) E) şıkları için yaklaşık 4-5 satır daha
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
    
    def get_question_statistics(self):
        """Soru istatistiklerini döndürür"""
        
        if not self.questions:
            return {}
        
        stats = {
            'total_questions': len(self.questions),
            'questions_by_page': {},
            'questions_by_side': {'sol': 0, 'sag': 0},
            'question_numbers': []
        }
        
        for q in self.questions:
            # Sayfa bazında
            page_key = f"sayfa_{q['original_page']}_{q['side']}"
            if page_key not in stats['questions_by_page']:
                stats['questions_by_page'][page_key] = 0
            stats['questions_by_page'][page_key] += 1
            
            # Taraf bazında
            stats['questions_by_side'][q['side']] += 1
            
            # Soru numaraları
            stats['question_numbers'].append(q['number'])
        
        stats['question_numbers'].sort()
        return stats
    
    def save_question_list(self, output_file="question_list.txt"):
        """Soru listesini text dosyasına kaydeder"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== ÇIKARILAN SORULAR ===\n\n")
            
            for q in sorted(self.questions, key=lambda x: x['number']):
                f.write(f"Soru {q['number']}:\n")
                f.write(f"  Dosya: {q['filename']}\n")
                f.write(f"  Sayfa: {q['original_page']} ({q['side']})\n")
                f.write(f"  Boyut: {q['dimensions'][0]}x{q['dimensions'][1]}\n")
                f.write(f"  Metin: {q['text_preview']}\n")
                f.write("-" * 50 + "\n")
        
        print(f"Soru listesi kaydedildi: {output_file}")

# Kullanım örneği
def main():
    # Bölünmüş PDF dosyası
    pdf_path = "sorular.pdf"
    
    # Question extractor oluştur
    extractor = QuestionExtractor(pdf_path)
    
    # PDF'i ön işleme tabi tut
    print("=== PDF ÖN İŞLEME ===")
    processed_doc = extractor.preprocess_pdf()
    
    # İşlenmiş PDF'i kaydet (isteğe bağlı)
    processed_doc.save("processed_sorular.pdf")
    print("İşlenmiş PDF kaydedildi: processed_sorular.pdf")
    
    # Tüm soruları çıkar
    print("\n=== SORU ÇIKARMA ===")
    questions = extractor.extract_all_questions()
    
    # İstatistikleri göster
    stats = extractor.get_question_statistics()
    print(f"\n=== İSTATİSTİKLER ===")
    print(f"Toplam soru: {stats['total_questions']}")
    print(f"Sol taraf: {stats['questions_by_side']['sol']}")
    print(f"Sağ taraf: {stats['questions_by_side']['sag']}")
    print(f"Soru numaraları: {stats['question_numbers']}")
    
    # Soru listesini kaydet
    extractor.save_question_list()
    
    return questions, stats

if __name__ == "__main__":
    questions, stats = main()
