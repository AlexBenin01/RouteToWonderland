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
from stdnum.it import codicefiscale
from stdnum import vatin
from stdnum.exceptions import ValidationError
from pathlib import Path
import phonenumbers
from phonenumbers import geocoder
import logging

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



from .template_manager import TemplateManager
from .base_template import BaseTemplate


class ContattiTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
    
    
    
    
    def is_valid_phone_number(self, phone_number: str) -> bool:
        """
        Verifica se il numero di telefono è valido
        """
        print(f"[DEBUG] Verifica numero di telefono: {phone_number}")
        result = phone_number.isdigit() and len(phone_number) == 10
        print(f"[DEBUG] Risultato verifica numero: {result}")
        return result
    
    def is_valid_email(self, email: str) -> bool:
        """
        Verifica se l'email è valida
        """
        print(f"[DEBUG] Verifica email: {email}")
        result = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
        print(f"[DEBUG] Risultato verifica email: {result}")
        return result
    
    def is_valid_codice_fiscale(self, cf_value: str) -> bool:
        """
        Verifica se il codice fiscale è valido
        
        Args:
            cf_value: Il codice fiscale da verificare
            
        Returns:
            bool: True se il codice fiscale è valido, False altrimenti
        """
        try:
            # Rimuovi spazi e converti in maiuscolo
            cf_value = cf_value.strip().upper()
            # Verifica se il codice fiscale è valido
            return codicefiscale.is_valid(cf_value)
        except ValidationError as e:
            print("Codice non valido:", e)
            return False

    def is_valid_partita_iva(self, piva: str) -> bool:
        """
        Verifica se la partita IVA è valida
        
        Args:
            piva: La partita IVA da verificare
            
        Returns:
            bool: True se la partita IVA è valida, False altrimenti
        """
        try:
            print(f"[DEBUG] Verifica partita IVA: {piva}")
            # Rimuovi spazi
            piva = vatin.compact(piva)
            print(f"[DEBUG] Partita IVA normalizzata: {piva}")
            # Verifica partita IVA
            result = vatin.is_valid(piva)
            print(f"[DEBUG] Risultato verifica partita IVA: {result}")
            return result
        except Exception as e:
            print(f"[ERROR] Errore durante la verifica della partita IVA: {str(e)}")
            return False
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida i dati in input secondo il template
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        print("[DEBUG] Inizio validazione dati contatti")
        print(f"[DEBUG] Dati ricevuti: {data}")
        
        # Crea una copia dei dati originali per il confronto
        corrected_data = data.copy()
        template_data = self.get_template_data()
        
        try:
            # Validazione full_name
            if 'full_name' in data:
                print(f"[DEBUG] Validazione nome: {data['full_name']}")
                if not isinstance(data['full_name'], str):
                    print("[ERROR] Nome non è una stringa")
                    return False, "Il nome deve essere una stringa", corrected_data
                if not data['full_name'].strip():
                    print("[ERROR] Nome vuoto")
                    return False, "Il nome non può essere vuoto", corrected_data
                corrected_data['full_name'] = data['full_name'].strip()
                print(f"[DEBUG] Nome corretto: {corrected_data['full_name']}")

            # Validazione codice_fiscale
            if 'codice_fiscale_o_partita_iva' in data:
                print(f"[DEBUG] Validazione codice fiscale/partita IVA: {data['codice_fiscale_o_partita_iva']}")
                if not isinstance(data['codice_fiscale_o_partita_iva'], str):
                    print("[ERROR] Codice fiscale/partita IVA non è una stringa")
                    return False, "Il codice fiscale o la partita IVA deve essere una stringa", corrected_data
                
                value = data['codice_fiscale_o_partita_iva'].strip()
                print(f"[DEBUG] Valore normalizzato: {value}")
                
                # Verifica se è un codice fiscale o una partita IVA valida
                if self.is_valid_codice_fiscale(value):
                    print("[DEBUG] Validato come codice fiscale")
                    corrected_data['codice_fiscale_o_partita_iva'] = value
                elif self.is_valid_partita_iva(value):
                    print("[DEBUG] Validato come partita IVA")
                    corrected_data['codice_fiscale_o_partita_iva'] = vatin.compact(value)
                else:
                    print("[ERROR] Valore non valido come codice fiscale o partita IVA")
                    corrected_data['codice_fiscale_o_partita_iva'] = ""
                    return False, "Il valore inserito non è un codice fiscale o una partita IVA valida", corrected_data

            # Validazione numero_cellulare
            if 'numero_cellulare' in data:
                print(f"[DEBUG] Validazione numero cellulare: {data['numero_cellulare']}")
                if not isinstance(data['numero_cellulare'], str):
                    print("[ERROR] Numero cellulare non è una stringa")
                    corrected_data['numero_cellulare'] = ""
                    return False, "Il numero di cellulare deve essere una stringa", corrected_data
                
                try:
                    # Aggiungi il prefisso + se non presente
                    phone_number = data['numero_cellulare']
                    if not phone_number.startswith('+'):
                        phone_number = '+' + phone_number
                    
                    # Parsa il numero
                    parsed_number = phonenumbers.parse(phone_number)
                    print(f"[DEBUG] Numero cellulare parsato: {parsed_number}")
                    
                    # Verifica se il numero è valido
                    if not phonenumbers.is_valid_number(parsed_number):
                        print("[ERROR] Numero cellulare non valido")
                        corrected_data['numero_cellulare'] = ""
                        return False, "Il numero di cellulare non è valido", corrected_data
                    
                    # Ottieni il nome del paese
                    country_name = phonenumbers.geocoder.description_for_number(parsed_number, "it")
                    print(f"[DEBUG] Paese rilevato: {country_name}")
                    
                    # Formatta il numero nel formato internazionale
                    formatted_number = phonenumbers.format_number(
                        parsed_number, 
                        phonenumbers.PhoneNumberFormat.INTERNATIONAL
                    )
                    
                    # Aggiungi il nome del paese, se non disponibile usa "Italia" come default
                    if not country_name:
                        country_name = "Italia"
                        print("[DEBUG] Nessun paese rilevato, uso Italia come default")
                    
                    corrected_data['numero_cellulare'] = f"{formatted_number} ({country_name})"
                    print(f"[DEBUG] Numero cellulare corretto: {corrected_data['numero_cellulare']}")
                except phonenumbers.NumberParseException as e:
                    print(f"[ERROR] Errore nel parsing del numero: {str(e)}")
                    corrected_data['numero_cellulare'] = ""
                    return False, "Il numero di cellulare non è valido", corrected_data

            # Validazione email
            if 'email' in data:
                print(f"[DEBUG] Validazione email: {data['email']}")
                if not isinstance(data['email'], str):
                    print("[ERROR] Email non è una stringa")
                    corrected_data['email'] = ""
                    return False, "L'email deve essere una stringa", corrected_data
                
                email = data['email'].lower().strip()
                print(f"[DEBUG] Email normalizzata: {email}")
                if not self.is_valid_email(email):
                    print("[ERROR] Formato email non valido")
                    corrected_data['email'] = ""
                    return False, "Formato email non valido", corrected_data
                corrected_data['email'] = email
                print(f"[DEBUG] Email corretta: {corrected_data['email']}")
            
            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template contatti
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        print("[DEBUG] Inizio verifica_template contatti")
        print(f"[DEBUG] Dati ricevuti: {data}")
        warnings = []
        errors = []
        original_data = data.copy()
        updated_data = data.copy()
        try:
            
            # 4. Chiama il metodo della classe base per la validazione standard
            updated_data, base_warnings, base_errors = super().verifica_template(updated_data)
            warnings.extend(base_warnings)
            errors.extend(base_errors)

            data_was_different = self.are_data_different(original_data, updated_data)
            #verifica se è completo
            template_completo = all(
                campo in updated_data and (
                    updated_data[campo] is not None and 
                    (isinstance(updated_data[campo], bool) or updated_data[campo])
                )
                for campo in self.get_template_data().keys()
            )
            print(f"[DEBUG] Template completo: {template_completo}")
            
            # Se il template è completo, imposta data_was_different a True
            if template_completo:
                data_was_different = True
                print("[DEBUG] Template completo, data_was_different impostato a True")
            
            return updated_data, data_was_different, warnings, errors
            
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            data_was_different = self.are_data_different(original_data, updated_data)
            return updated_data, data_was_different, warnings, errors