import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.benessere_lib import BenessereTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def benessere_template(template_manager):
    template = BenessereTemplate(template_manager)
    template.template_path = "template/benessere.json"  # Aggiungo il template_path
    return template

def test_init(benessere_template):
    """Test dell'inizializzazione della classe BenessereTemplate"""
    assert benessere_template.model_path is not None
    assert benessere_template.model is not None
    assert benessere_template.template_path == "template/benessere.json"

def test_load_template(benessere_template):
    """Test del caricamento del template"""
    with patch('builtins.open', MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
        result = benessere_template._load_template()
        assert result == {"test": "data"}

def test_load_template_file_not_found(benessere_template):
    """Test del caricamento del template quando il file non esiste"""
    with patch('builtins.open', side_effect=FileNotFoundError) as mock_open:
        mock_open.side_effect = [FileNotFoundError, MagicMock()]
        mock_open.return_value.__enter__.return_value.read.return_value = '{"default": "data"}'
        result = benessere_template._load_template()
        assert result == {"default": "data"}

def test_set_template(benessere_template):
    """Test del cambio di template"""
    with patch.object(benessere_template, '_load_template') as mock_load:
        mock_load.return_value = {"new": "template"}
        benessere_template.set_template("nuovo_template")
        assert benessere_template.template_name == "nuovo_template"
        assert benessere_template.template_path == "template/nuovo_template.json"
        assert benessere_template.template_data == {"new": "template"}

def test_validate_trattamenti_success(benessere_template):
    """Test della validazione dei trattamenti con successo"""
    data = {"trattamenti": ["massaggio", "sauna"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(benessere_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.benessere_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("massaggio", 0.2), ("sauna", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = benessere_template.validate_trattamenti(data)
        assert is_valid
        assert "verificati" in msg.lower()
        assert len(result["trattamenti"]) == 2

def test_validate_trattamenti_missing_data(benessere_template):
    """Test della validazione dei trattamenti con dati mancanti"""
    data = {}
    is_valid, msg, result = benessere_template.validate_trattamenti(data)
    assert is_valid
    assert "opzionali" in msg.lower()

def test_validate_trattamenti_high_distance(benessere_template):
    """Test della validazione dei trattamenti con distanza elevata"""
    data = {"trattamenti": ["invalid_treatment"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(benessere_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.benessere_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("massaggio", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = benessere_template.validate_trattamenti(data)
        assert is_valid
        assert result["trattamenti"] is None

def test_validate_data_success(benessere_template):
    """Test della validazione dei dati con successo"""
    data = {"trattamenti": ["massaggio"]}
    
    with patch.object(benessere_template, 'validate_trattamenti', return_value=(True, "Success", {"trattamenti": ["massaggio"]})):
        is_valid, msg, result = benessere_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result["trattamenti"] == ["massaggio"]

def test_validate_data_failure(benessere_template):
    """Test della validazione dei dati con fallimento"""
    data = {"trattamenti": ["invalid"]}
    
    with patch.object(benessere_template, 'validate_trattamenti', return_value=(False, "Error", {"trattamenti": None})):
        is_valid, msg, result = benessere_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(benessere_template):
    """Test della verifica del template con successo"""
    data = {"trattamenti": ["massaggio"]}
    
    with patch.object(benessere_template, 'get_template_data', return_value={"trattamenti": None}), \
         patch.object(benessere_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = benessere_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(benessere_template):
    """Test della verifica del template con errore"""
    data = {"trattamenti": ["invalid"]}
    
    with patch.object(benessere_template, 'get_template_data', return_value={"trattamenti": None}), \
         patch.object(benessere_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = benessere_template.verifica_template(data)
        assert "test error" in errors[0].lower() 