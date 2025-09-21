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
        
        # Talimat kutusunun alt sınırı = 1. sorunun hemen üstünden (çok küçük margin)
        instruction_bottom_y = first_question_y - 5  # Sadece 5 piksel margin - 1. sorunun hemen üstü
        
        print(f"Talimat kutusu alt sınırı hesaplandı: y={instruction_bottom_y}")
        print(f"(1. soru: y={first_question_y}, kesme noktası: y={instruction_bottom_y})")
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
        
        # Tüm soruları topla
        all_questions = []
        for page_num in range(len(doc_to_use)):
            page = doc_to_use.load_page(page_num)
            page_text = page.get_text()
            questions_on_page = self.detect_questions_on_page(page, page_text, page_num)
            all_questions.extend(questions_on_page)
        
        # Benzersiz soru numaralarını filtrele
        unique_questions = {}
        for question in all_questions:
            q_num = question['number']
            if q_num not in unique_questions:
                unique_questions[q_num] = question
        
        # Benzersiz soruları sırala ve çıkar
        sorted_questions = sorted(unique_questions.values(), key=lambda x: x['number'])
        
        # self.questions listesini temizle
        self.questions = []
        
        for question in sorted_questions:
            page_num = question['page']
            page = doc_to_use.load_page(page_num)
            self.extract_question_as_image(page, question, page_num, 0, output_dir)
        
        print(f"Toplam {len(self.questions)} soru çıkarıldı.")
        return self.questions
    
    def detect_questions_on_page(self, page, page_text, page_num):
        """Sayfadaki soruları tespit eder - şıklar dahil"""
        
        questions = []
        
        # Sayfa metnini dict formatında al (pozisyon bilgisi için)
        text_dict = page.get_text("dict")
        
        # Tüm metin bloklarını topla ve sırala
        text_blocks = []
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            text_blocks.append({
                                'text': text,
                                'bbox': span["bbox"],
                                'y': span["bbox"][1],  # Y pozisyonu
                                'span_info': {
                                    'flags': span.get("flags", 0),
                                    'font': span.get("font", ""),
                                    'size': span.get("size", 0)
                                }
                            })
        
        # Y pozisyonuna göre sırala
        text_blocks.sort(key=lambda x: x['y'])
        
        # Soru numarası pattern'leri
        question_patterns = [
            r'^(\d+)\.\s*',  # "1. " gibi
            r'^Soru\s*(\d+)',  # "Soru 1" gibi
            r'^(\d+)\s*-\s*',  # "1 - " gibi
        ]
        
        # Önce tüm soru numaralarını ve pozisyonlarını bul
        question_starts = []
        for i, block in enumerate(text_blocks):
            text = block['text']
            
            # Soru numarası var mı kontrol et - SADECE satır başında
            question_number = None
            for pattern in question_patterns:
                match = re.search(pattern, text)
                if match:
                    question_number = int(match.group(1))
                    # Geçerli soru numarası mı? (1-50 arası)
                    if 1 <= question_number <= 50:
                        break
                    else:
                        question_number = None
            
            if question_number:
                # Talimat mı kontrol et
                if self.is_instruction(text):
                    continue
                
                # Span bilgilerini al (font kalınlığı için)
                span_info = block.get('span_info', {})
                
                # Gerçek soru başlangıcı mı kontrol et
                if not self.is_question_start(text, question_number, span_info):
                    continue
                
                # Ek güvenlik kontrolü: Eğer metin çok uzunsa veya içinde soru içeriği varsa atla
                if len(text.strip()) > 20:  # Çok uzun metinler soru içeriği içerir
                    continue
                
                # İçinde soru içeriği olan kelimeler var mı kontrol et
                content_words = ['saat', 'dakika', 'gün', 'Mart', 'matematik', 'geometri', 'öğretmen', 'ders', 'vermiştir', 'toplam']
                if any(word in text for word in content_words):
                    continue
                
                question_starts.append({
                    'number': question_number,
                    'start_index': i,
                    'start_bbox': block['bbox'],
                    'start_text': text
                })
        
        # Her soru için içeriği topla
        for i, q_start in enumerate(question_starts):
            start_idx = q_start['start_index']
            end_idx = question_starts[i + 1]['start_index'] if i + 1 < len(question_starts) else len(text_blocks)
            
            # Bu soruya ait tüm metinleri topla
            question_text_parts = []
            has_choices = False
            
            for j in range(start_idx, end_idx):
                block = text_blocks[j]
                text = block['text']
                question_text_parts.append(text)
                
                # Şık pattern'i kontrol et
                if re.search(r'^[A-E]\)\s*', text):
                    has_choices = True
            
            # Soru bilgilerini oluştur
            question = {
                'number': q_start['number'],
                'start_bbox': q_start['start_bbox'],
                'text': q_start['start_text'],
                'page': page_num,
                'full_text': ' '.join(question_text_parts),
                'has_choices': has_choices
            }
            
            questions.append(question)
        
        return questions
    
    def is_question_start(self, text, question_number, span_info=None):
        """Bir metnin gerçekten soru başlangıcı olup olmadığını kontrol eder"""
        
        # Soru başlangıcı karakteristikleri:
        # 1. Satır başında olmalı
        # 2. Sadece sayı ve nokta içermeli (veya "Soru" kelimesi)
        # 3. Ardından boşluk ve büyük harf gelmeli
        # 4. İçinde "saat", "dakika", "gün" gibi kelimeler olmamalı
        # 5. Soru içeriği olmamalı (sadece numara olmalı)
        # 6. Font kalınlığı kontrolü (eğer span_info varsa)
        
        text = text.strip()
        
        # Satır başında sayı kontrolü - sadece "X." formatında olmalı
        if not re.match(r'^\d+\.\s*$|^Soru\s*\d+\s*$', text):
            return False
        
        # İçinde soru içeriği olmamalı (sadece numara olmalı)
        if len(text) > 15:  # Çok uzun ise soru içeriği var demektir
            return False
        
        # Soru numarası 1-50 arasında olmalı
        if not (1 <= question_number <= 50):
            return False
        
        # Ek kontrol: Eğer metin sadece sayı ve nokta ise, soru içeriği yok demektir
        # Ama eğer içinde "saat", "dakika", "gün", "Mart" gibi kelimeler varsa soru içeriği var demektir
        content_indicators = ['saat', 'dakika', 'gün', 'Mart', 'matematik', 'geometri', 'öğretmen', 'ders']
        if any(indicator in text for indicator in content_indicators):
            return False
        
        # Font kalınlığı kontrolü (eğer span_info varsa)
        if span_info and 'flags' in span_info:
            # Font flags kontrolü - bold olup olmadığını kontrol et
            # PyMuPDF'de bold font genellikle flags & 2^16 (65536) ile kontrol edilir
            is_bold = bool(span_info['flags'] & 16)  # Bold flag
            if not is_bold:
                # Eğer font kalın değilse, bu muhtemelen soru içeriği değil
                # Ama sadece sayı ve nokta ise yine de kabul et
                if not re.match(r'^\d+\.\s*$', text):
                    return False
        
        return True
    
    def has_math_content(self, line):
        """Satırda matematik içeriği var mı kontrol eder - talimatları hariç tutar"""
        
        # Önce basit talimat kontrolü (recursion'ı önlemek için)
        instruction_keywords = [
            'Bu testte', 'Cevaplarınızı', 'Test süresi', 'Sınav başlamadan',
            'Talimatlar', 'Yönergeler', 'işaretleyiniz'
        ]
        
        if any(keyword in line for keyword in instruction_keywords):
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
        
        # Çok spesifik talimat pattern'leri - sadece gerçek talimatlar
        instruction_patterns = [
            r'^\d+\.\s*Bu testte \d+ soru vardır',
            r'^\d+\.\s*Cevaplarınızı, cevap kâğıdının Temel Matematik Testi için ayrılan kısmına işaretleyiniz\.',
            r'^\d+\.\s*Test süresi',
            r'^\d+\.\s*Sınav başlamadan önce',
            r'^\d+\.\s*Talimatlar',
            r'^\d+\.\s*Yönergeler',
            r'^\d+\.\s*Bu testte',
            r'^\d+\.\s*Cevaplarınızı.*işaretleyiniz'
        ]
        
        # Sadece tam eşleşme kontrol et
        is_instruction_text = any(re.search(pattern, line) for pattern in instruction_patterns)
        
        # Ek kontrol: Eğer talimat pattern'i varsa ama matematik içeriği de varsa, bu bir soru olabilir
        if is_instruction_text:
            # Basit matematik kontrolü (recursion'ı önlemek için)
            has_numbers = bool(re.search(r'[0-9]', line))
            has_math_operators = bool(re.search(r'[+\-*/=]', line))
            has_question_words = bool(re.search(r'(kaçtır|bulunuz|hesaplayınız|olduğuna göre)', line))
            
            if has_numbers and (has_math_operators or has_question_words):
                return False  # Matematik içeriği varsa soru olarak kabul et
        
        return is_instruction_text
    
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
                            
                            # Soru numarasını içeren span'ı bul - sadece "X." formatında
                            if text.strip() == f"{question_number}.":
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
        """Soru alanını genişletir - şıklar dahil, bir sonraki soruya kadar"""
        
        try:
            # Başlangıç pozisyonu
            x0, y0, x1, y1 = start_bbox
            
            # Soru numarasını da dahil etmek için üst kenarı biraz yukarı çek
            # Soru numarası genellikle soru metninden 10-20 piksel yukarıda olur
            question_number_margin = 15  # Soru numarası için ekstra alan (daha az margin)
            start_y = max(0, y0 - question_number_margin)
            
            # Bir sonraki sorunun başlangıcını bul
            next_question_y = self.find_next_question_start(page, question['number'])
            
            if next_question_y is not None:
                # Bir sonraki soru bulundu, onun başlangıcına kadar genişlet
                # Ama biraz margin bırak
                margin = 20
                end_y = max(start_y + 150, next_question_y - margin)  # Minimum 150px yükseklik
            else:
                # Bir sonraki soru bulunamadı, şıklar için daha fazla alan bırak
                text_length = len(question['full_text'])
                # Şıklar için ekstra alan ekle
                if question.get('has_choices', False):
                    estimated_height = max(250, text_length * 0.8 + 200)  # Şıklar için daha fazla alan
                else:
                    estimated_height = max(200, text_length * 1.0 + 150)
                end_y = min(page.rect.height, start_y + estimated_height)
            
            # SADECE YÜKSEKLİK GENİŞLET - Genişlik değişmez
            expanded_rect = fitz.Rect(
                x0,  # Sol kenar aynı
                start_y,  # Üst kenar - soru numarası dahil
                x1,  # Sağ kenar aynı (genişlik değişmez)
                end_y  # Bir sonraki soruya kadar veya hesaplanan yükseklik
            )
            
            return expanded_rect
            
        except Exception as e:
            print(f"Alan genişletme hatası: {e}")
            return fitz.Rect(start_bbox)
    
    def find_next_question_start(self, page, current_question_num):
        """Bir sonraki sorunun başlangıç pozisyonunu bulur"""
        
        try:
            # Sayfa metnini dict formatında al
            text_dict = page.get_text("dict")
            
            # Sonraki soru numarası
            next_question_num = current_question_num + 1
            
            # Tüm metin bloklarını topla ve sırala
            text_blocks = []
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                text_blocks.append({
                                    'text': text,
                                    'bbox': span["bbox"],
                                    'y': span["bbox"][1]
                                })
            
            # Y pozisyonuna göre sırala
            text_blocks.sort(key=lambda x: x['y'])
            
            # Sonraki soru numarasını ara
            for block in text_blocks:
                text = block['text']
                
                # Soru numarası pattern'leri
                question_patterns = [
                    r'^(\d+)\.\s*',  # "1. " gibi
                    r'^Soru\s*(\d+)',  # "Soru 1" gibi
                    r'^(\d+)\s*-\s*',  # "1 - " gibi
                ]
                
                for pattern in question_patterns:
                    match = re.search(pattern, text)
                    if match:
                        question_number = int(match.group(1))
                        if question_number == next_question_num and not self.is_instruction(text):
                            return block['y']
            
            return None
            
        except Exception as e:
            print(f"Sonraki soru bulma hatası: {e}")
            return None
    
    def get_question_statistics(self):
        """Soru istatistiklerini döndürür"""
        
        if not self.questions:
            return {
                'total_questions': 0,
                'questions_by_page': {},
                'questions_by_side': {'sol': 0, 'sag': 0},
                'question_numbers': []
            }
        
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

