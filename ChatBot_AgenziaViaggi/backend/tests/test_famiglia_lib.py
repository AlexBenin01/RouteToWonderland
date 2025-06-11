import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.famiglia_lib import FamigliaTemplate
from backend.librerie.template_manager import TemplateManager

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def famiglia_template(template_manager):
    template = FamigliaTemplate(template_manager)
    template.template_path = "template/famiglia.json"
    return template

def test_init(famiglia_template):
    """Test dell'inizializzazione della classe FamigliaTemplate"""
    assert famiglia_template.template_path == "template/famiglia.json"

def test_validate_data_success(famiglia_template):
    """Test della validazione dei dati con successo"""
    data = {
        "adulti": 2,
        "bambini": 2
    }
    
    is_valid, msg, result = famiglia_template.validate_data(data)
    assert is_valid
    assert "validi" in msg.lower()
    assert result["adulti"] == 2
    assert result["bambini"] == 2

def test_validate_data_negative_adulti(famiglia_template):
    """Test della validazione dei dati con adulti negativi"""
    data = {
        "adulti": -2,
        "bambini": 2
    }
    
    is_valid, msg, result = famiglia_template.validate_data(data)
    assert is_valid
    assert result["adulti"] == 2  # Il valore negativo viene convertito in positivo

def test_validate_data_negative_bambini(famiglia_template):
    """Test della validazione dei dati con bambini negativi"""
    data = {
        "adulti": 2,
        "bambini": -2
    }
    
    is_valid, msg, result = famiglia_template.validate_data(data)
    assert is_valid
    assert result["bambini"] == 2  # Il valore negativo viene convertito in positivo

def test_validate_data_invalid_type(famiglia_template):
    """Test della validazione dei dati con tipi non validi"""
    data = {
        "adulti": "due",
        "bambini": "due"
    }
    
    is_valid, msg, result = famiglia_template.validate_data(data)
    assert is_valid
    assert result["adulti"] == 0  # Valore di default per tipo non valido
    assert result["bambini"] == 0  # Valore di default per tipo non valido

def test_validate_data_missing_fields(famiglia_template):
    """Test della validazione dei dati con campi mancanti"""
    data = {}
    
    is_valid, msg, result = famiglia_template.validate_data(data)
    assert is_valid
    assert "adulti" not in result
    assert "bambini" not in result

def test_verifica_template_success(famiglia_template):
    """Test della verifica del template con successo"""
    data = {
        "adulti": 2,
        "bambini": 2
    }
    
    with patch.object(famiglia_template, 'get_template_data', return_value={"adulti": None, "bambini": None}), \
         patch.object(famiglia_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = famiglia_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(famiglia_template):
    """Test della verifica del template con errore"""
    data = {
        "adulti": "invalid",
        "bambini": "invalid"
    }
    
    with patch.object(famiglia_template, 'get_template_data', return_value={"adulti": None, "bambini": None}), \
         patch.object(famiglia_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = famiglia_template.verifica_template(data)
        assert "test error" in errors[0].lower() 