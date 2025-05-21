"""
Libreria per la gestione del template contatti.json
Gestisce le informazioni di contatto dell'utente
"""

import json
from typing import Dict, Any, Tuple, List
from datetime import datetime
import re
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from codicefiscale import codicefiscale
from stdnum.it import vat
from pathlib import Path

class ContattiTemplate:
    def __init__(self, template_name="contatti"):
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)
    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Template {self.template_name} non trovato, uso il template di default")
            with open("template/contatti.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def is_valid_phone_number(self, phone_number: str) -> bool:
        """
        Verifica se il numero di telefono è valido
        """
        return phone_number.isdigit() and len(phone_number) == 10
    
    def is_valid_email(self, email: str) -> bool:
        """
        Verifica se l'email è valida
        """
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    
    def is_valid_codice_fiscale(self, cf: str) -> bool:
        """
        Verifica se il codice fiscale è valido
        
        Args:
            cf: Il codice fiscale da verificare
            
        Returns:
            bool: True se il codice fiscale è valido, False altrimenti
        """
        # Rimuovi spazi
        cf = cf.strip()
        # Verifica se il codice fiscale è valido
        return codicefiscale.is_valid(cf)

    def is_valid_partita_iva(self, piva: str) -> bool:
        """
        Verifica se la partita IVA è valida
        
        Args:
            piva: La partita IVA da verificare
            
        Returns:
            bool: True se la partita IVA è valida, False altrimenti
        """
        # Rimuovi spazi
        piva = vat.compact(piva)
        
        # Verifica partita IVA
        return vat.is_valid(piva)

    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida i dati in input secondo il template
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            # Validazione full_name
            if 'full_name' in data:
                if not isinstance(data['full_name'], str):
                    return False, "Il nome deve essere una stringa", corrected_data
                if not data['full_name'].strip():
                    return False, "Il nome non può essere vuoto", corrected_data
                corrected_data['full_name'] = data['full_name'].strip()

            # Validazione codice_fiscale
            if 'codice_fiscale_o_partita_iva' in data:
                if not isinstance(data['codice_fiscale_o_partita_iva'], str):
                    return False, "Il codice fiscale o la partita IVA deve essere una stringa", corrected_data
                
                value = data['codice_fiscale_o_partita_iva'].strip()
                
                # Verifica se è un codice fiscale o una partita IVA valida
                if self.is_valid_codice_fiscale(value):
                    corrected_data['codice_fiscale_o_partita_iva'] = value
                elif self.is_valid_partita_iva(value):
                    corrected_data['codice_fiscale_o_partita_iva'] = vat.compact(value)
                else:
                    return False, "Il valore inserito non è un codice fiscale o una partita IVA valida", corrected_data

            # Validazione numero_cellulare
            if 'numero_cellulare' in data:
                if not isinstance(data['numero_cellulare'], str):
                    return False, "Il numero di cellulare deve essere una stringa", corrected_data
                
                # Rimuovi spazi e caratteri non numerici
                phone = re.sub(r'[^\d]', '', data['numero_cellulare'])
                
                if not self.is_valid_phone_number(phone):
                    return False, "Formato numero di cellulare non valido", corrected_data
                corrected_data['numero_cellulare'] = phone

            # Validazione email
            if 'email' in data:
                if not isinstance(data['email'], str):
                    return False, "L'email deve essere una stringa", corrected_data
                
                email = data['email'].lower().strip()
                if not self.is_valid_email(email):
                    return False, "Formato email non valido", corrected_data
                corrected_data['email'] = email
            
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora i dati secondo le regole del template
        
        Args:
            data: Dizionario contenente i dati da elaborare
            
        Returns:
            Dict[str, Any]: Dati elaborati
        """
        processed_data = {}
        
        # Normalizza nome e cognome
        for field in ['full_name']:
            if field in data:
                if isinstance(data[field], str):
                    processed_data[field] = data[field].strip()
                else:
                    processed_data[field] = data[field]

        # Normalizza codice fiscale
        if 'codice_fiscale' in data:
            if isinstance(data['codice_fiscale'], str):
                processed_data['codice_fiscale'] = data['codice_fiscale'].upper().strip()
            else:
                processed_data['codice_fiscale'] = data['codice_fiscale']

        # Normalizza numero cellulare
        if 'numero_cellulare' in data:
            if isinstance(data['numero_cellulare'], str):
                # Rimuovi spazi e caratteri non numerici
                processed_data['numero_cellulare'] = re.sub(r'[^\d+]', '', data['numero_cellulare'])
            else:
                processed_data['numero_cellulare'] = data['numero_cellulare']

        # Normalizza email
        if 'email' in data:
            if isinstance(data['email'], str):
                processed_data['email'] = data['email'].lower().strip()
            else:
                processed_data['email'] = data['email']
        
        return processed_data

    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template contatti
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        warnings = []
        errors = []
        updated_data = data.copy()
        
        try:
            # Verifica e normalizza i dati
            updated_data = self.process_data(updated_data)
            
            # Verifica la validità dei dati
            is_valid, msg, updated_data = self.validate_data(updated_data)
            if not is_valid:
                errors.append(msg)
            
            return updated_data, warnings, errors 
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            return updated_data, warnings, errors 