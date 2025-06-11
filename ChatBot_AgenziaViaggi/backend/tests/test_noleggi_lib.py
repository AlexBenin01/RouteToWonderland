import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.noleggi_lib import NoleggiTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def noleggi_template(template_manager):
    template = NoleggiTemplate(template_manager)
    template.template_path = "template/noleggi.json"
    return template

def test_init(noleggi_template):
    """Test dell'inizializzazione della classe NoleggiTemplate"""
    assert noleggi_template.model_path is not None
    assert noleggi_template.model is not None
    assert noleggi_template.template_path == "template/noleggi.json"

def test_validate_tipo_cambio_success(noleggi_template):
    """Test della validazione del tipo di cambio con successo"""
    data = {"tipo_cambio": "manuale"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(noleggi_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.noleggi_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("manuale", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = noleggi_template.validate_tipo_cambio(data)
        assert is_valid
        assert "verificato" in msg.lower()
        assert result["tipo_cambio"] == "manuale"

def test_validate_tipo_cambio_missing_data(noleggi_template):
    """Test della validazione del tipo di cambio con dati mancanti"""
    data = {}
    is_valid, msg, result = noleggi_template.validate_tipo_cambio(data)
    assert is_valid
    assert "mancante" in msg.lower()
    assert result == {}

def test_validate_tipo_cambio_high_distance(noleggi_template):
    """Test della validazione del tipo di cambio con distanza elevata"""
    data = {"tipo_cambio": "invalid_cambio"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(noleggi_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.noleggi_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("manuale", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = noleggi_template.validate_tipo_cambio(data)
        assert not is_valid
        assert result["tipo_cambio"] is None

def test_validate_data_success(noleggi_template):
    """Test della validazione dei dati con successo"""
    data = {
        "posti_auto": 5,
        "tipo_cambio": "manuale"
    }
    
    with patch.object(noleggi_template, 'validate_tipo_cambio', return_value=(True, "Success", {"tipo_cambio": "manuale"})):
        is_valid, msg, result = noleggi_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result["posti_auto"] == 5
        assert result["tipo_cambio"] == "manuale"

def test_validate_data_invalid_posti_auto(noleggi_template):
    """Test della validazione dei dati con posti_auto non valido"""
    data = {
        "posti_auto": 1,  # Minimo 2 posti
        "tipo_cambio": "manuale"
    }
    
    is_valid, msg, result = noleggi_template.validate_data(data)
    assert not is_valid
    assert "intero" in msg.lower()

def test_validate_data_invalid_tipo_cambio(noleggi_template):
    """Test della validazione dei dati con tipo_cambio non valido"""
    data = {
        "posti_auto": 5,
        "tipo_cambio": "invalid"
    }
    
    with patch.object(noleggi_template, 'validate_tipo_cambio', return_value=(False, "Error", {"tipo_cambio": None})):
        is_valid, msg, result = noleggi_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(noleggi_template):
    """Test della verifica del template con successo"""
    data = {
        "posti_auto": 5,
        "tipo_cambio": "manuale"
    }
    
    with patch.object(noleggi_template, 'get_template_data', return_value={"posti_auto": None, "tipo_cambio": None}), \
         patch.object(noleggi_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = noleggi_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(noleggi_template):
    """Test della verifica del template con errore"""
    data = {
        "posti_auto": 1,
        "tipo_cambio": "invalid"
    }
    
    with patch.object(noleggi_template, 'get_template_data', return_value={"posti_auto": None, "tipo_cambio": None}), \
         patch.object(noleggi_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = noleggi_template.verifica_template(data)
        assert "test error" in errors[0].lower() 