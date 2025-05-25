"""
Libreria per la gestione del template famiglia.json
Gestisce le preferenze per le attività familiari
"""

import json
from typing import Dict, Any, Tuple, List
from datetime import datetime
import re
from .template_manager import TemplateManager
from .base_template import BaseTemplate

class FamigliaTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.template_name = "famiglia"
    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Template {self.template_name} non trovato, uso il template di default")
            with open("template/famiglia.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida i dati in input secondo il template
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        print("[DEBUG] Inizio validazione dati famiglia")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        
        try:
            # Validazione adulti
            if 'adulti' in data:
                print(f"[DEBUG] Validazione adulti: {data['adulti']}")
                if not isinstance(data['adulti'], int) or data['adulti'] < 0:
                    print(f"[ERROR] adulti non valido: {data['adulti']}")
                    corrected_data.pop('adulti', None)
                else:
                    print(f"[DEBUG] adulti validato con successo: {data['adulti']}")

            # Validazione bambini
            if 'bambini' in data:
                print(f"[DEBUG] Validazione bambini: {data['bambini']}")
                if not isinstance(data['bambini'], int) or data['bambini'] < 0:
                    print(f"[ERROR] bambini non valido: {data['bambini']}")
                    corrected_data.pop('bambini', None)
                else:
                    print(f"[DEBUG] bambini validato con successo: {data['bambini']}")
            
            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template famiglia
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        print("[DEBUG] Inizio verifica_template famiglia")
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
