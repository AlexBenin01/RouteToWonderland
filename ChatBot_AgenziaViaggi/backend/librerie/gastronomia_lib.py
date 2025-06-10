"""
Libreria per la gestione del template gastronomia.json
Gestisce le informazioni relative alle attività gastronomiche
"""

import json
from typing import Dict, Any, Tuple, List
from datetime import datetime
import re
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from pathlib import Path
from .template_manager import TemplateManager
from .base_template import BaseTemplate
from .database import get_db_connection, release_connection


class GastronomiaTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)


    def validate_degustazione(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica il tipo di degustazione usando gli embedding.
        Controlla che il tipo di degustazione inserito corrisponda a un tipo valido nel database.
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """

        corrected_data = {}
        try:
            if 'degustazioni' not in data or not data['degustazioni']:
                return True, "Le degustazioni sono opzionali", data

            # Converti in lista se è una stringa singola
            degustazione_list = data['degustazioni'] if isinstance(data['degustazioni'], list) else [data['degustazioni']]
            print(f"Verifica degustazioni per: {degustazione_list}")

            print("Tentativo di connessione al database...")
            conn = get_db_connection()
            print("Connessione al database stabilita con successo")
            cursor = conn.cursor()

            degustazione_corrette = []
            for degustazione in degustazione_list:
                try:
                    print(f"Generazione embedding per attività: '{degustazione}'")
                    degustazione_embedding = self.model.encode(degustazione)
                    print(f"Embedding generato con successo, dimensione: {len(degustazione_embedding)}")
                    # Converti l'array NumPy in lista
                    degustazione_embedding = degustazione_embedding.tolist()

                    print("Esecuzione query per trovare il tipo di degustazione più simile...")
                    cursor.execute("""
                        SELECT degustazione, embedding_degustazione <=> %s::vector as distanza
                        FROM degustazione
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
                            print(f"Aggiornamento degustazione da '{data['degustazioni']}' a '{degustazione_corretta}'")
                            degustazione_corrette.append(degustazione_corretta)
                        else:
                            print(f"Degustazione '{degustazione}' non ha corrispondenze sufficientemente simili")
                            degustazione_corrette.append(None)
                    else:
                        print(f"Nessun risultato trovato per la degustazione '{degustazione}'")
                        degustazione_corrette.append(None)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{degustazione}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    degustazione_corrette.append(None)

            # Rimuovi i None dalla lista
            degustazione_corrette = [a for a in degustazione_corrette if a is not None]
            corrected_data['degustazioni'] = degustazione_corrette if degustazione_corrette else None
            print(f"Degustazioni finali: {degustazione_corrette}")
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
        print("[DEBUG] Inizio validazione dati gastronomia")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        template_data = self.get_template_data()
        
        try:
            # Validazione corsi_cucina (booleano)
            if 'corsi_cucina' in data:
                print(f"[DEBUG] Validazione corsi_cucina: {data['corsi_cucina']}")
                if not isinstance(data['corsi_cucina'], bool):
                    print(f"[ERROR] corsi_cucina non è un booleano: {data['corsi_cucina']}")
                    corrected_data['corsi_cucina'] = None
                    return False, "Il campo corsi_cucina deve essere un booleano (true/false)", corrected_data
                print(f"[DEBUG] corsi_cucina valido: {data['corsi_cucina']}")
                corrected_data['corsi_cucina'] = data['corsi_cucina']

            # Validazione degustazioni usando validate_degustazione
            if 'degustazioni' in data:
                print(f"[DEBUG] Validazione degustazioni: {data['degustazioni']}")
                is_valid, error_msg, updated_data = self.validate_degustazione(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione degustazioni fallita: {error_msg}")
                    return False, error_msg, corrected_data
                # Aggiorna solo il campo degustazioni
                corrected_data['degustazioni'] = updated_data.get('degustazioni')
                print(f"[DEBUG] degustazioni validata con successo: {corrected_data['degustazioni']}")

            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
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
        original_data = data.copy()
        # Inizializza updated_data con tutti i campi del template, impostando quelli mancanti a None
        updated_data = {campo: None for campo in self.get_template_data().keys()}
        # Aggiorna con i dati ricevuti
        updated_data.update(data)
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