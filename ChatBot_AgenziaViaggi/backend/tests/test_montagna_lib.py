import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.montagna_lib import MontagnaTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def montagna_template(template_manager):
    template = MontagnaTemplate(template_manager)
    template.template_path = "template/montagna.json"  # Aggiungo il template_path
    return template

def test_init(montagna_template):
    """Test dell'inizializzazione della classe MontagnaTemplate"""
    assert montagna_template.model_path is not None
    assert montagna_template.model is not None
    assert montagna_template.template_path == "template/montagna.json"

def test_load_template(montagna_template):
    """Test del caricamento del template"""
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        result = montagna_template._load_template()
        assert result == {"test": "data"}

def test_load_template_file_not_found(montagna_template):
    """Test del caricamento del template quando il file non esiste"""
    with patch('builtins.open', side_effect=FileNotFoundError) as mock_open:
        mock_open.side_effect = [FileNotFoundError, MagicMock()]
        mock_open.return_value.__enter__.return_value.read.return_value = '{"default": "data"}'
        result = montagna_template._load_template()
        assert result == {"default": "data"}

def test_set_template(montagna_template):
    """Test del cambio di template"""
    with patch.object(montagna_template, '_load_template') as mock_load:
        mock_load.return_value = {"new": "template"}
        montagna_template.set_template("nuovo_template")
        assert montagna_template.template_name == "nuovo_template"
        assert montagna_template.template_path == "template/nuovo_template.json"
        assert montagna_template.template_data == {"new": "template"}

def test_validate_attivita_montagna_success(montagna_template):
    """Test della validazione delle attività con successo"""
    data = {"attivita": ["sci", "snowboard"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(montagna_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.montagna_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("sci", 0.2), ("snowboard", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = montagna_template.validate_attivita_montagna(data)
        assert is_valid
        assert "verificate" in msg.lower()
        assert len(result["attivita"]) == 2

def test_validate_attivita_montagna_missing_data(montagna_template):
    """Test della validazione delle attività con dati mancanti"""
    data = {}
    is_valid, msg, result = montagna_template.validate_attivita_montagna(data)
    assert is_valid
    assert "opzionali" in msg.lower()

def test_validate_attivita_montagna_high_distance(montagna_template):
    """Test della validazione delle attività con distanza elevata"""
    data = {"attivita": ["invalid_activity"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(montagna_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.montagna_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("sci", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = montagna_template.validate_attivita_montagna(data)
        assert is_valid
        assert result["attivita"] is None

def test_validate_data_success(montagna_template):
    """Test della validazione dei dati con successo"""
    data = {
        "attivita": ["sci"],
        "attrezzatura": True,
        "attrezzatura_menzionata": True
    }
    
    with patch.object(montagna_template, 'validate_attivita_montagna', return_value=(True, "Success", {"attivita": ["sci"]})):
        is_valid, msg, result = montagna_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result["attivita"] == ["sci"]
        assert result["attrezzatura"] is True
        assert result["attrezzatura_menzionata"] is True

def test_validate_data_attrezzatura_sync(montagna_template):
    """Test della sincronizzazione tra attrezzatura e attrezzatura_menzionata"""
    data = {
        "attivita": ["sci"],
        "attrezzatura": True
    }
    
    with patch.object(montagna_template, 'validate_attivita_montagna', return_value=(True, "Success", {"attivita": ["sci"]})):
        is_valid, msg, result = montagna_template.validate_data(data)
        assert is_valid
        assert result["attrezzatura"] is True
        assert result["attrezzatura_menzionata"] is True

def test_validate_data_attrezzatura_menzionata_sync(montagna_template):
    """Test della sincronizzazione tra attrezzatura_menzionata e attrezzatura"""
    data = {
        "attivita": ["sci"],
        "attrezzatura_menzionata": True
    }
    
    with patch.object(montagna_template, 'validate_attivita_montagna', return_value=(True, "Success", {"attivita": ["sci"]})):
        is_valid, msg, result = montagna_template.validate_data(data)
        assert is_valid
        assert result["attrezzatura"] is True
        assert result["attrezzatura_menzionata"] is True

def test_validate_data_failure(montagna_template):
    """Test della validazione dei dati con fallimento"""
    data = {"attivita": ["invalid"]}
    
    with patch.object(montagna_template, 'validate_attivita_montagna', return_value=(False, "Error", {"attivita": None})):
        is_valid, msg, result = montagna_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(montagna_template):
    """Test della verifica del template con successo"""
    data = {
        "attivita": ["sci"],
        "attrezzatura": True,
        "attrezzatura_menzionata": True
    }
    
    with patch.object(montagna_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(montagna_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = montagna_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(montagna_template):
    """Test della verifica del template con errore"""
    data = {
        "attivita": ["invalid"],
        "attrezzatura": True,
        "attrezzatura_menzionata": True
    }
    
    with patch.object(montagna_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(montagna_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = montagna_template.verifica_template(data)
        assert "test error" in errors[0].lower() 