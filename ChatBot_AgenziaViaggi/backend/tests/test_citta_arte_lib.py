import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.citta_arte_lib import CittaArteTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def citta_arte_template(template_manager):
    template = CittaArteTemplate(template_manager)
    template.template_path = "template/citta_arte.json"  # Aggiungo il template_path
    return template

def test_init(citta_arte_template):
    """Test dell'inizializzazione della classe CittaArteTemplate"""
    assert citta_arte_template.model_path is not None
    assert citta_arte_template.model is not None
    assert citta_arte_template.template_path == "template/citta_arte.json"

def test_validate_attivita_success(citta_arte_template):
    """Test della validazione delle attività con successo"""
    data = {"attivita": ["museo", "galleria"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(citta_arte_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.citta_arte_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("museo", 0.2), ("galleria", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = citta_arte_template.validate_attivita(data)
        assert is_valid
        assert "verificate" in msg.lower()
        assert len(result["attivita"]) == 2

def test_validate_attivita_missing_data(citta_arte_template):
    """Test della validazione delle attività con dati mancanti"""
    data = {}
    is_valid, msg, result = citta_arte_template.validate_attivita(data)
    assert is_valid
    assert "opzionali" in msg.lower()

def test_validate_attivita_high_distance(citta_arte_template):
    """Test della validazione delle attività con distanza elevata"""
    data = {"attivita": ["invalid_activity"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(citta_arte_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.citta_arte_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("museo", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = citta_arte_template.validate_attivita(data)
        assert is_valid
        assert result["attivita"] is None

def test_validate_lingua_success(citta_arte_template):
    """Test della validazione della lingua con successo"""
    data = {"lingua_guida": "italiano"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(citta_arte_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.citta_arte_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("italiano", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = citta_arte_template.validate_lingua(data)
        assert is_valid
        assert "verificata" in msg.lower()
        assert result["lingua_guida"] == "italiano"
        assert result["guida_turistica"] is True
        assert result["guida_menzionata"] is True

def test_validate_lingua_missing_data(citta_arte_template):
    """Test della validazione della lingua con dati mancanti"""
    data = {}
    is_valid, msg, result = citta_arte_template.validate_lingua(data)
    assert is_valid
    assert "mancante" in msg.lower()

def test_validate_lingua_high_distance(citta_arte_template):
    """Test della validazione della lingua con distanza elevata"""
    data = {"lingua_guida": "invalid_language"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(citta_arte_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.citta_arte_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("italiano", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = citta_arte_template.validate_lingua(data)
        assert is_valid
        assert result["lingua_guida"] is None

def test_validate_data_success(citta_arte_template):
    """Test della validazione dei dati con successo"""
    data = {
        "attivita": ["museo"],
        "guida_menzionata": True,
        "guida_turistica": True,
        "lingua_guida": "italiano"
    }
    
    with patch.object(citta_arte_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["museo"]})), \
         patch.object(citta_arte_template, 'validate_lingua', return_value=(True, "Success", {"lingua_guida": "italiano"})):
        is_valid, msg, result = citta_arte_template.validate_data(data)
        assert is_valid
        assert result["attivita"] == ["museo"]
        assert result["lingua_guida"] == "italiano"
        assert result["guida_turistica"] is True
        assert result["guida_menzionata"] is True

def test_validate_data_no_guide(citta_arte_template):
    """Test della validazione dei dati senza guida"""
    data = {
        "attivita": ["museo"],
        "guida_menzionata": False,
        "guida_turistica": False
    }
    
    with patch.object(citta_arte_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["museo"]})):
        is_valid, msg, result = citta_arte_template.validate_data(data)
        assert is_valid
        assert result["attivita"] == ["museo"]
        assert result["guida_turistica"] is False
        assert result["guida_menzionata"] is False
        assert result["lingua_guida"] == "no guida"

def test_validate_data_guide_mentioned_none(citta_arte_template):
    """Test della validazione dei dati con guida_menzionata None"""
    data = {
        "attivita": ["museo"],
        "guida_menzionata": None
    }
    
    with patch.object(citta_arte_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["museo"]})):
        is_valid, msg, result = citta_arte_template.validate_data(data)
        assert is_valid
        assert result["attivita"] == ["museo"]
        assert result["guida_turistica"] is None
        assert result["guida_menzionata"] is None
        assert result["lingua_guida"] is None

def test_verifica_template_success(citta_arte_template):
    """Test della verifica del template con successo"""
    data = {
        "attivita": ["museo"],
        "guida_menzionata": True,
        "guida_turistica": True,
        "lingua_guida": "italiano"
    }
    
    with patch.object(citta_arte_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(citta_arte_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = citta_arte_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(citta_arte_template):
    """Test della verifica del template con errore"""
    data = {
        "attivita": ["invalid"],
        "guida_menzionata": True,
        "guida_turistica": True,
        "lingua_guida": "invalid"
    }
    
    with patch.object(citta_arte_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(citta_arte_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = citta_arte_template.verifica_template(data)
        assert "test error" in errors[0].lower() 