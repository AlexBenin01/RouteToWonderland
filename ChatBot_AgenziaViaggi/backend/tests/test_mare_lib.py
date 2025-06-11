import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.mare_lib import MareTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def mare_template(template_manager):
    template = MareTemplate(template_manager)
    template.template_path = "template/mare.json"  # Aggiungo il template_path
    return template

def test_init(mare_template):
    """Test dell'inizializzazione della classe MareTemplate"""
    assert mare_template.model_path is not None
    assert mare_template.model is not None
    assert mare_template.template_path == "template/mare.json"

def test_load_template(mare_template):
    """Test del caricamento del template"""
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        result = mare_template._load_template()
        assert result == {"test": "data"}

def test_load_template_file_not_found(mare_template):
    """Test del caricamento del template quando il file non esiste"""
    with patch('builtins.open', side_effect=FileNotFoundError) as mock_open:
        mock_open.side_effect = [FileNotFoundError, MagicMock()]
        mock_open.return_value.__enter__.return_value.read.return_value = '{"default": "data"}'
        result = mare_template._load_template()
        assert result == {"default": "data"}

def test_set_template(mare_template):
    """Test del cambio di template"""
    with patch.object(mare_template, '_load_template') as mock_load:
        mock_load.return_value = {"new": "template"}
        mare_template.set_template("nuovo_template")
        assert mare_template.template_name == "nuovo_template"
        assert mare_template.template_path == "template/nuovo_template.json"
        assert mare_template.template_data == {"new": "template"}

def test_validate_attivita_success(mare_template):
    """Test della validazione delle attività con successo"""
    data = {"attivita": ["nuoto", "snorkeling"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(mare_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.mare_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("nuoto", 0.2), ("snorkeling", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = mare_template.validate_attivita(data)
        assert is_valid
        assert "verificate" in msg.lower()
        assert len(result["attivita"]) == 2

def test_validate_attivita_missing_data(mare_template):
    """Test della validazione delle attività con dati mancanti"""
    data = {}
    is_valid, msg, result = mare_template.validate_attivita(data)
    assert is_valid
    assert "opzionali" in msg.lower()

def test_validate_attivita_high_distance(mare_template):
    """Test della validazione delle attività con distanza elevata"""
    data = {"attivita": ["invalid_activity"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(mare_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.mare_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("nuoto", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = mare_template.validate_attivita(data)
        assert is_valid
        assert result["attivita"] is None

def test_validate_data_success(mare_template):
    """Test della validazione dei dati con successo"""
    data = {
        "attivita": ["nuoto"],
        "attrezzatura": True,
        "attrezzatura_menzionata": True
    }
    
    with patch.object(mare_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["nuoto"]})):
        is_valid, msg, result = mare_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result["attivita"] == ["nuoto"]
        assert result["attrezzatura"] is True
        assert result["attrezzatura_menzionata"] is True

def test_validate_data_attrezzatura_sync(mare_template):
    """Test della sincronizzazione tra attrezzatura e attrezzatura_menzionata"""
    data = {
        "attivita": ["nuoto"],
        "attrezzatura": True
    }
    
    with patch.object(mare_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["nuoto"]})):
        is_valid, msg, result = mare_template.validate_data(data)
        assert is_valid
        assert result["attrezzatura"] is True
        assert result["attrezzatura_menzionata"] is True

def test_validate_data_attrezzatura_menzionata_sync(mare_template):
    """Test della sincronizzazione tra attrezzatura_menzionata e attrezzatura"""
    data = {
        "attivita": ["nuoto"],
        "attrezzatura_menzionata": True
    }
    
    with patch.object(mare_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["nuoto"]})):
        is_valid, msg, result = mare_template.validate_data(data)
        assert is_valid
        assert result["attrezzatura"] is True
        assert result["attrezzatura_menzionata"] is True

def test_validate_data_failure(mare_template):
    """Test della validazione dei dati con fallimento"""
    data = {"attivita": ["invalid"]}
    
    with patch.object(mare_template, 'validate_attivita', return_value=(False, "Error", {"attivita": None})):
        is_valid, msg, result = mare_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(mare_template):
    """Test della verifica del template con successo"""
    data = {
        "attivita": ["nuoto"],
        "attrezzatura": True,
        "attrezzatura_menzionata": True
    }
    
    with patch.object(mare_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(mare_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = mare_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(mare_template):
    """Test della verifica del template con errore"""
    data = {
        "attivita": ["invalid"],
        "attrezzatura": True,
        "attrezzatura_menzionata": True
    }
    
    with patch.object(mare_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(mare_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = mare_template.verifica_template(data)
        assert "test error" in errors[0].lower() 