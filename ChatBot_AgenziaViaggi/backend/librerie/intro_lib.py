"""
Libreria per la gestione del template intro.json
Gestisce le informazioni base del viaggio come destinazione, partecipanti, periodo e budget
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


class IntroTemplate:
    def __init__(self):
        self.template_path = "template/intro.json"
        self.template_data = self._load_template()
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)
    
    def _load_template(self) -> Dict[str, Any]:
        """Carica il template JSON"""
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _adjust_past_date(self, date_str: str) -> str:
        """
        Se la data è nel passato, la sposta all'anno successivo
        
        Args:
            date_str: Data nel formato YYYY-MM-DD
            
        Returns:
            str: Data corretta nel formato YYYY-MM-DD
        """
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now()
            
            # Se la data è nel passato, aggiungi anni fino a renderla valida
            while date < today:
                date = date.replace(year=date.year + 1)
            
            return date.strftime('%Y-%m-%d')
        except ValueError:
            return date_str
    
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

            # Validazione numero_partecipanti
            if 'numero_partecipanti' in data:
                if not isinstance(data['numero_partecipanti'], int):
                    return False, "Il numero di partecipanti deve essere un intero", corrected_data
                if data['numero_partecipanti'] < 1:
                    return False, "Il numero di partecipanti deve essere almeno 1", corrected_data
                if data['numero_partecipanti'] > 100:
                    return False, "Il numero di partecipanti non può superare 100", corrected_data

            # Validazione data_partenza
            if 'departure_date' in data:
                if not isinstance(data['departure_date'], str):
                    return False, "La data di partenza deve essere una stringa", corrected_data
                try:
                    # Verifica il formato YYYY-MM-DD
                    datetime.strptime(data['departure_date'], '%Y-%m-%d')
                    # Se la data è nel passato, la correggiamo
                    corrected_data['departure_date'] = self._adjust_past_date(data['departure_date'])
                except ValueError:
                    return False, "La data di partenza deve essere nel formato YYYY-MM-DD", corrected_data
            
            # Validazione trip_duration
            if 'trip_duration' in data:
                if not isinstance(data['trip_duration'], int):
                    return False, "La durata del viaggio deve essere un intero", corrected_data
                if data['trip_duration'] < 1:
                    return False, "La durata del viaggio deve essere di almeno 1 giorno", corrected_data
                if data['trip_duration'] > 365:
                    return False, "La durata del viaggio non può superare 365 giorni", corrected_data

            # Validazione budget_viaggio
            if 'budget_viaggio' in data:
                if not isinstance(data['budget_viaggio'], int):
                    return False, "Il budget del viaggio deve essere un intero", corrected_data
                if data['budget_viaggio'] < 0:
                    return False, "Il budget del viaggio non può essere negativo", corrected_data
                if data['budget_viaggio'] > 1000000:
                    return False, "Il budget del viaggio non può superare 1.000.000", corrected_data
            
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
        
        # Normalizza le stringhe
        for key in ['nazione_destinazione', 'regione_citta_destinazione', 'tipo_partecipanti']:
            if key in data:
                if isinstance(data[key], str):
                    processed_data[key] = data[key].strip().lower()
                elif isinstance(data[key], list):
                    processed_data[key] = [item.strip().lower() if isinstance(item, str) else item for item in data[key]]
                else:
                    processed_data[key] = data[key]
        
        # Gestione speciale per mood_vacanza che è sempre una lista
        if 'mood_vacanza' in data:
            if isinstance(data['mood_vacanza'], list):
                processed_data['mood_vacanza'] = [item.strip().lower() if isinstance(item, str) else item for item in data['mood_vacanza']]
            elif isinstance(data['mood_vacanza'], str):
                processed_data['mood_vacanza'] = [data['mood_vacanza'].strip().lower()]
            else:
                processed_data['mood_vacanza'] = []
        
        # Gestione speciale per trip_duration
        if 'trip_duration' in data:
            print(f"Elaborazione durata_viaggio. Valore originale: {data['trip_duration']} (tipo: {type(data['trip_duration'])})")
            try:
                # Se è una stringa, prova a estrarre il numero
                if isinstance(data['trip_duration'], str):
                    print(f"Valore è una stringa: '{data['trip_duration']}'")
                    # Rimuovi eventuali spazi e caratteri non numerici
                    numero_str = ''.join(c for c in data['trip_duration'] if c.isdigit())
                    print(f"Stringa pulita: '{numero_str}'")
                    if numero_str:
                        processed_data['trip_duration'] = int(numero_str)
                        print(f"Numero convertito: {processed_data['trip_duration']}")
                    else:
                        print("Nessun numero trovato nella stringa")
                        processed_data['trip_duration'] = None
                # Se è già un numero, convertilo in intero
                elif isinstance(data['trip_duration'], (int, float)):
                    print(f"Valore è un numero: {data['trip_duration']}")
                    processed_data['trip_duration'] = int(data['trip_duration'])
                    print(f"Numero convertito in intero: {processed_data['trip_duration']}")
                else:
                    print(f"Tipo non supportato: {type(data['trip_duration'])}")
                    processed_data['trip_duration'] = None
            except (ValueError, TypeError) as e:
                print(f"Errore durante la conversione del numero: {str(e)}")
                processed_data['trip_duration'] = None
        
        # Assicura che gli altri numeri siano interi
        for key in ['numero_partecipanti', 'budget_viaggio']:
            if key in data:
                try:
                    processed_data[key] = int(data[key]) if data[key] is not None else None
                except (ValueError, TypeError):
                    processed_data[key] = None
        
        # Normalizza la data
        if 'departure_date' in data:
            try:
                date = datetime.strptime(data['departure_date'], '%Y-%m-%d')
                processed_data['departure_date'] = date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                processed_data['departure_date'] = None
        
        print(f"Risultato finale per durata_viaggio: {processed_data.get('trip_duration')}")
        return processed_data

    def verifica_destinazione_generica(self, data: Dict[str, Any], model_path: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica la destinazione generica usando gli embedding
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        try:
            if 'nazione_destinazione' not in data or not data['nazione_destinazione']:
                print("Nazione di destinazione mancante o vuota")
                return False, "La nazione di destinazione è obbligatoria", data

            print(f"Verifica destinazione generica per: {data['nazione_destinazione']}")
            
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
                print("Generazione embedding con modello locale...")
                print(f"Testo da convertire in embedding: '{data['nazione_destinazione']}'")
                destinazione_embedding = self.model.encode(data['nazione_destinazione'])
                print(f"Embedding generato con successo, dimensione: {len(destinazione_embedding)}")
                # Converti l'array NumPy in lista
                destinazione_embedding = destinazione_embedding.tolist()
            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                raise

            print("Esecuzione query per trovare la destinazione più simile...")
            cursor.execute("""
                SELECT stato, embedding_stato  <=> %s::vector as distanza
                FROM destinazione_generica
                WHERE embedding_stato IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
            """, (destinazione_embedding,))
            
            risultato = cursor.fetchall()
            print(f"Risultato query: {risultato}")
            
            if risultato:
                stato_corretto, distanza = risultato[0]
                print(f"Distanza trovata: {distanza}")
                if distanza > 0.4:
                    print(f"Distanza troppo grande ({distanza} > 0.4), rimuovo il valore")
                    data['nazione_destinazione'] = None
                    return False, "Nessuna nazione simile trovata nel database", data
                
                print(f"Aggiornamento nazione da '{data['nazione_destinazione']}' a '{stato_corretto}'")
                data['nazione_destinazione'] = stato_corretto
                return True, "Nazione di destinazione verificata e corretta", data
            else:
                print("Nessun risultato trovato nel database, rimuovo il valore")
                data['nazione_destinazione'] = None
                return False, "Nessuna nazione trovata nel database", data

        except Exception as e:
            print(f"Errore durante la verifica della nazione: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            return False, f"Errore durante la verifica della nazione: {str(e)}", data
        finally:
            if 'cursor' in locals():
                print("Chiusura cursor")
                cursor.close()
            if 'conn' in locals():
                print("Chiusura connessione")
                conn.close()

    def verifica_destinazione_locale(self, data: Dict[str, Any], model_path: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica la destinazione locale usando gli embedding.
        Cerca sia nella tabella destinazioni_regionali che destinazioni_locali.
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        try:
            if 'regione_citta_destinazione' not in data or not data['regione_citta_destinazione']:
                print("Regione o città di destinazione mancante o vuota")
                return True, "La regione o città di destinazione è opzionale", data

            print(f"Verifica destinazione locale per: {data['regione_citta_destinazione']}")

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
                print("Generazione embedding con modello locale...")
                print(f"Testo da convertire in embedding: '{data['regione_citta_destinazione']}'")
                destinazione_embedding = self.model.encode(data['regione_citta_destinazione'])
                print(f"Embedding generato con successo, dimensione: {len(destinazione_embedding)}")
                # Converti l'array NumPy in lista
                destinazione_embedding = destinazione_embedding.tolist()
            except Exception as e:
                print(f"Errore durante la generazione dell'embedding: {str(e)}")
                print(f"Tipo di errore: {type(e)}")
                import traceback
                print("Stack trace:")
                print(traceback.format_exc())
                raise

            print("Esecuzione query per trovare la regione più simile...")
            cursor.execute("""
                SELECT regione, embedding_regione  <=> %s::vector as distanza
                FROM destinazioni_regionali
                WHERE embedding_regione IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
            """, (destinazione_embedding,))
            
            risultato_regionale = cursor.fetchall()
            print(f"Risultato query regionale: {risultato_regionale}")
            
            print("Esecuzione query per trovare la località più simile...")
            cursor.execute("""
                SELECT luogo, embedding_luogo  <=> %s::vector as distanza
                FROM destinazioni_locali
                WHERE embedding_luogo IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
            """, (destinazione_embedding,))
            
            risultato_locale = cursor.fetchall()
            print(f"Risultato query locale: {risultato_locale}")
            
            migliore_risultato = None
            migliore_distanza = float('inf')
            
            if risultato_regionale:
                regione, distanza_reg = risultato_regionale[0]
                print(f"Distanza regionale trovata: {distanza_reg}")
                if distanza_reg < migliore_distanza and distanza_reg < 0.4:
                    migliore_risultato = ('regione', regione)
                    migliore_distanza = distanza_reg
                    print(f"Nuovo migliore risultato: regione '{regione}' con distanza {distanza_reg}")
            
            if risultato_locale:
                luogo, distanza_loc = risultato_locale[0]
                print(f"Distanza locale trovata: {distanza_loc}")
                if distanza_loc < migliore_distanza and distanza_loc < 0.4:
                    migliore_risultato = ('luogo', luogo)
                    migliore_distanza = distanza_loc
                    print(f"Nuovo migliore risultato: luogo '{luogo}' con distanza {distanza_loc}")
            
            if migliore_risultato:
                tipo, nome = migliore_risultato
                print(f"Risultato finale: {tipo} '{nome}' con distanza {migliore_distanza}")
                print(f"Aggiornamento destinazione da '{data['regione_citta_destinazione']}' a '{nome}'")
                data['regione_citta_destinazione'] = nome
                return True, f"Regione o città di destinazione verificata e corretta (trovata come {tipo})", data
            else:
                print("Nessuna corrispondenza valida trovata (distanza > 0.4), rimuovo il valore")
                data['regione_citta_destinazione'] = None
                return False, "Nessuna regione o città simile trovata nel database", data

        except Exception as e:
            print(f"Errore durante la verifica della regione o città: {str(e)}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
            return False, f"Errore durante la verifica della regione o città: {str(e)}", data
        finally:
            if 'cursor' in locals():
                print("Chiusura cursor")
                cursor.close()
            if 'conn' in locals():
                print("Chiusura connessione")
                conn.close()

    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template intro utilizzando le funzioni di verifica esistenti
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        warnings = []
        errors = []
        updated_data = data.copy()
        
        try:
            # 1. Verifica destinazione generica
            is_valid_gen, msg_gen, updated_data = self.verifica_destinazione_generica(updated_data)
            if not is_valid_gen:
                errors.append(msg_gen)
            
            # 2. Verifica destinazione locale
            is_valid_loc, msg_loc, updated_data = self.verifica_destinazione_locale(updated_data)
            if not is_valid_loc:
                errors.append(msg_loc)
            
            # 3. Verifica e normalizza i dati
            updated_data = self.process_data(updated_data)
            
            # 4. Verifica la validità dei dati
            is_valid, msg, updated_data = self.validate_data(updated_data)
            if not is_valid:
                errors.append(msg)
            
            return updated_data, warnings, errors
            
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            return updated_data, warnings, errors 