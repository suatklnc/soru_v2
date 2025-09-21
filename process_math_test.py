#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from question_extractor import QuestionExtractor

# Çıkarılan matematik testini işle
pdf_path = "InternetKitapcigi29032018_matematik_testi.pdf"
output_dir = "output/InternetKitapcigi29032018_matematik"

print(f"🔍 Matematik testi işleniyor: {pdf_path}")

extractor = QuestionExtractor(pdf_path)
extractor.preprocess_pdf()
questions = extractor.extract_all_questions(output_dir)
stats = extractor.get_question_statistics()

print(f"✅ İşlem tamamlandı!")
print(f"📊 Toplam soru: {stats['total_questions']}")
print(f"📄 Sol taraf: {stats['questions_by_side']['sol']}")
print(f"📄 Sağ taraf: {stats['questions_by_side']['sag']}")

extractor.save_question_list(f"{output_dir}/question_list.txt")
extractor.doc.close()
if hasattr(extractor, 'processed_doc') and extractor.processed_doc:
    extractor.processed_doc.close()
