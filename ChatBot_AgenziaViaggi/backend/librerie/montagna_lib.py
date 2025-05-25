"""
Libreria per la gestione del template montagna.json
Gestisce le preferenze per le attività montane
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

class MontagnaTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.template_name = "montagna"
        self.template_path = f"template/{self.template_name}.json"
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
            with open("template/montagna.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def validate_attivita_montagna(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida le attività montane usando l'embedding per trovare corrispondenze nel database.
        Verifica che le attività inserite corrispondano a quelle disponibili nel database.
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            if 'attivita' not in data or not data['attivita']:
                return True, "Le attività montane sono opzionali", corrected_data

            # Converti in lista se è una stringa singola
            attivita_list = data['attivita'] if isinstance(data['attivita'], list) else [data['attivita']]
            print(f"Verifica attività montane per: {attivita_list}")

            print("Tentativo di connessione al database...")
            conn = psycopg2.connect(
                dbname="routeToWonderland",
                user="postgres",
                password="admin",
                host="localhost",
                port=5432
            )
            print("Connessione al database stabilita con successo")
            cursor = conn.cursor()

            attivita_corrette = []
            for attivita in attivita_list:
                try:
                    print(f"Generazione embedding per attività montana: '{attivita}'")
                    attivita_embedding = self.model.encode(attivita)
                    print(f"Embedding generato con successo, dimensione: {len(attivita_embedding)}")
                    attivita_embedding = attivita_embedding.tolist()

                    print("Esecuzione query per trovare l'attività montana più simile...")
                    cursor.execute("""
                        SELECT attivita, embedding_attivita <=> %s::vector as distanza
                        FROM attivita_montagna
                        WHERE embedding_attivita IS NOT NULL
                        ORDER BY distanza ASC
                        LIMIT 1
                    """, (attivita_embedding,))
                    
                    risultato = cursor.fetchall()
                    print(f"Risultato query: {risultato}")

                    if risultato:
                        attivita_corretta, distanza = risultato[0]
                        print(f"Distanza trovata: {distanza}")
                        if distanza < 0.4:
                            print(f"Aggiornamento attività da '{attivita}' a '{attivita_corretta}'")
                            attivita_corrette.append(attivita_corretta)
                        else:
                            print(f"Attività montana '{attivita}' non ha corrispondenze sufficientemente simili")
                            attivita_corrette.append(attivita)
                    else:
                        print(f"Nessun risultato trovato per l'attività montana '{attivita}'")
                        attivita_corrette.append(attivita)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{attivita}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    attivita_corrette.append(attivita)

            corrected_data['attivita'] = attivita_corrette
            print(f"Attività montane finali: {attivita_corrette}")
            return True, "Attività montane verificate con successo", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica delle attività montane: {str(e)}")
            return False, f"Errore durante la verifica delle attività montane: {str(e)}", corrected_data
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida i dati in input secondo il template
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        print("[DEBUG] Inizio validazione dati montagna")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        
        try:
            # Validazione attivita usando validate_attivita_montagna
            if 'attivita' in data:
                print(f"[DEBUG] Validazione attivita: {data['attivita']}")
                is_valid, error_msg, corrected_data = self.validate_attivita_montagna(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione attivita fallita: {error_msg}")
                    return False, error_msg, corrected_data
                print(f"[DEBUG] attivita validata con successo: {corrected_data['attivita']}")
            

             # Mantieni il valore di attrezzatura se presente
            if 'attrezzatura' in data:
                corrected_data['attrezzatura'] = data['attrezzatura']
                # Se attrezzatura è valorizzata, copia lo stesso valore in attrezzatura_menzionata
                if data['attrezzatura'] is not None:
                    corrected_data['attrezzatura_menzionata'] = data['attrezzatura']
            
            
            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template montagna
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        print("[DEBUG] Inizio verifica_template montagna")
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