"""
Libreria per la gestione del template mare.json
Gestisce le preferenze per le attività balneari
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

class MareTemplate(BaseTemplate):
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
            with open("template/mare.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

    def validate_attivita(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
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
            conn = get_db_connection()
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
                            attivita_corrette.append(None)
                    else:
                        print(f"Nessun risultato trovato per l'attività marina '{attivita}'")
                        attivita_corrette.append(None)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{attivita}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    attivita_corrette.append(None)

            # Rimuovi i None dalla lista
            attivita_corrette = [a for a in attivita_corrette if a is not None]
            corrected_data['attivita'] = attivita_corrette if attivita_corrette else None
            print(f"Attività finali: {attivita_corrette}")
            return True, "Attività verificate", corrected_data

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
        print("[DEBUG] Inizio validazione dati mare")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        
        try:
            # Validazione attivita usando validate_attivita
            if 'attivita' in data:
                print(f"[DEBUG] Validazione attivita: {data['attivita']}")
                is_valid, error_msg, updated_data = self.validate_attivita(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione attivita fallita: {error_msg}")
                    return False, error_msg, corrected_data
                corrected_data.update(updated_data)
                print(f"[DEBUG] attivita validato con successo: {corrected_data['attivita']}")

            # Mantieni il valore di attrezzatura se presente
            if 'attrezzatura' in data:
                corrected_data['attrezzatura'] = data['attrezzatura']
                # Se attrezzatura è valorizzata, copia lo stesso valore in attrezzatura_menzionata
                if data['attrezzatura'] is not None:
                    corrected_data['attrezzatura_menzionata'] = corrected_data['attrezzatura']
            
            if 'attrezzatura_menzionata' in data:
                corrected_data['attrezzatura_menzionata'] = data['attrezzatura_menzionata']

                if data['attrezzatura_menzionata'] is not None:
                    corrected_data['attrezzatura'] = corrected_data['attrezzatura_menzionata']
            
                

            print("[DEBUG] Validazione completata con successo")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
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