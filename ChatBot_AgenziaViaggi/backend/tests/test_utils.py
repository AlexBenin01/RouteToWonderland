import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.utils import extract_entities, extract_and_print

# Test per l'estrazione delle entità
def test_extract_entities():
    """Test dell'estrazione delle entità"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "entities": [
                {"text": "Firenze", "type": "LOC"},
                {"text": "Toscana", "type": "LOC"}
            ]
        }
        mock_post.return_value = mock_response

        result = extract_entities("Testo di esempio su Firenze in Toscana")
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["text"] == "Firenze"
        assert result[0]["type"] == "LOC"
        assert result[1]["text"] == "Toscana"
        assert result[1]["type"] == "LOC"

def test_extract_entities_empty():
    """Test dell'estrazione delle entità con testo vuoto"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"entities": []}
        mock_post.return_value = mock_response

        result = extract_entities("")
        assert isinstance(result, list)
        assert len(result) == 0

def test_extract_entities_error():
    """Test dell'estrazione delle entità con errore"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Errore di test")

        with pytest.raises(Exception) as exc_info:
            extract_entities("Testo di esempio")
        assert "Errore di test" in str(exc_info.value)

def test_extract_entities_invalid_response():
    """Test dell'estrazione delle entità con risposta non valida"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response"}
        mock_post.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            extract_entities("Testo di esempio")
        assert "Risposta non valida dal servizio" in str(exc_info.value)

def test_extract_entities_with_custom_model():
    with patch('backend.librerie.utils.AutoTokenizer') as mock_tokenizer, \
         patch('backend.librerie.utils.AutoModelForCausalLM') as mock_model:
        
        # Configura i mock
        mock_tokenizer_instance = MagicMock()
        mock_model_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Simula la risposta del modello
        mock_model_instance.generate.return_value = ["Test response"]
        mock_tokenizer_instance.batch_decode.return_value = ["Test response"]
        
        # Test con modello personalizzato
        text = "Testo di esempio"
        template = {"type": "location"}
        custom_model_path = "./custom-model"
        result = extract_entities(text, template, custom_model_path)
        
        assert isinstance(result, str)
        assert result == "Test response"
        
        # Verifica che il modello personalizzato sia stato usato
        mock_tokenizer.from_pretrained.assert_called_once_with(custom_model_path, trust_remote_code=True)
        mock_model.from_pretrained.assert_called_once_with(custom_model_path, trust_remote_code=True)

def test_extract_and_print():
    with patch('backend.librerie.utils.extract_entities') as mock_extract:
        mock_extract.return_value = "Test response"
        
        text = "Testo di esempio"
        template = {"type": "location"}
        result = extract_and_print(text, template)
        
        assert isinstance(result, str)
        assert result == "Test response"
        mock_extract.assert_called_once_with(text, template)

def test_extract_entities_empty_text():
    with patch('backend.librerie.utils.AutoTokenizer') as mock_tokenizer, \
         patch('backend.librerie.utils.AutoModelForCausalLM') as mock_model:
        
        # Configura i mock
        mock_tokenizer_instance = MagicMock()
        mock_model_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Simula la risposta del modello
        mock_model_instance.generate.return_value = [""]
        mock_tokenizer_instance.batch_decode.return_value = [""]
        
        # Test con testo vuoto
        text = ""
        template = {"type": "location"}
        result = extract_entities(text, template)
        
        assert isinstance(result, str)
        assert result == ""

def test_extract_entities_error():
    with patch('backend.librerie.utils.AutoTokenizer') as mock_tokenizer, \
         patch('backend.librerie.utils.AutoModelForCausalLM') as mock_model:
        
        # Simula un errore durante il caricamento del modello
        mock_tokenizer.from_pretrained.side_effect = Exception("Model loading error")
        
        # Test con errore
        text = "Testo di esempio"
        template = {"type": "location"}
        
        with pytest.raises(Exception) as exc_info:
            extract_entities(text, template)
        assert str(exc_info.value) == "Model loading error"
