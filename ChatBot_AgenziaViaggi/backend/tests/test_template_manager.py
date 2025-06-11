import pytest
from unittest.mock import patch, mock_open
import json
from backend.librerie.template_manager import TemplateManager

# Test per il caricamento dei template
def test_load_templates():
    """Test del caricamento dei template"""
    template_data = {
        "intro": {
            "fields": {
                "regione_citta_destinazione": "string",
                "numero_partecipanti": "number",
                "trip_duration": "number",
                "budget_viaggio": "number"
            },
            "required": [
                "regione_citta_destinazione",
                "numero_partecipanti",
                "trip_duration",
                "budget_viaggio"
            ]
        }
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(template_data))):
        manager = TemplateManager()
        manager.load_templates()
        assert manager.templates == template_data

def test_load_templates_file_not_found():
    """Test del caricamento dei template con file non trovato"""
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError()
        manager = TemplateManager()
        manager.load_templates()
        assert manager.templates == {}

def test_load_templates_invalid_json():
    """Test del caricamento dei template con JSON invalido"""
    with patch('builtins.open', mock_open(read_data='invalid json')):
        manager = TemplateManager()
        manager.load_templates()
        assert manager.templates == {}

# Test per la validazione dei dati
def test_validate_data():
    template_data = {
        "intro": {
            "fields": ["regione_citta_destinazione", "numero_partecipanti", "trip_duration", "budget_viaggio"],
            "required": ["regione_citta_destinazione", "numero_partecipanti", "trip_duration", "budget_viaggio"]
        }
    }
    
    with patch("builtins.open", mock_open(read_data=json.dumps(template_data))):
        manager = TemplateManager()
        
        # Test con dati validi
        valid_data = {
            "regione_citta_destinazione": "Toscana, Firenze",
            "numero_partecipanti": 2,
            "trip_duration": 7,
            "budget_viaggio": 1000
        }
        assert manager.validate_data("intro", valid_data) is True
        
        # Test con dati mancanti
        invalid_data = {
            "regione_citta_destinazione": "Toscana, Firenze",
            "numero_partecipanti": 2
        }
        assert manager.validate_data("intro", invalid_data) is False
        
        # Test con template non esistente
        assert manager.validate_data("non_existent", valid_data) is False

# Test per il recupero dei campi richiesti
def test_get_required_fields():
    template_data = {
        "intro": {
            "fields": ["regione_citta_destinazione", "numero_partecipanti", "trip_duration", "budget_viaggio"],
            "required": ["regione_citta_destinazione", "numero_partecipanti", "trip_duration", "budget_viaggio"]
        }
    }
    
    with patch("builtins.open", mock_open(read_data=json.dumps(template_data))):
        manager = TemplateManager()
        
        # Test con template esistente
        required_fields = manager.get_required_fields("intro")
        assert isinstance(required_fields, list)
        assert len(required_fields) == 4
        assert "regione_citta_destinazione" in required_fields
        
        # Test con template non esistente
        assert manager.get_required_fields("non_existent") == []

# Test per il recupero di tutti i campi
def test_get_all_fields():
    template_data = {
        "intro": {
            "fields": ["regione_citta_destinazione", "numero_partecipanti", "trip_duration", "budget_viaggio"],
            "required": ["regione_citta_destinazione", "numero_partecipanti", "trip_duration", "budget_viaggio"]
        }
    }
    
    with patch("builtins.open", mock_open(read_data=json.dumps(template_data))):
        manager = TemplateManager()
        
        # Test con template esistente
        all_fields = manager.get_all_fields("intro")
        assert isinstance(all_fields, list)
        assert len(all_fields) == 4
        assert "regione_citta_destinazione" in all_fields
        
        # Test con template non esistente
        assert manager.get_all_fields("non_existent") == []

# Test per il recupero di un template specifico
def test_get_template():
    """Test del recupero di un template"""
    template_data = {
        "intro": {
            "fields": {
                "regione_citta_destinazione": "string",
                "numero_partecipanti": "number"
            },
            "required": ["regione_citta_destinazione"]
        }
    }
    
    with patch('builtins.open', mock_open(read_data=json.dumps(template_data))):
        manager = TemplateManager()
        manager.load_templates()
        template = manager.get_template("intro")
        assert template == template_data["intro"]
        assert manager.get_template("non_existent") is None

def test_set_active_template():
    """Test dell'impostazione del template attivo"""
    manager = TemplateManager()
    manager.set_active_template("intro")
    assert manager.active_template == "intro"

def test_update_template_sequence():
    """Test dell'aggiornamento della sequenza dei template"""
    manager = TemplateManager()
    sequence = ["intro", "contatti", "trasporto"]
    manager.update_template_sequence(sequence)
    assert manager.template_sequence == sequence 