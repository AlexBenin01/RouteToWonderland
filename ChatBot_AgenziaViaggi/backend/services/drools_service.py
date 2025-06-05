import requests
from typing import List, Dict, Any
from config import DROOLS_SERVICE_URL
import re
import logging

logger = logging.getLogger(__name__)

class DroolsService:
    def __init__(self):
        self.base_url = DROOLS_SERVICE_URL

    @staticmethod
    def _convert_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte i nomi dei campi da snake_case a camelCase.
        """
        result = {}
        for key, value in data.items():
            # Converti il nome del campo in camelCase
            camel_key = ''.join(word.capitalize() if i > 0 else word.lower() 
                              for i, word in enumerate(key.split('_')))
            result[camel_key] = value
        return result

    async def evaluate_Templates(self, preferences: Dict[str, Any]) -> List[str]:
        """
        Invia le preferenze al servizio Drools per la valutazione.
        
        Args:
            preferences: Dizionario contenente le preferenze di viaggio
            
        Returns:
            Lista dei template attivi
            
        Raises:
            Exception: Se la chiamata al servizio Drools fallisce
        """
        try:
            # Converti i nomi dei campi in camelCase
            camel_case_preferences = DroolsService._convert_to_camel_case(preferences)
            logger.info(f"Invio richiesta al servizio Drools: {camel_case_preferences}")
            response = requests.post(f"{self.base_url}/api/preferences/evaluate", json=camel_case_preferences)
            response.raise_for_status()  # Solleva un'eccezione per codici di errore HTTP
            result = response.json()
            logger.info(f"Risposta dal servizio Drools: {result}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Errore nella comunicazione con il servizio Drools: {str(e)}")
            raise Exception(f"Errore nella comunicazione con il servizio Drools: {str(e)}") 