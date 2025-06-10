"""
Libreria per la gestione del template naturalistico.json
Gestisce le preferenze per le attività naturalistiche
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

class NaturalisticoTemplate(BaseTemplate):
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
            with open("template/naturalistico.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def set_template(self, template_name: str):
        """Cambia il template attivo"""
        self.template_name = template_name
        self.template_path = f"template/{template_name}.json"
        self.template_data = self._load_template()

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
            conn = get_db_connection()
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
                        FROM attivita_naturalistiche
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
                            attivita_corrette.append(None)
                    else:
                        print(f"Nessun risultato trovato per l'attività '{attivita}'")
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
            print(f"Errore durante la verifica delle attività: {str(e)}")
            return False, f"Errore durante la verifica delle attività: {str(e)}", corrected_data
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()


    def validate_lingua(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida lingua_guida
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = {}
        
        try:
            if 'lingua_guida' not in data or not data['lingua_guida']:
                return True, "La lingua guida mancante", corrected_data

            print(f"Verifica lingua guida per: {data['lingua_guida']}")

            print("Tentativo di connessione al database...")
            conn = get_db_connection()
            print("Connessione al database stabilita con successo")
            cursor = conn.cursor()

            try:
                print(f"Generazione embedding per lingua guida: '{data['lingua_guida']}'")
                lingua_guida_embedding = self.model.encode(data['lingua_guida'])
                print(f"Embedding generato con successo, dimensione: {len(lingua_guida_embedding)}")
                lingua_guida_embedding = lingua_guida_embedding.tolist()

                print("Esecuzione query per trovare la lingua guida più simile...")
                cursor.execute("""
                    SELECT lingua, embedding_lingua <=> %s::vector as distanza
                    FROM linguaggio
                    WHERE embedding_lingua IS NOT NULL
                    ORDER BY distanza ASC
                    LIMIT 1
                """, (lingua_guida_embedding,))
                
                risultato = cursor.fetchall()
                print(f"Risultato query: {risultato}")

                if risultato:
                    lingua_corretta, distanza = risultato[0]
                    print(f"Distanza trovata: {distanza}")
                    if distanza < 0.4:
                        print(f"Aggiornamento lingua guida da '{data['lingua_guida']}' a '{lingua_corretta}'")
                        corrected_data['lingua_guida'] = lingua_corretta
                        corrected_data['guida_esperta'] = True
                        corrected_data['guida_menzionata'] = True
                        return True, "Lingua guida verificata", corrected_data
                    else:
                        print(f"Lingua guida '{data['lingua_guida']}' non ha corrispondenze sufficientemente simili")
                        corrected_data['lingua_guida'] = None
                        return True, "Lingua guida non valida", corrected_data
                else:
                    print(f"Nessun risultato trovato per la lingua guida '{data['lingua_guida']}'")
                    corrected_data['lingua_guida'] = None
                    return True, "Lingua guida non valida", corrected_data

            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                corrected_data['lingua_guida'] = None
                return True, f"Errore durante la verifica della lingua guida: {str(e)}", corrected_data

        except Exception as e:
            print(f"Errore durante la verifica della lingua guida: {str(e)}")
            corrected_data['lingua_guida'] = None
            return True, f"Errore durante la verifica della lingua guida: {str(e)}", corrected_data
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
        print("[DEBUG] Inizio validazione dati naturalistico")
        print(f"[DEBUG] Dati ricevuti: {data}")
        
        # Inizializza corrected_data con tutti i campi del template
        corrected_data = data.copy()
        errors = []
        
        try:
            # Validazione attivita usando validate_attivita
            if 'attivita' in data:
                print(f"[DEBUG] Validazione attivita: {data['attivita']}")
                is_valid, error_msg, updated_data = self.validate_attivita(corrected_data)
                if not is_valid:
                    print(f"[ERROR] Validazione attivita fallita: {error_msg}")
                    errors.append(error_msg)
                corrected_data.update(updated_data)
                print(f"[DEBUG] attivita validata con successo: {corrected_data['attivita']}")

            #se guida_menzionata è null, allora non è presente guida_esperta
            print("[DEBUG]: guida_menzionata",data['guida_menzionata'])
            if data['guida_menzionata'] == None:
                print("[DEBUG] guida_menzionata è null, allora non è presente guida_esperta")
                corrected_data['guida_esperta'] = None
                corrected_data['lingua_guida'] = None
                data['guida_esperta']=None
            if data['guida_menzionata'] == True:
                print("[DEBUG] guida_menzionata è true, allora è presente guida_esperta")
                corrected_data['guida_esperta'] = True
                data['guida_esperta']=True
            if data['guida_menzionata'] == False:
                print("[DEBUG] guida_menzionata è false, allora non è presente guida_esperta")
                corrected_data['guida_esperta'] = False
                data['guida_esperta'] = False

            # Gestione guida esperta e lingua
            print("[DEBUG]: guida_esperta",data['guida_esperta'])
            if data['guida_esperta'] is not None:
                print(f"[DEBUG] Verifica guida_esperta: {data['guida_esperta']}")
                if data['guida_esperta'] is False:  # Verifica esplicita per False
                    print("[DEBUG] Richiesta guida esperta impostata a False")
                    corrected_data['lingua_guida'] = "no guida"
                    print(f"[DEBUG] Lingua guida impostata a: {corrected_data['lingua_guida']}")
                elif data['guida_esperta'] is True:  # Verifica esplicita per True
                    if 'lingua_guida' not in data or not data['lingua_guida']:
                        print("[ERROR] Lingua guida mancante o non specificata")
                        errors.append("La lingua della guida è obbligatoria quando è richiesta una guida esperta")
                    else:
                        print("[DEBUG] Validazione lingua guida")
                        is_valid, error_msg, updated_data = self.validate_lingua(corrected_data)
                        if not is_valid:
                            errors.append(error_msg)
                        corrected_data.update(updated_data)
                        if corrected_data.get('lingua_guida'):
                            corrected_data['guida_esperta'] = True
                            corrected_data['guida_menzionata'] = True
                            print("[DEBUG] Lingua guida validata con successo, impostato guida_esperta e guida_menzionata a True")
                        print(f"[DEBUG] Lingua guida validata: {corrected_data.get('lingua_guida')}")
                        
                else:
                    print("[ERROR] Campo guida_esperta mancante")
                    errors.append("Il campo guida_esperta è obbligatorio")
                    corrected_data['lingua_guida'] = None
            
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
        Verifica e aggiorna tutti i campi del template naturalistico
        
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