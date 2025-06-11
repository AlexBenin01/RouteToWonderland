import pytest
from unittest.mock import patch, mock_open, MagicMock
from backend.librerie.base_template import BaseTemplate
from backend.librerie.template_manager import TemplateManager
import json

@pytest.fixture
def template_data():
    return {
        "test_template": {
            "fields": {
                "field1": "string",
                "field2": "number"
            },
            "required": ["field1"]
        }
    }

@pytest.fixture
def mock_template_manager(template_data):
    """Fixture per creare un mock del template manager"""
    mock = MagicMock()
    mock.get_active_template.return_value = template_data["test_template"]
    return mock

@pytest.fixture
def base_template(mock_template_manager):
    """Fixture per creare un'istanza di BaseTemplate"""
    return BaseTemplate(mock_template_manager)

def test_init(base_template, mock_template_manager):
    """Test dell'inizializzazione del template"""
    assert base_template.template_manager == mock_template_manager

def test_set_template(base_template, mock_template_manager):
    """Test del cambio di template"""
    base_template.set_template("nuovo_template")
    mock_template_manager.set_active_template.assert_called_once_with("nuovo_template")

def test_get_template_data(base_template, mock_template_manager, template_data):
    """Test del recupero dei dati del template"""
    data = base_template.get_template_data()
    assert data == template_data["test_template"]
    mock_template_manager.get_active_template.assert_called_once()

def test_are_data_different(base_template):
    """Test del confronto tra dati"""
    data1 = {"field1": "valore1", "field2": 2}
    data2 = {"field1": "valore1", "field2": 2}
    assert not base_template.are_data_different(data1, data2)
    
    data3 = {"field1": "valore_diverso"}
    assert base_template.are_data_different(data1, data3)

def test_validate_data(base_template):
    """Test della validazione dei dati"""
    data = {"field1": "valore1", "field2": 2}
    is_valid, msg, corrected_data = base_template.validate_data(data)
    assert is_valid
    assert msg == "Dati validi"
    assert corrected_data == data

def test_verifica_template(base_template):
    """Test della verifica del template"""
    data = {"field1": "valore1", "field2": 2}
    updated_data, warnings, errors = base_template.verifica_template(data)
    assert updated_data == data
    assert len(warnings) == 0
    assert len(errors) == 0 