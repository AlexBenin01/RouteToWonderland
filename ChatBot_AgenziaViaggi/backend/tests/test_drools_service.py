import pytest
from unittest.mock import patch, MagicMock
import requests
from backend.services.drools_service import DroolsService

def test_init():
    """Test dell'inizializzazione del servizio"""
    service = DroolsService()
    assert service.base_url == "http://localhost:8080"

def test_convert_to_camel_case():
    """Test della conversione in camelCase"""
    service = DroolsService()
    input_data = {
        "test_string": "value1",
        "another_test_string": "value2",
        "alreadyCamelCase": "value3"
    }
    expected = {
        "testString": "value1",
        "anotherTestString": "value2",
        "alreadyCamelCase": "value3"  # Mantiene il case originale
    }
    result = service._convert_to_camel_case(input_data)
    assert result == expected

def test_convert_to_camel_case_empty():
    """Test della conversione in camelCase con dizionario vuoto"""
    service = DroolsService()
    result = service._convert_to_camel_case({})
    assert result == {}

def test_convert_to_camel_case_none():
    """Test della conversione in camelCase con None"""
    service = DroolsService()
    with pytest.raises(AttributeError):
        service._convert_to_camel_case(None)

@pytest.mark.asyncio
async def test_evaluate_templates():
    """Test della valutazione dei template"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["template1", "template2"]
        mock_post.return_value = mock_response

        service = DroolsService()
        preferences = {"test_preference": "value"}
        result = await service.evaluate_Templates(preferences)
        
        assert result == ["template1", "template2"]
        mock_post.assert_called_once_with(
            "http://localhost:8080/api/preferences/evaluate",
            json={"testPreference": "value"}
        )

@pytest.mark.asyncio
async def test_evaluate_templates_error():
    """Test della gestione degli errori nella valutazione dei template"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection error")

        service = DroolsService()
        preferences = {"test_preference": "value"}
        with pytest.raises(Exception) as exc_info:
            await service.evaluate_Templates(preferences)
        assert "Errore nella comunicazione con il servizio Drools" in str(exc_info.value) 