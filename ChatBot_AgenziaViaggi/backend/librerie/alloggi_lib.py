"""
Libreria per la gestione del template alloggi.json
Gestisce le preferenze e i requisiti per l'alloggio
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

class AlloggiTemplate:
    def __init__(self, template_name="alloggi"):
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
            with open("template/alloggi.json", 'r', encoding='utf-8') as f:
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
        corrected_data = {}
        
        try:
            # Validazione tipo_alloggio
            if 'tipo_alloggio' not in data or not data['tipo_alloggio']:
                return False, "Il tipo di alloggio è obbligatorio", corrected_data

            print(f"Verifica alloggio per: {data['tipo_alloggio']}")
            
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

            try:
                print("Generazione embedding con modello locale...")
                print(f"Testo da convertire in embedding: '{data['tipo_alloggio']}'")
                # Genera l'embedding per il tipo di alloggio
                alloggio_embedding = self.model.encode(data['tipo_alloggio'])
                print(f"Embedding generato con successo, dimensione: {len(alloggio_embedding)}")
                # Converti l'array NumPy in lista
                alloggio_embedding = alloggio_embedding.tolist()
            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                raise

            print("Esecuzione query per trovare l'alloggio più simile...")
            cursor.execute("""
                SELECT nome, embedding_alloggi <=> %s::vector as distanza
                FROM alloggi
                WHERE embedding_alloggi IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
            """, (alloggio_embedding,))
            
            risultato = cursor.fetchall()
            print(f"Risultato query: {risultato}")
            
            if risultato:
                alloggio_corretto, distanza = risultato[0]
                print(f"Distanza trovata: {distanza}")
                if distanza > 0.4:
                    print(f"Distanza troppo grande ({distanza} > 0.4), rimuovo il valore")
                    return False, "Nessun alloggio simile trovato nel database", corrected_data
                
                print(f"Aggiornamento alloggio da '{data['tipo_alloggio']}' a '{alloggio_corretto}'")
                corrected_data['tipo_alloggio'] = alloggio_corretto
                return True, "Alloggio verificato e corretto", corrected_data
            else:
                print("Nessun risultato trovato nel database")
                return False, "Nessun alloggio trovato nel database", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica dell'alloggio: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            return False, f"Errore durante la verifica dell'alloggio: {str(e)}", corrected_data
        finally:
            if 'cursor' in locals():
                print("Chiusura cursor")
                cursor.close()
            if 'conn' in locals():
                print("Chiusura connessione")
                conn.close()
    
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elabora i dati secondo le regole del template
        
        Args:
            data: Dizionario contenente i dati da elaborare
            
        Returns:
            Dict[str, Any]: Dati elaborati
        """
        processed_data = {}
        
        # Normalizza il tipo di alloggio
        if 'tipo_alloggio' in data:
            if isinstance(data['tipo_alloggio'], str):
                processed_data['tipo_alloggio'] = data['tipo_alloggio'].strip().lower()
            elif isinstance(data['tipo_alloggio'], list):
                processed_data['tipo_alloggio'] = [item.strip().lower() for item in data['tipo_alloggio']]
            else:
                processed_data['tipo_alloggio'] = data['tipo_alloggio']
        
        return processed_data

    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template alloggi
        
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