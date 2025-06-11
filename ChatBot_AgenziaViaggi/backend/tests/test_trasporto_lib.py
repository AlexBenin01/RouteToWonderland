import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.trasporto_lib import TrasportoTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def trasporto_template(template_manager):
    template = TrasportoTemplate(template_manager)
    template.template_path = "template/trasporto.json"
    return template

def test_init(trasporto_template):
    """Test dell'inizializzazione della classe TrasportoTemplate"""
    assert trasporto_template.model_path is not None
    assert trasporto_template.model is not None
    assert trasporto_template.template_path == "template/trasporto.json"

def test_verifica_tipo_veicolo_success(trasporto_template):
    """Test della verifica del tipo di veicolo con successo"""
    data = {"tipo_veicolo": "autobus"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(trasporto_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.trasporto_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("autobus", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = trasporto_template.verifica_tipo_veicolo(data)
        assert is_valid
        assert "verificato" in msg.lower()
        assert result["tipo_veicolo"] == "autobus"

def test_verifica_tipo_veicolo_missing_data(trasporto_template):
    """Test della verifica del tipo di veicolo con dati mancanti"""
    data = {}
    is_valid, msg, result = trasporto_template.verifica_tipo_veicolo(data)
    assert is_valid
    assert "mancante" in msg.lower()
    assert result["tipo_veicolo"] is None

def test_verifica_tipo_veicolo_high_distance(trasporto_template):
    """Test della verifica del tipo di veicolo con distanza elevata"""
    data = {"tipo_veicolo": "invalid_vehicle"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(trasporto_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.trasporto_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("autobus", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = trasporto_template.verifica_tipo_veicolo(data)
        assert is_valid
        assert result["tipo_veicolo"] is None

def test_verifica_luogo_success(trasporto_template):
    """Test della verifica del luogo di partenza con successo"""
    data = {"luogo_partenza": "Roma"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(trasporto_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.trasporto_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("Roma", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = trasporto_template.verifica_luogo(data)
        assert is_valid
        assert "verificato" in msg.lower()
        assert result["luogo_partenza"] == "Roma"

def test_verifica_luogo_missing_data(trasporto_template):
    """Test della verifica del luogo di partenza con dati mancanti"""
    data = {}
    is_valid, msg, result = trasporto_template.verifica_luogo(data)
    assert is_valid
    assert "mancante" in msg.lower()
    assert result["luogo_partenza"] is None

def test_verifica_luogo_high_distance(trasporto_template):
    """Test della verifica del luogo di partenza con distanza elevata"""
    data = {"luogo_partenza": "invalid_place"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(trasporto_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.trasporto_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("Roma", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = trasporto_template.verifica_luogo(data)
        assert is_valid
        assert result["luogo_partenza"] is None

def test_validate_data_success(trasporto_template):
    """Test della validazione dei dati con successo"""
    data = {
        "tipo_veicolo": "autobus",
        "luogo_partenza": "Roma"
    }
    
    with patch.object(trasporto_template, 'verifica_tipo_veicolo', return_value=(True, "Success", {"tipo_veicolo": "autobus"})), \
         patch.object(trasporto_template, 'verifica_luogo', return_value=(True, "Success", {"luogo_partenza": "Roma"})):
        is_valid, msg, result = trasporto_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result["tipo_veicolo"] == "autobus"
        assert result["luogo_partenza"] == "Roma"

def test_validate_data_failure(trasporto_template):
    """Test della validazione dei dati con fallimento"""
    data = {
        "tipo_veicolo": "invalid",
        "luogo_partenza": "invalid"
    }
    
    with patch.object(trasporto_template, 'verifica_tipo_veicolo', return_value=(False, "Error", {"tipo_veicolo": None})), \
         patch.object(trasporto_template, 'verifica_luogo', return_value=(False, "Error", {"luogo_partenza": None})):
        is_valid, msg, result = trasporto_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(trasporto_template):
    """Test della verifica del template con successo"""
    data = {
        "tipo_veicolo": "autobus",
        "luogo_partenza": "Roma"
    }
    
    with patch.object(trasporto_template, 'get_template_data', return_value={"tipo_veicolo": None, "luogo_partenza": None}), \
         patch.object(trasporto_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = trasporto_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(trasporto_template):
    """Test della verifica del template con errore"""
    data = {
        "tipo_veicolo": "invalid",
        "luogo_partenza": "invalid"
    }
    
    with patch.object(trasporto_template, 'get_template_data', return_value={"tipo_veicolo": None, "luogo_partenza": None}), \
         patch.object(trasporto_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = trasporto_template.verifica_template(data)
        assert "test error" in errors[0].lower() 