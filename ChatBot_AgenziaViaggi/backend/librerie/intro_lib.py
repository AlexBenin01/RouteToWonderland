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
from .template_manager import TemplateManager
from .base_template import BaseTemplate


class IntroTemplate(BaseTemplate):
    def __init__(self, template_manager: TemplateManager):
        super().__init__(template_manager)
        self.model_path = str(Path(__file__).resolve().parent.parent.parent / 'nomic-embed-text-v1.5')
        self.model = SentenceTransformer(self.model_path, trust_remote_code=True)
    
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
        corrected_data = data.copy()
        template_data = self.get_template_data()
        
        try:
            # Validazione nazione_destinazione
            if 'nazione_destinazione' not in data or not data['nazione_destinazione']:
                return False, "La nazione di destinazione è obbligatoria", corrected_data
            
            # Validazione regione_citta_destinazione
            if 'regione_citta_destinazione' not in data or not data['regione_citta_destinazione']:
                return False, "La regione/città di destinazione è obbligatoria", corrected_data
            
            # Validazione numero_partecipanti
            if 'numero_partecipanti' in data:
                if not isinstance(data['numero_partecipanti'], int):
                    return False, "Il numero di partecipanti deve essere un intero", corrected_data
                if data['numero_partecipanti'] <= 0:
                    return False, "Il numero di partecipanti deve essere maggiore di zero", corrected_data
            
            # Validazione tipo_partecipanti
            if 'tipo_partecipanti' in data:
                valid_types = template_data.get('tipo_partecipanti', [])
                if isinstance(data['tipo_partecipanti'], list):
                    if not all(tipo in valid_types for tipo in data['tipo_partecipanti']):
                        return False, f"I tipi di partecipanti devono essere tra: {', '.join(valid_types)}", corrected_data
                else:
                    if data['tipo_partecipanti'] not in valid_types:
                        return False, f"Il tipo di partecipanti deve essere tra: {', '.join(valid_types)}", corrected_data
            
            # Validazione departure_date
            if 'departure_date' in data:
                if not isinstance(data['departure_date'], str):
                    return False, "La data di partenza deve essere una stringa", corrected_data
                try:
                    corrected_data['departure_date'] = self._adjust_past_date(data['departure_date'])
                except ValueError:
                    return False, "La data di partenza deve essere nel formato YYYY-MM-DD", corrected_data
            
            # Validazione trip_duration
            if 'trip_duration' in data:
                if not isinstance(data['trip_duration'], int):
                    return False, "La durata del viaggio deve essere un intero", corrected_data
                if data['trip_duration'] <= 0:
                    return False, "La durata del viaggio deve essere maggiore di zero", corrected_data
            
            # Validazione mood_vacanza
            if 'mood_vacanza' in data:
                valid_moods = template_data.get('mood_vacanza', [[]])[0]
                if isinstance(data['mood_vacanza'], list):
                    if not all(mood in valid_moods for mood in data['mood_vacanza']):
                        return False, f"I mood della vacanza devono essere tra: {', '.join(valid_moods)}", corrected_data
                else:
                    if data['mood_vacanza'] not in valid_moods:
                        return False, f"Il mood della vacanza deve essere tra: {', '.join(valid_moods)}", corrected_data
            
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
        
        # Copia gli altri campi
        for key, value in data.items():
            if key not in processed_data:
                processed_data[key] = value
        
        return processed_data
    
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

            # 3. Verifica mood vacanza
            is_valid_mood, msg_mood, updated_data = self.verifica_mood_vacanza(updated_data)
            if not is_valid_mood:
                errors.append(msg_mood)
            
            # 4. Chiama il metodo della classe base per la validazione standard
            updated_data, base_warnings, base_errors = super().verifica_template(updated_data)
            warnings.extend(base_warnings)
            errors.extend(base_errors)
            
            return updated_data, warnings, errors
            
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            return updated_data, warnings, errors

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

    def verifica_mood_vacanza(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica il mood della vacanza usando gli embedding.
        Gestisce sia un singolo mood che una lista di mood.
        Utilizza la tabella tag per trovare corrispondenze semantiche.
        """
        try:
            if 'mood_vacanza' not in data or not data['mood_vacanza']:
                print("Mood della vacanza mancante o vuoto")
                return True, "Mood della vacanza è opzionale", data

            # Converti in lista se è una stringa singola
            mood_list = data['mood_vacanza'] if isinstance(data['mood_vacanza'], list) else [data['mood_vacanza']]
            print(f"Verifica mood della vacanza per: {mood_list}")

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

            mood_corretti = []
            for mood in mood_list:
                try:
                    print(f"Generazione embedding per mood: '{mood}'")
                    mood_embedding = self.model.encode(mood)
                    print(f"Embedding generato con successo, dimensione: {len(mood_embedding)}")
                    # Converti l'array NumPy in lista
                    mood_embedding = mood_embedding.tolist()

                    print("Esecuzione query per trovare il tag più simile...")
                    cursor.execute("""
                        SELECT nome_tag, embedding_tag <=> %s::vector as distanza
                        FROM tag
                        WHERE embedding_tag IS NOT NULL
                        ORDER BY distanza ASC
                        LIMIT 1
                    """, (mood_embedding,))
                    
                    risultato_mood = cursor.fetchall()
                    print(f"Risultato query tag: {risultato_mood}")

                    if risultato_mood:
                        tag_corretto, distanza = risultato_mood[0]
                        print(f"Distanza trovata: {distanza}")
                        if distanza < 0.4:
                            print(f"Aggiornamento mood da '{mood}' a '{tag_corretto}'")
                            mood_corretti.append(tag_corretto)
                        else:
                            print(f"Mood '{mood}' non ha corrispondenze sufficientemente simili")
                            mood_corretti.append(mood)
                    else:
                        print(f"Nessun risultato trovato per il mood '{mood}'")
                        mood_corretti.append(mood)

                except Exception as e:
                    print(f"Errore durante la generazione dell'embedding per '{mood}': {str(e)}")
                    print(f"Tipo di errore: {type(e)}")
                    import traceback
                    print("Stack trace:")
                    print(traceback.format_exc())
                    mood_corretti.append(mood)

            # Aggiorna il mood_vacanza con la lista corretta
            data['mood_vacanza'] = mood_corretti
            print(f"Mood finali: {mood_corretti}")
            return True, "Mood della vacanza verificato", data

        except Exception as e:
            print(f"Errore durante la verifica del mood della vacanza: {str(e)}")
            return False, f"Errore durante la verifica del mood della vacanza: {str(e)}", data
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()