"""
Libreria per la gestione del template noleggi.json
Gestisce le preferenze per servizi di noleggio
"""
import json
from typing import Dict, Any, Tuple, List
from datetime import datetime
import re
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from pathlib import Path

class NoleggiTemplate:
    def __init__(self):
        self.template_path = "template/noleggi.json"
        self.template_data = self._load_template()
    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Valida i dati in input secondo il template"""
        corrected_data = {}
        
        try:
            # Validazione posti_auto integer
            if 'posti_auto' in data:
                if not isinstance(data['posti_auto'], int):
                    return False, "Il campo posti_auto deve essere un numero intero", corrected_data
                corrected_data['posti_auto'] = data['posti_auto']

            # Validazione tipo_cambio
            if 'tipo_cambio' in data:
                if not isinstance(data['tipo_cambio'], bool):
                    return False, "Il campo tipo_cambio deve essere un booleano", corrected_data
                corrected_data['tipo_cambio'] = data['tipo_cambio']

            return True, "Dati validi", corrected_data
            
        except Exception as e:
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    


    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template avventura
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        warnings = []
        errors = []
        updated_data = data.copy()
        
        try:
            
            # Verifica la validità dei dati
            is_valid, msg, updated_data = self.validate_data(updated_data)
            if not is_valid:
                errors.append(msg)
            
            return updated_data, warnings, errors 
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            return updated_data, warnings, errors 