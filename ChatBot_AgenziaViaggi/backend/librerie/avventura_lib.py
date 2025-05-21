"""
Libreria per la gestione del template avventura.json
Gestisce le preferenze e i requisiti per le attività di avventura
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

class AvventuraTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)
    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Template {self.template_name} non trovato, uso il template di default")
            with open("template/avventura.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def validate_difficolta(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida il livello di difficoltà
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            if 'livello_difficolta' not in data or not data['livello_difficolta']:
                return True, "Il livello di difficoltà mancante", corrected_data

            print(f"Verifica livello di difficoltà per: {data['livello_difficolta']}")

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
                print(f"Generazione embedding per difficoltà: '{data['livello_difficolta']}'")
                difficolta_embedding = self.model.encode(data['livello_difficolta'])
                print(f"Embedding generato con successo, dimensione: {len(difficolta_embedding)}")
                difficolta_embedding = difficolta_embedding.tolist()

                print("Esecuzione query per trovare il livello di difficoltà più simile...")
                cursor.execute("""
                    SELECT difficolta, embedding_difficolta <=> %s::vector as distanza
                    FROM difficolta
                    WHERE embedding_difficolta IS NOT NULL
                    ORDER BY distanza ASC
                    LIMIT 1
                """, (difficolta_embedding,))
                
                risultato = cursor.fetchall()
                print(f"Risultato query: {risultato}")

                if risultato:
                    difficolta_corretta, distanza = risultato[0]
                    print(f"Distanza trovata: {distanza}")
                    if distanza < 0.4:
                        print(f"Aggiornamento difficoltà da '{data['livello_difficolta']}' a '{difficolta_corretta}'")
                        corrected_data['livello_difficolta'] = difficolta_corretta
                        return True, "Livello di difficoltà verificato", corrected_data
                    else:
                        print(f"Livello di difficoltà '{data['livello_difficolta']}' non ha corrispondenze sufficientemente simili")
                        return False, "Livello di difficoltà non valido", corrected_data
                else:
                    print(f"Nessun risultato trovato per il livello di difficoltà '{data['livello_difficolta']}'")
                    return False, "Livello di difficoltà non valido", corrected_data

            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                return False, f"Errore durante la verifica del livello di difficoltà: {str(e)}", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica del livello di difficoltà: {str(e)}")
            return False, f"Errore durante la verifica del livello di difficoltà: {str(e)}", corrected_data
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def validate_attivita(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida le attività usando l'embedding per trovare corrispondenze nel database
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            if 'attivita' not in data or not data['attivita']:
                return True, "Le attività sono opzionali", corrected_data

            # Converti in lista se è una stringa singola
            attivita_list = data['attivita'] if isinstance(data['attivita'], list) else [data['attivita']]
            print(f"Verifica attività per: {attivita_list}")

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
                    print(f"Generazione embedding per attività: '{attivita}'")
                    attivita_embedding = self.model.encode(attivita)
                    print(f"Embedding generato con successo, dimensione: {len(attivita_embedding)}")
                    # Converti l'array NumPy in lista
                    attivita_embedding = attivita_embedding.tolist()

                    print("Esecuzione query per trovare l'attività più simile...")
                    cursor.execute("""
                        SELECT attivita embedding_attivita <=> %s::vector as distanza
                        FROM attivita_avventura
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
                            print(f"Attività '{attivita}' non ha corrispondenze sufficientemente simili")
                            attivita_corrette.append(attivita)
                    else:
                        print(f"Nessun risultato trovato per l'attività '{attivita}'")
                        attivita_corrette.append(attivita)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{attivita}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    attivita_corrette.append(attivita)

            corrected_data['attivita'] = attivita_corrette
            print(f"Attività finali: {attivita_corrette}")
            return True, "Attività verificate", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica delle attività: {str(e)}")
            return False, f"Errore durante la verifica delle attività: {str(e)}", corrected_data
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
        print("[DEBUG] Inizio validazione dati avventura")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        
        try:
            # Validazione attivita usando validate_attivita
            if 'attivita' in data:
                print(f"[DEBUG] Validazione attivita: {data['attivita']}")
                is_valid, error_msg, corrected_data = self.validate_attivita(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione attivita fallita: {error_msg}")
                    return False, error_msg, corrected_data
                print(f"[DEBUG] attivita validata con successo: {corrected_data['attivita']}")

            # Validazione livello_difficoltà usando validate_difficolta
            if 'livello_difficoltà' in data:
                print(f"[DEBUG] Validazione livello_difficoltà: {data['livello_difficoltà']}")
                is_valid, error_msg, corrected_data = self.validate_difficolta(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione livello_difficoltà fallita: {error_msg}")
                    return False, error_msg, corrected_data
                print(f"[DEBUG] livello_difficoltà validato con successo: {corrected_data['livello_difficoltà']}")

            # Validazione attrezzatura_necessaria (solo verifica inizializzazione)
            if 'attrezzatura_necessaria' in data:
                print(f"[DEBUG] Verifica attrezzatura_necessaria: {data['attrezzatura_necessaria']}")
                if data['attrezzatura_necessaria'] is None:
                    print(f"[ERROR] attrezzatura_necessaria non inizializzato")
                    return False, "Il campo attrezzatura_necessaria deve essere inizializzato", corrected_data
                print(f"[DEBUG] attrezzatura_necessaria inizializzato: {data['attrezzatura_necessaria']}")

            # Validazione guida_esperta e gestione lingua_guida
            if 'guida_esperta' in data:
                print(f"[DEBUG] Validazione guida_esperta: {data['guida_esperta']}")
                if not isinstance(data['guida_esperta'], bool):
                    print(f"[ERROR] guida_esperta non è un booleano: {data['guida_esperta']}")
                    corrected_data['guida_esperta'] = False
                    return False, "Il campo guida_esperta deve essere un booleano (true/false)", corrected_data
                
                # Se guida_esperta è false, imposta lingua_guida a "no guida"
                if not data['guida_esperta']:
                    print("[DEBUG] guida_esperta è false, imposto lingua_guida a 'no guida'")
                    corrected_data['lingua_guida'] = "no guida"
                print(f"[DEBUG] guida_esperta valido: {data['guida_esperta']}")

            # Verifica lingua_guida
            if 'lingua_guida' in data:
                print(f"[DEBUG] Verifica lingua_guida: {data['lingua_guida']}")
                if not data['lingua_guida'] or data['lingua_guida'].strip() == "":
                    print(f"[ERROR] lingua_guida è vuoto")
                    if corrected_data.get('guida_esperta', False):
                        return False, "Il campo lingua_guida è obbligatorio quando è richiesta una guida", corrected_data
                    else:
                        corrected_data['lingua_guida'] = "no guida"
                print(f"[DEBUG] lingua_guida valido: {data['lingua_guida']}")

            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
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
            # Chiama il metodo della classe base per la validazione standard
            updated_data, base_warnings, base_errors = super().verifica_template(updated_data)
            warnings.extend(base_warnings)
            errors.extend(base_errors)
            
            return updated_data, warnings, errors
            
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            return updated_data, warnings, errors 