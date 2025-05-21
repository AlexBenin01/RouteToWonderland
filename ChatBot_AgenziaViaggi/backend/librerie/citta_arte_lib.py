"""
Libreria per la gestione del template citta_arte.json
Gestisce le preferenze per le attività culturali e artistiche
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
import logging
from .template_manager import TemplateManager
from .base_template import BaseTemplate

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

class CittaArteTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)
    
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
                        SELECT attivita, embedding_attivita <=> %s::vector as distanza
                        FROM attivita_citta
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
        print("[DEBUG] Inizio validazione dati città e arte")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        #template_data = self.get_template_data()
        
        try:
            # Validazione attività usando validate_attivita
            if 'attivita' in data:
                print(f"[DEBUG] Validazione attività: {data['attivita']}")
                is_valid, msg, updated_data = self.validate_attivita(data)
                if not is_valid:
                    print(f"[ERROR] {msg}")
                    corrected_data['attivita'] = []
                    return False, msg, corrected_data
                corrected_data.update(updated_data)
                print(f"[DEBUG] Attività valide: {corrected_data['attivita']}")

            # Gestione guida turistica e lingua
            if 'richiesta_guida_turistica' in data:
                print(f"[DEBUG] Verifica richiesta_guida_turistica: {data['richiesta_guida_turistica']}")
                if data['richiesta_guida_turistica'].lower() == "no":
                    print("[DEBUG] Richiesta guida turistica impostata a no")
                    corrected_data['lingua_guida'] = "no guida"
                    print(f"[DEBUG] Lingua guida impostata a: {corrected_data['lingua_guida']}")
                elif data['richiesta_guida_turistica'].lower() == "si":
                    if 'lingua_guida' not in data or not data['lingua_guida']:
                        print("[ERROR] Lingua guida mancante o non specificata")
                        return False, "La lingua della guida è obbligatoria quando è richiesta una guida turistica", corrected_data
                else:
                    print("[ERROR] Valore non valido per richiesta_guida_turistica")
                    return False, "Il campo richiesta_guida_turistica deve essere 'si' o 'no'", corrected_data
            else:
                print("[ERROR] Campo richiesta_guida_turistica mancante")
                return False, "Il campo richiesta_guida_turistica è obbligatorio", corrected_data

            
            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template città e arte
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        print("[DEBUG] Inizio verifica_template città e arte")
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