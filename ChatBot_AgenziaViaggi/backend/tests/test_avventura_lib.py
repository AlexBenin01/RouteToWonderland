import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.avventura_lib import AvventuraTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def avventura_template(template_manager):
    template = AvventuraTemplate(template_manager)
    template.template_path = "template/avventura.json"  # Aggiungo il template_path
    return template

def test_init(avventura_template):
    """Test dell'inizializzazione della classe AvventuraTemplate"""
    assert avventura_template.model_path is not None
    assert avventura_template.model is not None
    assert avventura_template.template_path == "template/avventura.json"

def test_load_template(avventura_template):
    """Test del caricamento del template"""
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        result = avventura_template._load_template()
        assert result == {"test": "data"}

def test_load_template_file_not_found(avventura_template):
    """Test del caricamento del template quando il file non esiste"""
    with patch('builtins.open', side_effect=FileNotFoundError) as mock_open:
        mock_open.side_effect = [FileNotFoundError, MagicMock()]
        mock_open.return_value.__enter__.return_value.read.return_value = '{"default": "data"}'
        result = avventura_template._load_template()
        assert result == {"default": "data"}

def test_set_template(avventura_template):
    """Test del cambio di template"""
    with patch.object(avventura_template, '_load_template') as mock_load:
        mock_load.return_value = {"new": "template"}
        avventura_template.set_template("nuovo_template")
        assert avventura_template.template_name == "nuovo_template"
        assert avventura_template.template_path == "template/nuovo_template.json"
        assert avventura_template.template_data == {"new": "template"}

def test_validate_difficolta_success(avventura_template):
    """Test della validazione del livello di difficoltà con successo"""
    data = {"livello_difficolta": "facile"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(avventura_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.avventura_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("facile", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = avventura_template.validate_difficolta(data)
        assert is_valid
        assert "verificato" in msg.lower()
        assert result["livello_difficolta"] == "facile"

def test_validate_difficolta_missing_data(avventura_template):
    """Test della validazione del livello di difficoltà con dati mancanti"""
    data = {}
    is_valid, msg, result = avventura_template.validate_difficolta(data)
    assert is_valid
    assert "mancante" in msg.lower()
    assert result["livello_difficolta"] == []

def test_validate_difficolta_high_distance(avventura_template):
    """Test della validazione del livello di difficoltà con distanza elevata"""
    data = {"livello_difficolta": "invalid_level"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(avventura_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.avventura_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("facile", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = avventura_template.validate_difficolta(data)
        assert is_valid
        assert result["livello_difficolta"] is None

def test_validate_lingua_success(avventura_template):
    """Test della validazione della lingua guida con successo"""
    data = {"lingua_guida": "italiano"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(avventura_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.avventura_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("italiano", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = avventura_template.validate_lingua(data)
        assert is_valid
        assert "verificata" in msg.lower()
        assert result["lingua_guida"] == "italiano"
        assert result["guida_esperta"] is True
        assert result["guida_menzionata"] is True

def test_validate_lingua_missing_data(avventura_template):
    """Test della validazione della lingua guida con dati mancanti"""
    data = {}
    is_valid, msg, result = avventura_template.validate_lingua(data)
    assert is_valid
    assert "mancante" in msg.lower()

def test_validate_lingua_high_distance(avventura_template):
    """Test della validazione della lingua guida con distanza elevata"""
    data = {"lingua_guida": "invalid_language"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(avventura_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.avventura_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("italiano", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = avventura_template.validate_lingua(data)
        assert is_valid
        assert result["lingua_guida"] is None

def test_validate_attivita_success(avventura_template):
    """Test della validazione delle attività con successo"""
    data = {"attivita": ["rafting", "arrampicata"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(avventura_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.avventura_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("rafting", 0.2), ("arrampicata", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = avventura_template.validate_attivita(data)
        assert is_valid
        assert "verificate" in msg.lower()
        assert len(result["attivita"]) == 2

def test_validate_attivita_missing_data(avventura_template):
    """Test della validazione delle attività con dati mancanti"""
    data = {}
    is_valid, msg, result = avventura_template.validate_attivita(data)
    assert is_valid
    assert "opzionali" in msg.lower()

def test_validate_attivita_high_distance(avventura_template):
    """Test della validazione delle attività con distanza elevata"""
    data = {"attivita": ["invalid_activity"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(avventura_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.avventura_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("rafting", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = avventura_template.validate_attivita(data)
        assert is_valid
        assert result["attivita"] == []

def test_validate_data_success(avventura_template):
    """Test della validazione dei dati con successo"""
    data = {
        "livello_difficolta": "facile",
        "lingua_guida": "italiano",
        "attivita": ["rafting"]
    }
    
    with patch.object(avventura_template, 'validate_difficolta', return_value=(True, "Success", {"livello_difficolta": "facile"})), \
         patch.object(avventura_template, 'validate_lingua', return_value=(True, "Success", {"lingua_guida": "italiano", "guida_esperta": True, "guida_menzionata": True})), \
         patch.object(avventura_template, 'validate_attivita', return_value=(True, "Success", {"attivita": ["rafting"]})):
        is_valid, msg, result = avventura_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()

def test_validate_data_failure(avventura_template):
    """Test della validazione dei dati con fallimento"""
    data = {
        "livello_difficolta": "invalid",
        "lingua_guida": "invalid",
        "attivita": ["invalid"]
    }
    
    with patch.object(avventura_template, 'validate_difficolta', return_value=(False, "Error", {"livello_difficolta": None})), \
         patch.object(avventura_template, 'validate_lingua', return_value=(False, "Error", {"lingua_guida": None})), \
         patch.object(avventura_template, 'validate_attivita', return_value=(False, "Error", {"attivita": []})):
        is_valid, msg, result = avventura_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(avventura_template):
    """Test della verifica del template con successo"""
    data = {
        "livello_difficolta": "facile",
        "lingua_guida": "italiano",
        "attivita": ["rafting"]
    }
    
    with patch.object(avventura_template, 'get_template_data', return_value={"livello_difficolta": None, "lingua_guida": None, "attivita": None}), \
         patch.object(avventura_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = avventura_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(avventura_template):
    """Test della verifica del template con errore"""
    data = {
        "livello_difficolta": "invalid",
        "lingua_guida": "invalid",
        "attivita": ["invalid"]
    }
    
    with patch.object(avventura_template, 'get_template_data', return_value={"livello_difficolta": None, "lingua_guida": None, "attivita": None}), \
         patch.object(avventura_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = avventura_template.verifica_template(data)
        assert "test error" in errors[0].lower() 