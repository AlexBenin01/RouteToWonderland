import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.intro_lib import IntroTemplate
from backend.librerie.template_manager import TemplateManager
import numpy as np
from datetime import datetime, timedelta

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def intro_template(template_manager):
    template = IntroTemplate(template_manager)
    template.template_path = "template/intro.json"
    return template

def test_init(intro_template):
    """Test dell'inizializzazione della classe IntroTemplate"""
    assert intro_template.model_path is not None
    assert intro_template.model is not None
    assert intro_template.template_path == "template/intro.json"

def test_adjust_past_date(intro_template):
    """Test della correzione delle date passate"""
    # Data nel passato
    past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    adjusted_date = intro_template._adjust_past_date(past_date)
    assert datetime.strptime(adjusted_date, '%Y-%m-%d') > datetime.now()
    
    # Data futura
    future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    assert intro_template._adjust_past_date(future_date) == future_date

def test_verifica_destinazione_generica_success(intro_template):
    """Test della verifica della destinazione generica con successo"""
    data = {"nazione_destinazione": "Italia"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(intro_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.intro_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("Italia", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = intro_template.verifica_destinazione_generica(data)
        assert is_valid
        assert "verificata" in msg.lower()
        assert result["nazione_destinazione"] == "Italia"

def test_verifica_destinazione_locale_success(intro_template):
    """Test della verifica della destinazione locale con successo"""
    data = {"regione_citta_destinazione": "Roma"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(intro_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.intro_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("Roma", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = intro_template.verifica_destinazione_locale(data)
        assert is_valid
        assert "verificata" in msg.lower()
        assert result["regione_citta_destinazione"] == "Roma"

def test_verifica_mood_vacanza_success(intro_template):
    """Test della verifica del mood della vacanza con successo"""
    data = {"mood_vacanza": ["mare", "montagna"]}
    mock_embedding = np.random.rand(384)
    
    with patch.object(intro_template.model, 'encode', return_value=mock_embedding), \
         patch('backend.librerie.intro_lib.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("mare", 0.2), ("montagna", 0.2)]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        is_valid, msg, result = intro_template.verifica_mood_vacanza(data)
        assert is_valid
        assert "verificato" in msg.lower()
        assert len(result["mood_vacanza"]) == 2

def test_verifica_tipo_partecipanti_success(intro_template):
    """Test della verifica del tipo di partecipanti con successo"""
    data = {"tipo_partecipanti": "famiglia"}
    mock_embedding = np.random.rand(384)
    
    with patch.object(intro_template.model, 'encode', return_value=mock_embedding):
        is_valid, msg, result = intro_template.verifica_tipo_partecipanti(data)
        assert is_valid
        assert "verificato" in msg.lower()

def test_validate_data_success(intro_template):
    """Test della validazione dei dati con successo"""
    data = {
        "nazione_destinazione": "Italia",
        "regione_citta_destinazione": "Roma",
        "departure_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        "numero_partecipanti": 4,
        "tipo_partecipanti": "famiglia",
        "mood_vacanza": ["mare"],
        "budget_viaggio": 1000,
        "trip_duration": 7
    }
    
    with patch.object(intro_template, 'verifica_destinazione_generica', return_value=(True, "Success", data)), \
         patch.object(intro_template, 'verifica_destinazione_locale', return_value=(True, "Success", data)), \
         patch.object(intro_template, 'verifica_mood_vacanza', return_value=(True, "Success", data)), \
         patch.object(intro_template, 'verifica_tipo_partecipanti', return_value=(True, "Success", data)):
        is_valid, msg, result = intro_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()

def test_validate_data_invalid_dates(intro_template):
    """Test della validazione dei dati con date non valide"""
    data = {
        "departure_date": "invalid-date",
        "trip_duration": -1
    }
    
    is_valid, msg, result = intro_template.validate_data(data)
    assert not is_valid
    assert "formato" in msg.lower() or "durata" in msg.lower()

def test_validate_data_invalid_numbers(intro_template):
    """Test della validazione dei dati con numeri non validi"""
    data = {
        "numero_partecipanti": -1,
        "budget_viaggio": -1000
    }
    
    is_valid, msg, result = intro_template.validate_data(data)
    assert not is_valid
    assert "intero" in msg.lower() or "negativo" in msg.lower()

def test_verifica_template_success(intro_template):
    """Test della verifica del template con successo"""
    data = {
        "nazione_destinazione": "Italia",
        "regione_citta_destinazione": "Roma",
        "departure_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        "numero_partecipanti": 4,
        "tipo_partecipanti": "famiglia",
        "mood_vacanza": ["mare"],
        "budget_viaggio": 1000,
        "trip_duration": 7
    }
    
    with patch.object(intro_template, 'get_template_data', return_value={}), \
         patch.object(intro_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = intro_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(intro_template):
    """Test della verifica del template con errore"""
    data = {
        "nazione_destinazione": "invalid",
        "departure_date": "invalid-date"
    }
    
    with patch.object(intro_template, 'get_template_data', return_value={}), \
         patch.object(intro_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = intro_template.verifica_template(data)
        assert "test error" in errors[0].lower() 