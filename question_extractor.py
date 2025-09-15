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
        
    def extract_all_questions(self, output_dir="individual_questions"):
        """Bölünmüş PDF'deki tüm soruları ayrı ayrı çıkarır"""
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        print("Soru algılama ve çıkarma başlıyor...")
        
        # Duplicate kontrolü kaldırıldı - talimatlar zaten filtreleniyor
        
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            
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
    pdf_path = "bolunmus_pdf.pdf"
    
    # Question extractor oluştur
    extractor = QuestionExtractor(pdf_path)
    
    # Tüm soruları çıkar
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
