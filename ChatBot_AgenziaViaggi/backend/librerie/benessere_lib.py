"""
Libreria per la gestione del template benessere.json
Gestisce le preferenze per i trattamenti di benessere
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

class BenessereTemplate:
    def __init__(self, template_name="benessere"):
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
            with open("template/benessere.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def validate_trattamenti(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica i trattamenti usando gli embedding.
        Gestisce sia un singolo trattamento che una lista di trattamenti.
        Utilizza la tabella trattamenti per trovare corrispondenze semantiche.
        """
        corrected_data = {}
        
        try:
            if 'trattamenti' not in data or not data['trattamenti']:
                return True, "I trattamenti sono opzionali", corrected_data

            # Converti in lista se è una stringa singola
            trattamenti_list = data['trattamenti'] if isinstance(data['trattamenti'], list) else [data['trattamenti']]
            print(f"Verifica trattamenti per: {trattamenti_list}")

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

            trattamenti_corretti = []
            for trattamento in trattamenti_list:
                try:
                    print(f"Generazione embedding per trattamento: '{trattamento}'")
                    trattamento_embedding = self.model.encode(trattamento)
                    print(f"Embedding generato con successo, dimensione: {len(trattamento_embedding)}")
                    trattamento_embedding = trattamento_embedding.tolist()

                    print("Esecuzione query per trovare il trattamento più simile...")
                    cursor.execute("""
                        SELECT trattamento, embedding_trattamento <=> %s::vector as distanza
                        FROM trattamenti
                        WHERE embedding_trattamento IS NOT NULL
                        ORDER BY distanza ASC
                        LIMIT 1
                    """, (trattamento_embedding,))
                    
                    risultato = cursor.fetchall()
                    print(f"Risultato query: {risultato}")

                    if risultato:
                        trattamento_corretto, distanza = risultato[0]
                        print(f"Distanza trovata: {distanza}")
                        if distanza < 0.4:
                            print(f"Aggiornamento trattamento da '{trattamento}' a '{trattamento_corretto}'")
                            trattamenti_corretti.append(trattamento_corretto)
                        else:
                            print(f"Trattamento '{trattamento}' non ha corrispondenze sufficientemente simili")
                            trattamenti_corretti.append(trattamento)
                    else:
                        print(f"Nessun risultato trovato per il trattamento '{trattamento}'")
                        trattamenti_corretti.append(trattamento)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{trattamento}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    trattamenti_corretti.append(trattamento)

            corrected_data['trattamenti'] = trattamenti_corretti
            print(f"Trattamenti finali: {trattamenti_corretti}")
            return True, "Trattamenti verificati", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica dei trattamenti: {str(e)}")
            return False, f"Errore durante la verifica dei trattamenti: {str(e)}", corrected_data
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
        corrected_data = {}
        
        try:
            # Validazione tipo_benessere
            if 'trattamenti' in data:
                is_valid, msg, trattamenti_data = self.validate_trattamenti(data)
                if not is_valid:
                    return False, msg, corrected_data
                corrected_data.update(trattamenti_data)

        
            
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    


    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template benessere
        
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