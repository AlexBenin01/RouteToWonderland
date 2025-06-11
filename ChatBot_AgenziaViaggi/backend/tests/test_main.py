import pytest
from fastapi.testclient import TestClient
from backend.main import app
import json
from datetime import datetime, timedelta

client = TestClient(app)

def test_get_templates():
    """Test dell'endpoint templates"""
    response = client.get("/get_templates")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "intro" in data
    assert "contatti" in data
    assert "trasporto" in data

def test_get_template_sequence():
    """Test dell'endpoint template-sequence"""
    response = client.get("/get_template_sequence")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "intro" in data
    assert "contatti" in data
    assert "trasporto" in data

def test_set_template():
    """Test dell'endpoint set_template"""
    test_data = {
        "template_type": "intro"
    }
    response = client.post("/set_template", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "template_attivo" in data
    assert data["template_attivo"] == "intro"

def test_set_template_invalid():
    """Test dell'endpoint set_template con template non valido"""
    test_data = {
        "template_type": "non_existent_template"
    }
    response = client.post("/set_template", json=test_data)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

def test_extract_simple_with_valid_data():
    """Test dell'endpoint extract_simple con dati validi"""
    test_data = {
        "text": "Voglio andare a Roma per una settimana con la mia famiglia",
        "campo": None
    }
    response = client.post("/extract_simple", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "guide_phrase" in data
    assert "template_usato" in data
    assert "stato_conversazione" in data
    assert "exit" in data
    assert "riepilogo" in data

def test_extract_simple_with_empty_text():
    """Test dell'endpoint extract_simple con testo vuoto"""
    test_data = {
        "text": "",
        "campo": None
    }
    response = client.post("/extract_simple", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "guide_phrase" in data
    assert "template_usato" in data

def test_extract_simple_with_special_characters():
    """Test dell'endpoint extract_simple con caratteri speciali"""
    test_data = {
        "text": "Voglio andare a Roma! È una città bellissima...",
        "campo": None
    }
    response = client.post("/extract_simple", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "guide_phrase" in data
    assert "template_usato" in data

def test_evaluate_preferences():
    """Test dell'endpoint evaluate_preferences"""
    test_data = {
        "nazione_destinazione": "Italia",
        "regione_citta_destinazione": "Roma",
        "numero_partecipanti": 4,
        "tipo_partecipanti": "famiglia",
        "departure_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        "trip_duration": 7,
        "mood_vacanza": ["mare", "cultura"],
        "budget_viaggio": 1000
    }
    response = client.post("/evaluate_preferences", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "active_templates" in data
    assert "new_sequence" in data
    assert "message" in data

def test_get_summary():
    """Test dell'endpoint get_summary"""
    response = client.get("/get_summary")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "show_summary" in data

def test_debug_stato():
    """Test dell'endpoint debug_stato"""
    response = client.get("/debug_stato")
    assert response.status_code == 200
    data = response.json()
    assert "stato_conversazione" in data
    assert "template_attivo" in data
    assert "sequenza_template" in data
    assert "contesto_conversazione" in data

def test_skip_template():
    """Test dell'endpoint skip_template"""
    response = client.post("/skip_template")
    assert response.status_code == 200
    data = response.json()
    assert "guide_phrase" in data
    assert "template_usato" in data
    assert "stato_conversazione" in data
    assert "nuovo_template" in data

def test_get_continue():
    """Test dell'endpoint get_continue"""
    response = client.get("/get_continue")
    assert response.status_code == 200
    data = response.json()
    assert "guide_phrase" in data
    assert "template_usato" in data
    assert "stato_conversazione" in data
    assert "exit" in data

def test_completa_ordine():
    """Test dell'endpoint completa_ordine"""
    test_data = {
        "budget_usato": 1000.0,
        "documento": "ABC123"
    }
    response = client.post("/completa_ordine", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "identificativo" in data
    assert "budget_totale" in data 