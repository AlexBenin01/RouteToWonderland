"""
Libreria per la gestione del template noleggi.json
Gestisce le informazioni relative ai noleggi
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
from .database import get_db_connection

class NoleggiTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)

    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
        

    def validate_tipo_cambio(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida il tipo di cambio
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            if 'tipo_cambio' not in data or not data['tipo_cambio']:
                return True, "Il tipo di cambio mancante", corrected_data

            print(f"Verifica tipo di cambio per: {data['tipo_cambio']}")

            print("Tentativo di connessione al database...")
            conn = get_db_connection()
            print("Connessione al database stabilita con successo")
            cursor = conn.cursor()

            try:
                print(f"Generazione embedding per tipo di cambio: '{data['tipo_cambio']}'")
                tipo_cambio_embedding = self.model.encode(data['tipo_cambio'])
                print(f"Embedding generato con successo, dimensione: {len(tipo_cambio_embedding)}")
                tipo_cambio_embedding = tipo_cambio_embedding.tolist()

                print("Esecuzione query per trovare il tipo di cambio più simile...")
                cursor.execute("""
                    SELECT cambio, embedding_tipo_cambio <=> %s::vector as distanza
                    FROM tipo_cambio
                    WHERE embedding_tipo_cambio IS NOT NULL
                    ORDER BY distanza ASC
                    LIMIT 1
                """, (tipo_cambio_embedding,))
                
                risultato = cursor.fetchall()
                print(f"Risultato query: {risultato}")

                if risultato:
                    tipo_cambio_corretto, distanza = risultato[0]
                    print(f"Distanza trovata: {distanza}")
                    if distanza < 0.4:
                        print(f"Aggiornamento tipo di cambio da '{data['tipo_cambio']}' a '{tipo_cambio_corretto}'")
                        corrected_data['tipo_cambio'] = tipo_cambio_corretto
                        return True, "Tipo di cambio verificato", corrected_data
                    else:
                        print(f"Tipo di cambio '{data['tipo_cambio']}' non ha corrispondenze sufficientemente simili")
                        corrected_data['tipo_cambio'] = None
                        data['tipo_cambio'] = None
                        return False, "Tipo di cambio non valido", corrected_data
                else:
                    print(f"Nessun risultato trovato per il tipo di cambio '{data['tipo_cambio']}'")
                    corrected_data['tipo_cambio'] = None
                    data['tipo_cambio'] = None
                    return False, "Tipo di cambio non valido", corrected_data

            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                return False, f"Errore durante la verifica del cambio auto: {str(e)}", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica del cambio auto: {str(e)}")
            return False, f"Errore durante la verifica del cambio auto: {str(e)}", corrected_data
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
        print("[DEBUG] Inizio validazione dati noleggi")
        print(f"[DEBUG] Dati ricevuti: {data}")
        corrected_data = data.copy()
        template_data = self.get_template_data()
        errors = []
        
        try:
            # Validazione posti_auto
            if 'posti_auto' in data:
                print(f"[DEBUG] Validazione posti_auto: {data['posti_auto']}")
                if not isinstance(data['posti_auto'], int):
                    print("[ERROR] posti_auto non è un intero")
                    corrected_data['posti_auto'] = None
                    errors.append("Il numero di posti auto deve essere un numero intero")
                elif data['posti_auto'] < 2:
                    print("[ERROR] posti_auto fuori range (2- XX)")
                    corrected_data['posti_auto'] = None
                    errors.append("Il numero di posti auto deve essere compreso tra 2 e XX")
                else:
                    print(f"[DEBUG] posti_auto valido: {data['posti_auto']}")

            # Validazione cambio_automatico
            if 'tipo_cambio' in data:
                print(f"[DEBUG] Validazione tipo_cambio: {data['tipo_cambio']}")
                is_valid, error_msg, updated_data = self.validate_tipo_cambio(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione tipo_cambio fallita: {error_msg}")
                    errors.append(error_msg)
                else:
                    corrected_data.update(updated_data)
                    print(f"[DEBUG] tipo_cambio validato con successo: {corrected_data['tipo_cambio']}")
            
            print("[DEBUG] Validazione completata")
            print(f"[DEBUG] Dati corretti: {corrected_data}")
            
            # Se ci sono errori, restituisci False con tutti gli errori
            if errors:
                error_message = "Errori di validazione:\n" + "\n".join(f"- {error}" for error in errors)
                return False, error_message, corrected_data
            
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            print(f"[ERROR] Errore durante la validazione: {str(e)}")
            errors.append(f"Errore durante la validazione: {str(e)}")
            return False, "\n".join(errors), corrected_data
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template noleggi
        
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

            return updated_data,data_was_different, warnings, errors
            
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            data_was_different = self.are_data_different(original_data, updated_data)
            return updated_data,data_was_different, warnings, errors