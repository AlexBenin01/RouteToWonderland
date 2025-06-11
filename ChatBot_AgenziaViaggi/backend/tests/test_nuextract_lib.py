import pytest
from backend.librerie.NuEstractLib import NuExtract
import json
import os

@pytest.fixture
def nuextract():
    """Fixture per creare un'istanza di NuExtract"""
    return NuExtract()

def test_init():
    """Test dell'inizializzazione della classe NuExtract"""
    nue = NuExtract()
    assert nue.model_path == './NuExtract-2-2B-experimental'
    assert os.path.exists(nue.model_path), "Il percorso del modello non esiste"

def test_process_extraction_with_valid_text():
    """Test dell'estrazione con testo valido"""
    nue = NuExtract()
    text = "Voglio andare a Roma per una settimana con la mia famiglia"
    empty_template = {
        "nazione_destinazione": None,
        "regione_citta_destinazione": None,
        "trip_duration": None,
        "tipo_partecipanti": None
    }
    saved_template = empty_template.copy()
    
    result = nue.process_extraction(text, empty_template, saved_template)
    
    assert isinstance(result, dict)
    assert "nazione_destinazione" in result
    assert "regione_citta_destinazione" in result
    assert "trip_duration" in result
    assert "tipo_partecipanti" in result

def test_process_extraction_with_empty_text():
    """Test dell'estrazione con testo vuoto"""
    nue = NuExtract()
    text = ""
    empty_template = {
        "nazione_destinazione": None,
        "regione_citta_destinazione": None
    }
    saved_template = empty_template.copy()
    
    result = nue.process_extraction(text, empty_template, saved_template)
    assert result == saved_template

def test_process_extraction_with_special_characters():
    """Test dell'estrazione con caratteri speciali"""
    nue = NuExtract()
    text = "Voglio andare a Roma! È una città bellissima..."
    empty_template = {
        "nazione_destinazione": None,
        "regione_citta_destinazione": None
    }
    saved_template = empty_template.copy()
    
    result = nue.process_extraction(text, empty_template, saved_template)
    assert isinstance(result, dict)
    assert "regione_citta_destinazione" in result

def test_process_extraction_with_multiple_entities():
    """Test dell'estrazione con multiple entità"""
    nue = NuExtract()
    text = "Voglio andare a Roma con la mia famiglia per una settimana, budget 1000 euro"
    empty_template = {
        "nazione_destinazione": None,
        "regione_citta_destinazione": None,
        "tipo_partecipanti": None,
        "trip_duration": None,
        "budget_viaggio": None
    }
    saved_template = empty_template.copy()
    
    result = nue.process_extraction(text, empty_template, saved_template)
    assert isinstance(result, dict)
    assert len(result) > 1

def test_process_exit_with_exit_intent():
    """Test del processamento dell'uscita con intento di uscita"""
    nue = NuExtract()
    text = "Voglio uscire"
    empty_template = {"exit": False}
    
    result = nue.process_exit(text, empty_template)
    assert isinstance(result, bool)

def test_process_exit_without_exit_intent():
    """Test del processamento dell'uscita senza intento di uscita"""
    nue = NuExtract()
    text = "Voglio continuare"
    empty_template = {"exit": False}
    
    result = nue.process_exit(text, empty_template)
    assert isinstance(result, bool)

def test_process_extraction_with_nested_template():
    """Test dell'estrazione con template annidato"""
    nue = NuExtract()
    text = "Voglio prenotare un hotel a Roma con piscina e spa"
    empty_template = {
        "alloggio": {
            "tipo": None,
            "servizi": []
        }
    }
    saved_template = empty_template.copy()
    
    result = nue.process_extraction(text, empty_template, saved_template)
    assert isinstance(result, dict)
    assert "alloggio" in result
    assert isinstance(result["alloggio"], dict)

def test_process_extraction_with_list_values():
    """Test dell'estrazione con valori lista"""
    nue = NuExtract()
    text = "Mi piacciono le attività: trekking, nuoto e ciclismo"
    empty_template = {
        "attivita_preferite": []
    }
    saved_template = empty_template.copy()
    
    result = nue.process_extraction(text, empty_template, saved_template)
    assert isinstance(result, dict)
    assert "attivita_preferite" in result
    assert isinstance(result["attivita_preferite"], list)

def test_process_extraction_with_date_values():
    """Test dell'estrazione con valori data"""
    nue = NuExtract()
    text = "Voglio partire il 15 giugno 2024"
    empty_template = {
        "departure_date": None
    }
    saved_template = empty_template.copy()
    
    result = nue.process_extraction(text, empty_template, saved_template)
    assert isinstance(result, dict)
    assert "departure_date" in result 