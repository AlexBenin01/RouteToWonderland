"""
Libreria per la gestione del template alloggi.json
Gestisce le preferenze e i requisiti per l'alloggio
"""

import json
from typing import Dict, Any, Tuple, List
import re
from sentence_transformers import SentenceTransformer
import numpy as np
import os
from pathlib import Path
from .template_manager import TemplateManager
from .base_template import BaseTemplate
from .database import get_db_connection, release_connection

class AlloggiTemplate(BaseTemplate):
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
            with open("template/alloggi.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

        
    def validate_alloggio(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica il tipo di alloggio usando gli embedding.
        Controlla che il tipo di alloggio inserito corrisponda a un tipo valido nel database.
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        try:
            if 'tipo_alloggio' not in data or not data['tipo_alloggio']:
                print("Tipo alloggio mancante o vuoto")
                return False, "Il tipo di alloggio è obbligatorio", data

            print(f"Verifica tipo alloggio: {data['tipo_alloggio']}")
            
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                print("Generazione embedding per il tipo di alloggio...")
                print(f"Testo da convertire in embedding: '{data['tipo_alloggio']}'")
                tipo_alloggio_embedding = self.model.encode(data['tipo_alloggio'])
                print(f"Embedding generato con successo, dimensione: {len(tipo_alloggio_embedding)}")
                tipo_alloggio_embedding = tipo_alloggio_embedding.tolist()
            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                raise

            print("Esecuzione query per trovare il tipo di alloggio più simile...")
            cursor.execute("""
                SELECT alloggi, embedding_tipo_alloggi <=> %s::vector as distanza
                FROM tipo_alloggi
                WHERE embedding_tipo_alloggi IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
            """, (tipo_alloggio_embedding,))
            
            risultato = cursor.fetchall()
            print(f"Risultato query: {risultato}")
            
            if risultato:
                tipo_alloggio_corretto, distanza = risultato[0]
                print(f"Distanza trovata: {distanza}")
                if distanza > 0.4:
                    print(f"Distanza troppo grande ({distanza} > 0.4), rimuovo il valore")
                    data['tipo_alloggio'] = None
                    return False, "Nessun tipo di alloggio simile trovato nel database", data
                
                print(f"Aggiornamento tipo alloggio da '{data['tipo_alloggio']}' a '{tipo_alloggio_corretto}'")
                data['tipo_alloggio'] = tipo_alloggio_corretto
                return True, "Tipo di alloggio verificato e corretto", data
            else:
                print("Nessun risultato trovato nel database, rimuovo il valore")
                data['tipo_alloggio'] = None
                return False, "Nessun tipo di alloggio trovato nel database", data

        except Exception as e:
            print(f"Errore durante la verifica del tipo di alloggio: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            return False, f"Errore durante la verifica del tipo di alloggio: {str(e)}", data
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
        print("[DEBUG] Inizio validazione dati alloggi")
        print(f"[DEBUG] Dati ricevuti: {data}")
        
        # Crea una copia dei dati originali per il confronto
        original_data = data.copy()
        corrected_data = data.copy()
        template_data = self.get_template_data()
        
        try:
            # Validazione tipo_alloggio usando validate_alloggio
            if 'tipo_alloggio' in data:
                print(f"[DEBUG] Validazione tipo_alloggio: {data['tipo_alloggio']}")
                is_valid, error_msg, corrected_data = self.validate_alloggio(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione tipo_alloggio fallita: {error_msg}")
                    return False, error_msg, corrected_data
                print(f"[DEBUG] tipo_alloggio validato con successo: {corrected_data['tipo_alloggio']}")

           
            
            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")

            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
        
        print("[DEBUG] Validazione completata con successo")
        print(f"[DEBUG] Dati corretti: {corrected_data}")
        return True, "Dati validi", corrected_data
        

    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template alloggi
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        print("[DEBUG] Inizio verifica_template alloggi")
        print(f"[DEBUG] Dati ricevuti: {data}")
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

