"""
Libreria per la gestione del template gastronomia.json
Gestisce le preferenze per le attività gastronomiche
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

class GastronomiaTemplate:
    def __init__(self, template_name="gastronomia"):
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
            with open("template/gastronomia.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()


    def validate_degustazione(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida le degustazioni usando l'embedding per trovare corrispondenze nel database
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            if 'degustazioni' not in data or not data['degustazioni']:
                return True, "Le degustazioni sono opzionali", corrected_data

            # Converti in lista se è una stringa singola
            degustazioni_list = data['degustazioni'] if isinstance(data['degustazioni'], list) else [data['degustazioni']]
            print(f"Verifica degustazioni per: {degustazioni_list}")

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

            degustazioni_corrette = []
            for degustazione in degustazioni_list:
                try:
                    print(f"Generazione embedding per degustazione: '{degustazione}'")
                    degustazione_embedding = self.model.encode(degustazione)
                    print(f"Embedding generato con successo, dimensione: {len(degustazione_embedding)}")
                    degustazione_embedding = degustazione_embedding.tolist()

                    print("Esecuzione query per trovare la degustazione più simile...")
                    cursor.execute("""
                        SELECT degustazione, embedding_degustazione <=> %s::vector as distanza
                        FROM degustazioni
                        WHERE embedding_degustazione IS NOT NULL
                        ORDER BY distanza ASC
                        LIMIT 1
                    """, (degustazione_embedding,))
                    
                    risultato = cursor.fetchall()
                    print(f"Risultato query: {risultato}")

                    if risultato:
                        degustazione_corretta, distanza = risultato[0]
                        print(f"Distanza trovata: {distanza}")
                        if distanza < 0.4:
                            print(f"Aggiornamento degustazione da '{degustazione}' a '{degustazione_corretta}'")
                            degustazioni_corrette.append(degustazione_corretta)
                        else:
                            print(f"Degustazione '{degustazione}' non ha corrispondenze sufficientemente simili")
                            degustazioni_corrette.append(degustazione)
                    else:
                        print(f"Nessun risultato trovato per la degustazione '{degustazione}'")
                        degustazioni_corrette.append(degustazione)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{degustazione}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    degustazioni_corrette.append(degustazione)

            corrected_data['degustazioni'] = degustazioni_corrette
            print(f"Degustazioni finali: {degustazioni_corrette}")
            return True, "Degustazioni verificate", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica delle degustazioni: {str(e)}")
            return False, f"Errore durante la verifica delle degustazioni: {str(e)}", corrected_data
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
            # Validazione corsi_cucina
            if 'corsi_cucina' in data:
                if not isinstance(data['corsi_cucina'], bool):
                    return False, "Il campo corsi_cucina deve essere un booleano", corrected_data
                corrected_data['corsi_cucina'] = data['corsi_cucina']

            # Validazione degustazioni
            if 'degustazioni' in data:
                is_valid, msg, degustazioni_data = self.validate_degustazione(data)
                if not is_valid:
                    return False, msg, corrected_data
                corrected_data.update(degustazioni_data)
            
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
        
        # Mantieni i booleani come sono
        if 'corsi_cucina' in data:
            processed_data['corsi_cucina'] = data['corsi_cucina']

        # Normalizza le degustazioni
        if 'degustazioni' in data:
            if isinstance(data['degustazioni'], list):
                processed_data['degustazioni'] = [item.strip().lower() for item in data['degustazioni']]
            else:
                processed_data['degustazioni'] = data['degustazioni'].strip().lower()
        
        return processed_data

    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template gastronomia
        
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