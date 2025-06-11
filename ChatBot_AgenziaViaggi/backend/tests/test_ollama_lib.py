import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.ollama_lib import OllamaManager

def test_load_frasi_guida():
    om = OllamaManager()
    frasi = om._load_frasi_guida()
    assert isinstance(frasi, dict)

def test_create_prompt():
    om = OllamaManager()
    template = {"campo1": None, "campo2": "valore"}
    prompt = om._create_prompt("intro", template)
    assert "campo1" in prompt or "campo2" in prompt

def test_validate_response():
    om = OllamaManager()
    assert om.validate_response("123", "integer") is True
    assert om.validate_response("ciao", "integer") is False
    assert om.validate_response("true", "boolean") is True
    assert om.validate_response("no", "boolean") is True
    assert om.validate_response("2023-01-01", "date") is True
    assert om.validate_response("testo", "string") is True

def test_init():
    manager = OllamaManager()
    assert manager.base_url == "http://localhost:11434/api"
    assert manager.model_name == "qwen3:1.7b"

def test_get_response():
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Test response\n\nRisposta finale"
        }
        mock_post.return_value = mock_response
        
        manager = OllamaManager()
        result = manager.get_response("intro", {"campo1": None})
        
        assert result == "Risposta finale"
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == "qwen3:1.7b"
        assert call_args['stream'] is False

def test_get_response_error():
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Connection error")
        
        manager = OllamaManager()
        result = manager.get_response("intro", {"campo1": None})
        assert "Si è verificato un errore" in result

def test_get_exit():
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Test response\n\nRisposta finale"
        }
        mock_post.return_value = mock_response
        
        manager = OllamaManager()
        result = manager.get_exit()
        
        assert result == "Risposta finale"
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == "qwen3:1.7b"
        assert call_args['stream'] is False

def test_get_exit_error():
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Connection error")
        
        manager = OllamaManager()
        result = manager.get_exit()
        assert "Si è verificato un errore" in result

def test_campi_obbligatori():
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Test response\n\nAbbiamo ancora delle domande obbligatorie prima di passare alla fattura di viaggio"
        }
        mock_post.return_value = mock_response
        
        manager = OllamaManager()
        result = manager.campi_obbligatori()
        
        assert "Abbiamo ancora delle domande obbligatorie" in result
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]['json']
        assert call_args['model'] == "qwen3:1.7b"
        assert call_args['stream'] is False

def test_campi_obbligatori_error():
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Connection error")
        
        manager = OllamaManager()
        result = manager.campi_obbligatori()
        assert "Si è verificato un errore" in result 