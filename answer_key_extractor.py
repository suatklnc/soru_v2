#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cevap anahtarı çıkarma modülü
"""

import fitz  # PyMuPDF
import re
import json
import os
from typing import Dict, List, Tuple, Optional

class AnswerKeyExtractor:
    def __init__(self, pdf_path: str):
        """Cevap anahtarı PDF'ini yükle"""
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.answers = {}
        
    def extract_answers(self) -> Dict[str, Dict[str, str]]:
        """Cevap anahtarından cevapları çıkar"""
        try:
            print(f"Cevap anahtarı işleniyor: {self.pdf_path}")
            
            # Tüm sayfaları işle
            for page_num in range(len(self.doc)):
                page = self.doc[page_num]
                text = page.get_text()
                
                # Test başlıklarını bul
                test_titles = self._find_test_titles(text)
                
                for title in test_titles:
                    if title not in self.answers:
                        self.answers[title] = {}
                    
                    # Bu test için cevapları bul
                    answers = self._extract_answers_for_test(text, title)
                    self.answers[title].update(answers)
            
            print(f"Toplam {len(self.answers)} test bulundu")
            for test_name, answers in self.answers.items():
                print(f"  {test_name}: {len(answers)} soru")
            
            return self.answers
            
        except Exception as e:
            print(f"Cevap anahtarı çıkarılırken hata: {e}")
            return {}
    
    def _find_test_titles(self, text: str) -> List[str]:
        """Basit başlık bulma - sadece soru-cevap eşleştirmesi için"""
        # Başlık aramayı basitleştir - sadece "TEST" içeren başlıkları bul
        test_titles = []
        
        # Basit pattern ile başlık bul
        patterns = [
            r'[A-ZÇĞIİÖŞÜ][A-ZÇĞIİÖŞÜ\s]*TEST[İI]?',
            r'[A-ZÇĞIİÖŞÜ][A-ZÇĞIİÖŞÜ\s]+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clean_match = match.strip()
                if 3 < len(clean_match) < 50:
                    test_titles.append(clean_match)
        
        # Tekrarları kaldır ve en yaygın olanları seç
        unique_titles = list(set(test_titles))
        
        if unique_titles:
            # Matematik ile ilgili başlıkları öncelikle seç
            math_related = [title for title in unique_titles if any(keyword in title.upper() for keyword in ['MATEMAT', 'MATEMET', 'MATH'])]
            if math_related:
                return math_related[:3]  # En fazla 3 başlık
            else:
                return unique_titles[:3]  # En fazla 3 başlık
        
        return ['GENEL']  # Varsayılan başlık
    
    def _extract_answers_for_test(self, text: str, test_title: str) -> Dict[str, str]:
        """Belirli bir test için cevapları çıkar"""
        answers = {}
        
        try:
            # Tüm metinde soru numarası ve cevap eşleştirmesi yap
            pattern = r'(\d+)\.\s*([ABCDE])'
            matches = re.findall(pattern, text)
            
            # Her soru numarası için sadece ilk cevabı kaydet
            seen_questions = set()
            for question_num, answer in matches:
                if question_num not in seen_questions:
                    # 1-50 arası soruları al (daha geniş aralık)
                    if 1 <= int(question_num) <= 50:
                        answers[question_num] = answer
                        seen_questions.add(question_num)
            
            print(f"  {test_title}: {len(answers)} soru bulundu")
            
        except Exception as e:
            print(f"Test {test_title} için cevap çıkarılırken hata: {e}")
        
        return answers
    
    def save_answers(self, output_json_path: str):
        """Cevapları JSON dosyasına kaydet"""
        try:
            os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
            
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.answers, f, ensure_ascii=False, indent=2)
            
            print(f"Cevaplar kaydedildi: {output_json_path}")
            
        except Exception as e:
            print(f"Cevaplar kaydedilirken hata: {e}")
    
    def close(self):
        """PDF dosyasını kapat"""
        if hasattr(self, 'doc'):
            self.doc.close()

def process_answer_key_pdfs(output_dir: str = "output") -> Dict[str, str]:
    """Output klasöründeki cevap anahtarı PDF'lerini işle"""
    answer_key_files = {}
    
    try:
        # Output klasöründeki tüm alt klasörleri tara
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.pdf') and ('cevap' in file.lower() or 'anahtar' in file.lower()):
                    pdf_path = os.path.join(root, file)
                    
                    # Ana PDF adını çıkar (klasör adından)
                    folder_name = os.path.basename(root)
                    
                    print(f"Cevap anahtarı bulundu: {pdf_path}")
                    print(f"Ana PDF: {folder_name}")
                    
                    # Cevap anahtarını işle
                    extractor = AnswerKeyExtractor(pdf_path)
                    answers = extractor.extract_answers()
                    
                    if answers:
                        # JSON dosyasına kaydet
                        json_path = os.path.join(root, f"{folder_name}_answers.json")
                        extractor.save_answers(json_path)
                        answer_key_files[folder_name] = json_path
                    
                    extractor.close()
        
        return answer_key_files
        
    except Exception as e:
        print(f"Cevap anahtarı PDF'leri işlenirken hata: {e}")
        return {}

if __name__ == "__main__":
    # Test
    answer_key_files = process_answer_key_pdfs()
    print(f"İşlenen cevap anahtarı dosyaları: {answer_key_files}")