# Matematik testi çıkarma fonksiyonu
def extract_math_test_from_pdf(pdf_path: str, output_path: str = None) -> bool:
    """PDF'den matematik testini çıkarır"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF dosyası bulunamadı: {pdf_path}")
        return False
    
    # Çıktı dosya adını oluştur
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = f"{base_name}_matematik_testi.pdf"
    
    try:
        # PDF dosyasını yükle
        doc = fitz.open(pdf_path)
        
        print(f"Matematik testi sınırları aranıyor: {pdf_path}")
        
        start_page = None
        end_page = None
        
        # Matematik testi başlangıç metni
        math_start_text = "2. Cevaplarınızı, cevap kâğıdının Temel Matematik Testi için ayrılan kısmına işaretleyiniz."
        
        # Fen bilimleri testi başlangıç metni (matematik testi bitişi)
        fen_start_text = "2. Cevaplarınızı, cevap kâğıdının Fen Bilimleri Testi için ayrılan kısmına işaretleyiniz."
        
        # Tüm sayfaları tara
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            # Matematik testi başlangıcını bul
            if math_start_text in page_text and start_page is None:
                start_page = page_num
                print(f"✅ Matematik testi başlangıcı bulundu: Sayfa {page_num + 1}")
            
            # Fen bilimleri testi başlangıcını bul (matematik testi bitişi)
            if fen_start_text in page_text and end_page is None:
                end_page = page_num
                print(f"✅ Matematik testi bitişi bulundu: Sayfa {page_num + 1}")
                break  # İlk fen bilimleri testi bulunduğunda dur
        
        if start_page is not None and end_page is not None:
            print(f"📊 Matematik testi: Sayfa {start_page + 1} - {end_page} (toplam {end_page - start_page} sayfa)")
            
            # Yeni PDF oluştur
            math_doc = fitz.open()
            
            # Matematik testi sayfalarını kopyala (ilk sayfa dahil, son sayfa hariç)
            for page_num in range(start_page, end_page):
                page = doc[page_num]
                new_page = math_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.show_pdf_page(new_page.rect, doc, page_num)
                print(f"   Sayfa {page_num + 1} kopyalandı")
            
            # Matematik testi PDF'ini kaydet
            math_doc.save(output_path)
            math_doc.close()
            doc.close()
            
            print(f"✅ Matematik testi çıkarıldı: {output_path}")
            print(f"📄 Sayfa sayısı: {end_page - start_page}")
            
            return True
        else:
            print("❌ Matematik testi sınırları bulunamadı!")
            if start_page is None:
                print("   - Matematik testi başlangıcı bulunamadı")
            if end_page is None:
                print("   - Fen bilimleri testi başlangıcı bulunamadı")
            doc.close()
            return False
            
    except Exception as e:
        print(f"❌ Matematik testi çıkarılırken hata: {e}")
        return False

# Çoklu PDF işleme fonksiyonu
def process_multiple_pdfs(pdf_directory=".", output_base_dir="output"):
    """Birden fazla PDF dosyasını toplu olarak işler"""
    
    import glob
    import os
    from datetime import datetime
    
    # PDF dosyalarını bul
    pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
    
    # processed_sorular.pdf'yi hariç tut
    pdf_files = [f for f in pdf_files if not f.endswith("processed_sorular.pdf")]
    
    if not pdf_files:
        print("Dizinde PDF dosyası bulunamadı!")
        return None
    
    print(f"Toplam {len(pdf_files)} PDF dosyası bulundu:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {os.path.basename(pdf_file)}")
    
    # Çıktı klasörünü oluştur
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir)
    
    # Toplu işlem raporu
    batch_report = {
        'start_time': datetime.now(),
        'total_files': len(pdf_files),
        'processed_files': 0,
        'failed_files': 0,
        'total_questions': 0,
        'results': []
    }
    
    # Her PDF'i işle
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n{'='*60}")
        print(f"PDF {i}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
        print(f"{'='*60}")
        
        try:
            # PDF adından çıktı klasörü oluştur
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_dir = os.path.join(output_base_dir, pdf_name)
            
            # Önce matematik testi çıkarmayı dene
            math_test_path = f"{pdf_name}_matematik_testi.pdf"
            math_extracted = extract_math_test_from_pdf(pdf_path, math_test_path)
            
            # Hangi PDF'i kullanacağımızı belirle
            if math_extracted:
                print(f"📚 Matematik testi çıkarıldı, matematik testi işleniyor...")
                pdf_to_process = math_test_path
                output_dir = os.path.join(output_base_dir, f"{pdf_name}_matematik")
            else:
                print(f"📄 Matematik testi çıkarılamadı, orijinal PDF işleniyor...")
                pdf_to_process = pdf_path
            
            # Question extractor oluştur
            extractor = QuestionExtractor(pdf_to_process)
            
            # PDF'i ön işleme tabi tut
            print("PDF ön işleme başlıyor...")
            processed_doc = extractor.preprocess_pdf()
            
            # İşlenmiş PDF'i kaydet
            processed_pdf_path = os.path.join(output_dir, f"processed_{pdf_name}.pdf")
            os.makedirs(output_dir, exist_ok=True)
            processed_doc.save(processed_pdf_path)
            print(f"İşlenmiş PDF kaydedildi: {processed_pdf_path}")
            
            # Tüm soruları çıkar
            print("Soru çıkarma başlıyor...")
            questions = extractor.extract_all_questions(output_dir)
            
            # İstatistikleri al
            stats = extractor.get_question_statistics()
            
            # Soru listesini kaydet
            question_list_path = os.path.join(output_dir, "question_list.txt")
            extractor.save_question_list(question_list_path)
            
            # Sonuçları rapora ekle
            result = {
                'pdf_name': os.path.basename(pdf_path),
                'processed_pdf': os.path.basename(pdf_to_process),
                'output_dir': output_dir,
                'total_questions': stats['total_questions'],
                'questions_by_side': stats['questions_by_side'],
                'question_numbers': stats['question_numbers'],
                'math_test_extracted': math_extracted,
                'status': 'success'
            }
            batch_report['results'].append(result)
            batch_report['processed_files'] += 1
            batch_report['total_questions'] += stats['total_questions']
            
            print(f"✅ Başarıyla tamamlandı: {stats['total_questions']} soru çıkarıldı")
            
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
            result = {
                'pdf_name': os.path.basename(pdf_path),
                'error': str(e),
                'status': 'failed'
            }
            batch_report['results'].append(result)
            batch_report['failed_files'] += 1
    
    # Toplu işlem raporunu kaydet
    batch_report['end_time'] = datetime.now()
    batch_report['duration'] = (batch_report['end_time'] - batch_report['start_time']).total_seconds()
    
    # Raporu kaydet
    report_path = os.path.join(output_base_dir, "batch_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=== TOPLU PDF İŞLEME RAPORU ===\n\n")
        f.write(f"Başlangıç Zamanı: {batch_report['start_time']}\n")
        f.write(f"Bitiş Zamanı: {batch_report['end_time']}\n")
        f.write(f"Toplam Süre: {batch_report['duration']:.2f} saniye\n")
        f.write(f"Toplam PDF: {batch_report['total_files']}\n")
        f.write(f"Başarılı: {batch_report['processed_files']}\n")
        f.write(f"Başarısız: {batch_report['failed_files']}\n")
        f.write(f"Toplam Soru: {batch_report['total_questions']}\n\n")
        
        f.write("=== DETAYLI SONUÇLAR ===\n")
        for result in batch_report['results']:
            f.write(f"\nPDF: {result['pdf_name']}\n")
            f.write(f"Durum: {result['status']}\n")
            if result['status'] == 'success':
                f.write(f"Çıktı Klasörü: {result['output_dir']}\n")
                f.write(f"İşlenen PDF: {result['processed_pdf']}\n")
                f.write(f"Matematik Testi Çıkarıldı: {'Evet' if result.get('math_test_extracted', False) else 'Hayır'}\n")
                f.write(f"Soru Sayısı: {result['total_questions']}\n")
                f.write(f"Sol Taraf: {result['questions_by_side']['sol']}\n")
                f.write(f"Sağ Taraf: {result['questions_by_side']['sag']}\n")
            else:
                f.write(f"Hata: {result['error']}\n")
            f.write("-" * 50 + "\n")
    
    print(f"\n{'='*60}")
    print("TOPLU İŞLEM TAMAMLANDI")
    print(f"{'='*60}")
    print(f"Toplam PDF: {batch_report['total_files']}")
    print(f"Başarılı: {batch_report['processed_files']}")
    print(f"Başarısız: {batch_report['failed_files']}")
    print(f"Toplam Soru: {batch_report['total_questions']}")
    print(f"Süre: {batch_report['duration']:.2f} saniye")
    print(f"Rapor: {report_path}")
    
    return batch_report

# Tek PDF işleme fonksiyonu (eski main fonksiyonu)
def process_single_pdf():
    """Tek PDF dosyasını işler (eski main fonksiyonu)"""
    
    import glob
    pdf_files = glob.glob("*.pdf")
    
    # processed_sorular.pdf'yi hariç tut
    pdf_files = [f for f in pdf_files if f != "processed_sorular.pdf"]
    
    if not pdf_files:
        print("Dizinde PDF dosyası bulunamadı!")
        return None, None
    
    # İlk PDF dosyasını kullan
    pdf_path = pdf_files[0]
    print(f"PDF dosyası bulundu: {pdf_path}")
    
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

# Ana fonksiyon
def main():
    """Ana fonksiyon - çoklu PDF işleme"""
    return process_multiple_pdfs()

if __name__ == "__main__":
    result = main()
