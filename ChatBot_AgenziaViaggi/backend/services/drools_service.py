import requests
from typing import List, Dict, Any
from config import DROOLS_SERVICE_URL
import re

class DroolsService:
    @staticmethod
    def _to_camel_case(snake_str: str) -> str:
        """
        Converte una stringa da snake_case a camelCase
        Esempio: nazione_destinazione -> nazioneDestinazione
        """
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    @staticmethod
    def _convert_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converte tutte le chiavi di un dizionario da snake_case a camelCase
        """
        return {DroolsService._to_camel_case(k): v for k, v in data.items()}

    @staticmethod
    async def evaluate_preferences(preferences: Dict[str, Any]) -> List[str]:
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
            response = requests.post(DROOLS_SERVICE_URL, json=camel_case_preferences)
            response.raise_for_status()  # Solleva un'eccezione per codici di errore HTTP
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Errore nella comunicazione con il servizio Drools: {str(e)}") 