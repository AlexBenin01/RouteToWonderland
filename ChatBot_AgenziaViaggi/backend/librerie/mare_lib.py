"""
Libreria per la gestione del template mare.json
Gestisce le preferenze per le attività balneari
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

class MareTemplate:
    def __init__(self, template_name="mare"):
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
            with open("template/mare.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def validate_attivita_mare(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida le attività marine usando l'embedding per trovare corrispondenze nel database
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            if 'attivita' not in data or not data['attivita']:
                return True, "Le attività marine sono opzionali", corrected_data

            # Converti in lista se è una stringa singola
            attivita_list = data['attivita'] if isinstance(data['attivita'], list) else [data['attivita']]
            print(f"Verifica attività marine per: {attivita_list}")

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
                    print(f"Generazione embedding per attività marina: '{attivita}'")
                    attivita_embedding = self.model.encode(attivita)
                    print(f"Embedding generato con successo, dimensione: {len(attivita_embedding)}")
                    # Converti l'array NumPy in lista
                    attivita_embedding = attivita_embedding.tolist()

                    print("Esecuzione query per trovare l'attività marina più simile...")
                    cursor.execute("""
                        SELECT attivita, embedding_attivita <=> %s::vector as distanza
                        FROM attivita_mare
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
                            print(f"Attività marina '{attivita}' non ha corrispondenze sufficientemente simili")
                            attivita_corrette.append(attivita)
                    else:
                        print(f"Nessun risultato trovato per l'attività marina '{attivita}'")
                        attivita_corrette.append(attivita)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{attivita}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    attivita_corrette.append(attivita)

            corrected_data['attivita'] = attivita_corrette
            print(f"Attività marine finali: {attivita_corrette}")
            return True, "Attività marine verificate", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica delle attività marine: {str(e)}")
            return False, f"Errore durante la verifica delle attività marine: {str(e)}", corrected_data
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
        try:
            corrected_data = data.copy()

            # Validazione attrezzatura
            if 'attrezzatura' in data:
                if not isinstance(data['attrezzatura'], bool):
                    return False, "Il campo attrezzatura deve essere un booleano", corrected_data

            # Validazione attività_acquatiche
            if 'attività_acquatiche' in data:
                valid_activities = self.template_data['attività_acquatiche']['enum']
                if not isinstance(data['attività_acquatiche'], list):
                    return False, "Le attività acquatiche devono essere specificate come lista", corrected_data
                if not all(activity.lower() in [a.lower() for a in valid_activities] for activity in data['attività_acquatiche']):
                    return False, f"Una o più attività acquatiche non valide. Valori accettati: {', '.join(valid_activities)}", corrected_data
                corrected_data['attività_acquatiche'] = [activity.lower() for activity in data['attività_acquatiche']]
            
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
        corrected_data = {}
        
        try:
            # Mantieni i booleani come sono
            if 'attrezzatura' in data:
                corrected_data['attrezzatura'] = data['attrezzatura']


                # Validazione attività
                if 'attivita' in data:
                    is_valid, msg, attivita_data = self.validate_attivita(data)
                    if not is_valid:
                        return False, msg, corrected_data
                    corrected_data.update(attivita_data)
            
                return True, "Dati validi", corrected_data
                
        except Exception as e:
            return False, f"Errore durante la validazione: {str(e)}", corrected_data

    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template mare
        
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