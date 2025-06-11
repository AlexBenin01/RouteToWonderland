import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.gastronomia_lib import GastronomiaTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def gastronomia_template(template_manager):
    template = GastronomiaTemplate(template_manager)
    template.template_path = "template/gastronomia.json"
    return template

def test_init(gastronomia_template):
    """Test dell'inizializzazione della classe GastronomiaTemplate"""
    assert gastronomia_template.model_path is not None
    assert gastronomia_template.model is not None
    assert gastronomia_template.template_path == "template/gastronomia.json"

def test_validate_degustazione_success(gastronomia_template):
    """Test della validazione delle degustazioni con successo"""
    data = {"degustazioni": ["vini", "formaggi"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(gastronomia_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.gastronomia_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("vini", 0.2), ("formaggi", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = gastronomia_template.validate_degustazione(data)
        assert is_valid
        assert "verificate" in msg.lower()
        assert len(result["degustazioni"]) == 2

def test_validate_degustazione_missing_data(gastronomia_template):
    """Test della validazione delle degustazioni con dati mancanti"""
    data = {}
    is_valid, msg, result = gastronomia_template.validate_degustazione(data)
    assert is_valid
    assert "opzionali" in msg.lower()

def test_validate_degustazione_high_distance(gastronomia_template):
    """Test della validazione delle degustazioni con distanza elevata"""
    data = {"degustazioni": ["invalid_degustazione"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(gastronomia_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.gastronomia_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("vini", 0.5)]  # Distanza > 0.4
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = gastronomia_template.validate_degustazione(data)
        assert is_valid
        assert result["degustazioni"] is None

def test_validate_data_success(gastronomia_template):
    """Test della validazione dei dati con successo"""
    data = {
        "corsi_cucina": True,
        "degustazioni": ["vini"]
    }
    
    with patch.object(gastronomia_template, 'validate_degustazione', return_value=(True, "Success", {"degustazioni": ["vini"]})):
        is_valid, msg, result = gastronomia_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result["corsi_cucina"] is True
        assert result["degustazioni"] == ["vini"]

def test_validate_data_invalid_corsi_cucina(gastronomia_template):
    """Test della validazione dei dati con corsi_cucina non booleano"""
    data = {
        "corsi_cucina": "si",
        "degustazioni": ["vini"]
    }
    
    is_valid, msg, result = gastronomia_template.validate_data(data)
    assert not is_valid
    assert "booleano" in msg.lower()

def test_validate_data_failure(gastronomia_template):
    """Test della validazione dei dati con fallimento"""
    data = {"degustazioni": ["invalid"]}
    
    with patch.object(gastronomia_template, 'validate_degustazione', return_value=(False, "Error", {"degustazioni": None})):
        is_valid, msg, result = gastronomia_template.validate_data(data)
        assert not is_valid
        assert "error" in msg.lower()

def test_verifica_template_success(gastronomia_template):
    """Test della verifica del template con successo"""
    data = {
        "corsi_cucina": True,
        "degustazioni": ["vini"]
    }
    
    with patch.object(gastronomia_template, 'get_template_data', return_value={"corsi_cucina": None, "degustazioni": None}), \
         patch.object(gastronomia_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = gastronomia_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(gastronomia_template):
    """Test della verifica del template con errore"""
    data = {
        "corsi_cucina": True,
        "degustazioni": ["invalid"]
    }
    
    with patch.object(gastronomia_template, 'get_template_data', return_value={"corsi_cucina": None, "degustazioni": None}), \
         patch.object(gastronomia_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = gastronomia_template.verifica_template(data)
        assert "test error" in errors[0].lower() 