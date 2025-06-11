import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.alloggi_lib import AlloggiTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def alloggi_template(template_manager):
    template = AlloggiTemplate(template_manager)
    template.template_path = "template/alloggi.json"  # Aggiungo il template_path
    return template

def test_init(alloggi_template):
    """Test dell'inizializzazione della classe AlloggiTemplate"""
    assert alloggi_template.model_path is not None
    assert alloggi_template.model is not None
    assert alloggi_template.template_path == "template/alloggi.json"

def test_load_template(alloggi_template):
    """Test del caricamento del template"""
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        result = alloggi_template._load_template()
        assert result == {"test": "data"}

def test_load_template_file_not_found(alloggi_template):
    """Test del caricamento del template quando il file non esiste"""
    with patch('builtins.open', side_effect=FileNotFoundError) as mock_open:
        mock_open.side_effect = [FileNotFoundError, MagicMock()]
        mock_open.return_value.__enter__.return_value.read.return_value = '{"default": "data"}'
        result = alloggi_template._load_template()
        assert result == {"default": "data"}

def test_set_template(alloggi_template):
    """Test del cambio di template"""
    with patch.object(alloggi_template, '_load_template') as mock_load:
        mock_load.return_value = {"new": "template"}
        alloggi_template.set_template("nuovo_template")
        assert alloggi_template.template_name == "nuovo_template"
        assert alloggi_template.template_path == "template/nuovo_template.json"
        assert alloggi_template.template_data == {"new": "template"}

def test_validate_alloggio_success(alloggi_template):
    """Test della validazione del tipo di alloggio con successo"""
    data = {"tipo_alloggio": "hotel"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(alloggi_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.alloggi_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("hotel", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = alloggi_template.validate_alloggio(data)
        assert is_valid
        assert "verificato" in msg.lower()
        assert result["tipo_alloggio"] == "hotel"

def test_validate_alloggio_missing_data(alloggi_template):
    """Test della validazione del tipo di alloggio con dati mancanti"""
    data = {}
    is_valid, msg, result = alloggi_template.validate_alloggio(data)
    assert not is_valid
    assert "obbligatorio" in msg.lower()

def test_validate_alloggio_high_distance(alloggi_template):
    """Test della validazione del tipo di alloggio con distanza elevata"""
    data = {"tipo_alloggio": "invalid_type"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(alloggi_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.alloggi_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("hotel", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = alloggi_template.validate_alloggio(data)
        assert not is_valid
        assert result["tipo_alloggio"] is None

def test_validate_alloggio_no_results(alloggi_template):
    """Test della validazione del tipo di alloggio senza risultati"""
    data = {"tipo_alloggio": "invalid_type"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(alloggi_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.alloggi_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = alloggi_template.validate_alloggio(data)
        assert not is_valid
        assert result["tipo_alloggio"] is None

def test_validate_data_success(alloggi_template):
    """Test della validazione dei dati con successo"""
    data = {"tipo_alloggio": "hotel"}
    
    with patch.object(alloggi_template, 'validate_alloggio', return_value=(True, "Success", data)):
        is_valid, msg, result = alloggi_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result == data

def test_validate_data_failure(alloggi_template):
    """Test della validazione dei dati con fallimento"""
    data = {"tipo_alloggio": "invalid"}
    
    with patch.object(alloggi_template, 'validate_alloggio', return_value=(False, "Error", data)):
        is_valid, msg, result = alloggi_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(alloggi_template):
    """Test della verifica del template con successo"""
    data = {"tipo_alloggio": "hotel", "adulti": 2, "bambini": 0}
    
    with patch.object(alloggi_template, 'get_template_data', return_value={"tipo_alloggio": None, "adulti": None, "bambini": None}), \
         patch.object(alloggi_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = alloggi_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(alloggi_template):
    """Test della verifica del template con errore"""
    data = {"tipo_alloggio": "invalid"}
    
    with patch.object(alloggi_template, 'get_template_data', return_value={"tipo_alloggio": None}), \
         patch.object(alloggi_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = alloggi_template.verifica_template(data)
        assert "test error" in errors[0].lower() 