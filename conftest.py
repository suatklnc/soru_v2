"""
Pytest configuration and fixtures for question extractor tests
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_pdf_document():
    """Create a mock PDF document for testing"""
    mock_doc = Mock()
    mock_page = Mock()
    mock_doc.load_page.return_value = mock_page
    mock_doc.__len__.return_value = 1
    return mock_doc, mock_page


@pytest.fixture
def sample_question_text():
    """Sample question text for testing"""
    return """
    1. Bir sayının 2 katı 8 ise, bu sayı kaçtır?
    A) 2
    B) 4
    C) 6
    D) 8
    E) 10
    
    2. 5 + 3 = ?
    A) 7
    B) 8
    C) 9
    D) 10
    E) 11
    """


@pytest.fixture
def sample_instruction_text():
    """Sample instruction text for testing"""
    return """
    Bu testte 40 soru vardır.
    Cevaplarınızı, cevap kâğıdının Temel Matematik bölümüne işaretleyiniz.
    Test süresi 75 dakikadır.
    Sınav başlamadan önce kitapçığın içindeki sayfaların eksik olup olmadığını kontrol ediniz.
    """
