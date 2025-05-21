"""
Libreria per la gestione del template noleggi.json
Gestisce le informazioni relative ai noleggi
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
from .template_manager import TemplateManager
from .base_template import BaseTemplate

class NoleggiTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.template_path = "template/noleggi.json"
        self.template_data = self._load_template()
    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida i dati in input secondo il template
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        print("[DEBUG] Inizio validazione dati noleggi")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        template_data = self.get_template_data()
        
        try:

            
            # Validazione posti_auto
            if 'posti_auto' in data:
                print(f"[DEBUG] Validazione posti_auto: {data['posti_auto']}")
                if not isinstance(data['posti_auto'], int):
                    print("[ERROR] posti_auto non è un intero")
                    corrected_data['posti_auto'] = None
                    return False, "Il numero di posti auto deve essere un numero intero", corrected_data
                if data['posti_auto'] < 2 or data['posti_auto'] > 12:
                    print("[ERROR] posti_auto fuori range (2-12)")
                    corrected_data['posti_auto'] = None
                    return False, "Il numero di posti auto deve essere compreso tra 2 e 12", corrected_data
                print(f"[DEBUG] posti_auto valido: {data['posti_auto']}")

            # Validazione cambio_automatico
            if 'cambio_automatico' in data:
                print(f"[DEBUG] Validazione cambio_automatico: {data['cambio_automatico']}")
                if not isinstance(data['cambio_automatico'], bool):
                    print("[ERROR] cambio_automatico non è un booleano")
                    corrected_data['cambio_automatico'] = None
                    return False, "Il campo cambio automatico deve essere un booleano", corrected_data
                print(f"[DEBUG] cambio_automatico valido: {data['cambio_automatico']}")
            
            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template noleggi
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        print("[DEBUG] Inizio verifica_template noleggi")
        print(f"[DEBUG] Dati ricevuti: {data}")
        warnings = []
        errors = []
        updated_data = data.copy()
        
        try:
            # Chiama il metodo della classe base per la validazione standard
            print("[DEBUG] Chiamata verifica_template della classe base")
            updated_data, base_warnings, base_errors = super().verifica_template(updated_data)
            warnings.extend(base_warnings)
            errors.extend(base_errors)
            print(f"[DEBUG] Warnings dalla classe base: {base_warnings}")
            print(f"[DEBUG] Errors dalla classe base: {base_errors}")
            
            print("[DEBUG] Verifica template completata")
            print(f"[DEBUG] Dati aggiornati: {updated_data}")
            return updated_data, warnings, errors
            
        except Exception as e:
            error_msg = f"Errore durante la verifica del template: {str(e)}"
            print(f"[ERROR] {error_msg}")
            errors.append(error_msg)
            return updated_data, warnings, errors 