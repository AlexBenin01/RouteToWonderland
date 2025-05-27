"""
Libreria per la gestione del template gastronomia.json
Gestisce le informazioni relative alle attività gastronomiche
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


class GastronomiaTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)


    def validate_degustazione(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica il tipo di degustazione usando gli embedding.
        Controlla che il tipo di degustazione inserito corrisponda a un tipo valido nel database.
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        try:
            if 'degustazione' not in data or not data['degustazione']:
                print("Tipo degustazione mancante o vuoto")
                return False, "Il tipo di degustazione è obbligatorio", data

            print(f"Verifica tipo degustazione: {data['degustazione']}")
            
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
                print("Generazione embedding per il tipo di degustazione...")
                print(f"Testo da convertire in embedding: '{data['degustazione']}'")
                degustazione_embedding = self.model.encode(data['degustazione'])
                print(f"Embedding generato con successo, dimensione: {len(degustazione_embedding)}")
                degustazione_embedding = degustazione_embedding.tolist()
            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                raise

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
                tipo_degustazione_corretto, distanza = risultato[0]
                print(f"Distanza trovata: {distanza}")
                if distanza > 0.4:
                    print(f"Distanza troppo grande ({distanza} > 0.4), rimuovo il valore")
                    data['degustazione'] = None
                    return False, "Nessun tipo di degustazione simile trovato nel database", data
                
                print(f"Aggiornamento tipo degustazione da '{data['degustazione']}' a '{tipo_degustazione_corretto}'")
                data['degustazione'] = tipo_degustazione_corretto
                return True, "Tipo di degustazione verificato e corretto", data
            else:
                print("Nessun risultato trovato nel database, rimuovo il valore")
                data['degustazione'] = None
                return False, "Nessun tipo di degustazione trovato nel database", data

        except Exception as e:
            print(f"Errore durante la verifica del tipo di degustazione: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            return False, f"Errore durante la verifica del tipo di degustazione: {str(e)}", data
        finally:
            if 'cursor' in locals():
                print("Chiusura cursor")
                cursor.close()
            if 'conn' in locals():
                print("Chiusura connessione")
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
                    corrected_data['corsi_cucina'] = False
                    return False, "Il campo corsi_cucina deve essere un booleano (true/false)", corrected_data
                print(f"[DEBUG] corsi_cucina valido: {data['corsi_cucina']}")

            # Validazione degustazione usando validate_degustazione
            if 'degustazione' in data:
                print(f"[DEBUG] Validazione degustazione: {data['degustazione']}")
                is_valid, error_msg, corrected_data = self.validate_degustazione(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione degustazione fallita: {error_msg}")
                    return False, error_msg, corrected_data
                print(f"[DEBUG] degustazione validata con successo: {corrected_data['degustazione']}")

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