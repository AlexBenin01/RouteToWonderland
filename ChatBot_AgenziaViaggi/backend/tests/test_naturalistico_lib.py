import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.naturalistico_lib import NaturalisticoTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def naturalistico_template(template_manager):
    template = NaturalisticoTemplate(template_manager)
    template.template_path = "template/naturalistico.json"  # Aggiungo il template_path
    return template

def test_init(naturalistico_template):
    """Test dell'inizializzazione della classe NaturalisticoTemplate"""
    assert naturalistico_template.model_path is not None
    assert naturalistico_template.model is not None
    assert naturalistico_template.template_path == "template/naturalistico.json"

def test_load_template(naturalistico_template):
    """Test del caricamento del template"""
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        result = naturalistico_template._load_template()
        assert result == {"test": "data"}

def test_load_template_file_not_found(naturalistico_template):
    """Test del caricamento del template quando il file non esiste"""
    with patch('builtins.open', side_effect=FileNotFoundError) as mock_open:
        mock_open.side_effect = [FileNotFoundError, MagicMock()]
        mock_open.return_value.__enter__.return_value.read.return_value = '{"default": "data"}'
        result = naturalistico_template._load_template()
        assert result == {"default": "data"}

def test_set_template(naturalistico_template):
    """Test del cambio di template"""
    with patch.object(naturalistico_template, '_load_template') as mock_load:
        mock_load.return_value = {"new": "template"}
        naturalistico_template.set_template("nuovo_template")
        assert naturalistico_template.template_name == "nuovo_template"
        assert naturalistico_template.template_path == "template/nuovo_template.json"
        assert naturalistico_template.template_data == {"new": "template"}

def test_validate_attivita_success(naturalistico_template):
    """Test della validazione delle attività con successo"""
    data = {"attivita": ["escursione", "birdwatching"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(naturalistico_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.naturalistico_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("escursione", 0.2), ("birdwatching", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = naturalistico_template.validate_attivita(data)
        assert is_valid
        assert "verificate" in msg.lower()
        assert len(result["attivita"]) == 2

def test_validate_attivita_missing_data(naturalistico_template):
    """Test della validazione delle attività con dati mancanti"""
    data = {}
    is_valid, msg, result = naturalistico_template.validate_attivita(data)
    assert is_valid
    assert "opzionali" in msg.lower()

def test_validate_attivita_high_distance(naturalistico_template):
    """Test della validazione delle attività con distanza elevata"""
    data = {"attivita": ["invalid_activity"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(naturalistico_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.naturalistico_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("escursione", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = naturalistico_template.validate_attivita(data)
        assert is_valid
        assert result["attivita"] is None

def test_validate_lingua_success(naturalistico_template):
    """Test della validazione della lingua con successo"""
    data = {"lingua_guida": "italiano"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(naturalistico_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.naturalistico_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("italiano", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = naturalistico_template.validate_lingua(data)
        assert is_valid
        assert "verificata" in msg.lower()
        assert result["lingua_guida"] == "italiano"
        assert result["guida_esperta"] is True
        assert result["guida_menzionata"] is True

def test_validate_lingua_high_distance(naturalistico_template):
    """Test della validazione della lingua con distanza elevata"""
    data = {"lingua_guida": "invalid_language"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(naturalistico_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.naturalistico_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("italiano", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = naturalistico_template.validate_lingua(data)
        assert is_valid
        assert result["lingua_guida"] is None

def test_validate_data_success(naturalistico_template):
    """Test della validazione dei dati con successo"""
    data = {
        "attivita": ["escursione"],
        "guida_menzionata": True,
        "guida_esperta": True,
        "lingua_guida": "italiano"
    }
    
    with patch.object(naturalistico_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["escursione"]})), \
         patch.object(naturalistico_template, 'validate_lingua', return_value=(True, "Success", {"lingua_guida": "italiano", "guida_esperta": True, "guida_menzionata": True})):
        is_valid, msg, result = naturalistico_template.validate_data(data)
        assert is_valid
        assert result["attivita"] == ["escursione"]
        assert result["guida_menzionata"] is True
        assert result["guida_esperta"] is True
        assert result["lingua_guida"] == "italiano"

def test_validate_data_guida_sync(naturalistico_template):
    """Test della sincronizzazione tra guida_menzionata e guida_esperta"""
    data = {
        "attivita": ["escursione"],
        "guida_menzionata": True
    }
    
    with patch.object(naturalistico_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["escursione"]})):
        is_valid, msg, result = naturalistico_template.validate_data(data)
        assert is_valid
        assert result["guida_menzionata"] is True
        assert result["guida_esperta"] is True

def test_validate_data_failure(naturalistico_template):
    """Test della validazione dei dati con fallimento"""
    data = {"attivita": ["invalid"]}
    
    with patch.object(naturalistico_template, 'validate_attivita', return_value=(False, "Error", {"attivita": None})):
        is_valid, msg, result = naturalistico_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(naturalistico_template):
    """Test della verifica del template con successo"""
    data = {
        "attivita": ["escursione"],
        "guida_menzionata": True,
        "guida_esperta": True,
        "lingua_guida": "italiano"
    }
    
    with patch.object(naturalistico_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(naturalistico_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = naturalistico_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(naturalistico_template):
    """Test della verifica del template con errore"""
    data = {
        "attivita": ["invalid"],
        "guida_menzionata": True,
        "guida_esperta": True,
        "lingua_guida": "italiano"
    }
    
    with patch.object(naturalistico_template, 'get_template_data', return_value={"attivita": None}), \
         patch.object(naturalistico_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = naturalistico_template.verifica_template(data)
        assert "test error" in errors[0].lower() 