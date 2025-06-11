import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.contatti_lib import ContattiTemplate
from backend.librerie.template_manager import TemplateManager
import phonenumbers

@pytest.fixture
def template_manager():
    return MagicMock(spec=TemplateManager)

@pytest.fixture
def contatti_template(template_manager):
    template = ContattiTemplate(template_manager)
    template.template_path = "template/contatti.json"
    return template

def test_init(contatti_template):
    """Test dell'inizializzazione della classe ContattiTemplate"""
    assert contatti_template.template_path == "template/contatti.json"

def test_is_valid_phone_number(contatti_template):
    """Test della validazione del numero di telefono"""
    assert contatti_template.is_valid_phone_number("1234567890")  # 10 cifre
    assert not contatti_template.is_valid_phone_number("123456789")  # 9 cifre
    assert not contatti_template.is_valid_phone_number("12345678901")  # 11 cifre
    assert not contatti_template.is_valid_phone_number("123456789a")  # contiene lettere

def test_is_valid_email(contatti_template):
    """Test della validazione dell'email"""
    assert contatti_template.is_valid_email("test@example.com")
    assert contatti_template.is_valid_email("test.name@example.com")
    assert not contatti_template.is_valid_email("test@example")  # dominio incompleto
    assert not contatti_template.is_valid_email("test@.com")  # dominio vuoto
    assert not contatti_template.is_valid_email("@example.com")  # username vuoto

def test_is_valid_codice_fiscale(contatti_template):
    """Test della validazione del codice fiscale"""
    assert contatti_template.is_valid_codice_fiscale("RSSMRA80A01H501U")  # Codice fiscale valido
    assert not contatti_template.is_valid_codice_fiscale("RSSMRA80A01H501")  # Codice fiscale incompleto
    assert not contatti_template.is_valid_codice_fiscale("RSSMRA80A01H501X")  # Codice fiscale non valido

def test_is_valid_partita_iva(contatti_template):
    """Test della validazione della partita IVA"""
    assert contatti_template.is_valid_partita_iva("12345678901")  # Partita IVA valida
    assert not contatti_template.is_valid_partita_iva("1234567890")  # Partita IVA incompleta
    assert not contatti_template.is_valid_partita_iva("123456789012")  # Partita IVA troppo lunga

def test_validate_data_success(contatti_template):
    """Test della validazione dei dati con successo"""
    data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RSSMRA80A01H501U",
        "numero_cellulare": "+393331234567",
        "email": "mario.rossi@example.com"
    }
    
    with patch.object(contatti_template, 'is_valid_codice_fiscale', return_value=True), \
         patch.object(contatti_template, 'is_valid_partita_iva', return_value=False):
        is_valid, msg, result = contatti_template.validate_data(data)
        assert is_valid
        assert "validi" in msg.lower()
        assert result["full_name"] == "Mario Rossi"
        assert result["codice_fiscale_o_partita_iva"] == "RSSMRA80A01H501U"
        assert "email" in result

def test_validate_data_invalid_name(contatti_template):
    """Test della validazione dei dati con nome non valido"""
    data = {
        "full_name": "",  # Nome vuoto
        "codice_fiscale_o_partita_iva": "RSSMRA80A01H501U",
        "numero_cellulare": "+393331234567",
        "email": "mario.rossi@example.com"
    }
    
    is_valid, msg, result = contatti_template.validate_data(data)
    assert not is_valid
    assert "vuoto" in msg.lower()

def test_validate_data_invalid_cf_piva(contatti_template):
    """Test della validazione dei dati con codice fiscale/partita IVA non validi"""
    data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "invalid",
        "numero_cellulare": "+393331234567",
        "email": "mario.rossi@example.com"
    }
    
    with patch.object(contatti_template, 'is_valid_codice_fiscale', return_value=False), \
         patch.object(contatti_template, 'is_valid_partita_iva', return_value=False):
        is_valid, msg, result = contatti_template.validate_data(data)
        assert not is_valid
        assert "valida" in msg.lower()

def test_validate_data_invalid_phone(contatti_template):
    """Test della validazione dei dati con numero di telefono non valido"""
    data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RSSMRA80A01H501U",
        "numero_cellulare": "invalid",
        "email": "mario.rossi@example.com"
    }
    
    with patch.object(contatti_template, 'is_valid_codice_fiscale', return_value=True), \
         patch.object(contatti_template, 'is_valid_partita_iva', return_value=False):
        is_valid, msg, result = contatti_template.validate_data(data)
        assert not is_valid
        assert "valido" in msg.lower()

def test_validate_data_invalid_email(contatti_template):
    """Test della validazione dei dati con email non valida"""
    data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RSSMRA80A01H501U",
        "numero_cellulare": "+393331234567",
        "email": "invalid-email"
    }
    
    with patch.object(contatti_template, 'is_valid_codice_fiscale', return_value=True), \
         patch.object(contatti_template, 'is_valid_partita_iva', return_value=False):
        is_valid, msg, result = contatti_template.validate_data(data)
        assert not is_valid
        assert "valido" in msg.lower()

def test_verifica_template_success(contatti_template):
    """Test della verifica del template con successo"""
    data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RSSMRA80A01H501U",
        "numero_cellulare": "+393331234567",
        "email": "mario.rossi@example.com"
    }
    
    with patch.object(contatti_template, 'get_template_data', return_value={}), \
         patch.object(contatti_template, 'validate_data', return_value=(True, "Success", data)):
        result, was_different, warnings, errors = contatti_template.verifica_template(data)
        assert result == data
        assert not warnings
        assert not errors

def test_verifica_template_error(contatti_template):
    """Test della verifica del template con errore"""
    data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "invalid",
        "numero_cellulare": "invalid",
        "email": "invalid-email"
    }
    
    with patch.object(contatti_template, 'get_template_data', return_value={}), \
         patch.object(contatti_template, 'validate_data', side_effect=Exception("Test error")):
        result, was_different, warnings, errors = contatti_template.verifica_template(data)
        assert "test error" in errors[0].lower() 