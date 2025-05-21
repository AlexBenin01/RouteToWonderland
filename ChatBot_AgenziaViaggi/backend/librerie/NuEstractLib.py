"""
Libreria per l'estrazione delle informazioni dal testo utilizzando il modello NuExtract-2-2B-experimental
"""

import json
from typing import Dict, Any, Optional, Tuple
from .utils import extract_entities

class NuExtract:
    def __init__(self, model_path: str = './NuExtract-2-2B-experimental'):
        self.model_path = model_path
        

    def process_extraction(self, text: str, empty_template: Dict[str, Any], saved_template: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Elabora il testo e aggiorna il template con le nuove informazioni
        
        Args:
            text: Il testo da analizzare
            empty_template: Il template vuoto che definisce la struttura
            saved_template: Il template con i dati già salvati
            
        Returns:
            Tuple[Dict[str, Any], bool]: Il template aggiornato e un flag che indica se sono state trovate nuove informazioni
        """
        try:
            

            # Usa la funzione extract_entities da utils.py per ottenere la risposta dal modello
            result = extract_entities(
                text=text,
                template=json.dumps(empty_template, ensure_ascii=False),
                model_path=self.model_path
            )
            
            # Converti la risposta in JSON
            try:
                print(f"Dati estratti: {result}")
                extracted_data = json.loads(result)
                print(f"Dati estratti: {extracted_data}")
            except json.JSONDecodeError:
                print(f"Errore nel parsing della risposta JSON: {result}")
                return saved_template, False
            
            # Aggiorna il template salvato solo con i campi non già presenti
            template_updated = False
            for key, value in extracted_data.items():
                if key not in saved_template or not saved_template[key]:
                    saved_template[key] = value
                    template_updated = True
            
            # Gestione speciale per mood_vacanza nel template intro
            if "mood_vacanza" in extracted_data:
                if "mood_vacanza" not in saved_template:
                    saved_template["mood_vacanza"] = []
                
                # Gestione del valore estratto
                if isinstance(extracted_data["mood_vacanza"], list):
                    # Se è una lista, aggiungi ogni mood non presente
                    for mood in extracted_data["mood_vacanza"]:
                        if mood not in saved_template["mood_vacanza"]:
                            saved_template["mood_vacanza"].append(mood)
                            template_updated = True
                else:
                    # Se è un singolo valore, aggiungilo se non presente
                    if extracted_data["mood_vacanza"] not in saved_template["mood_vacanza"]:
                        saved_template["mood_vacanza"].append(extracted_data["mood_vacanza"])
                        template_updated = True
            
            return saved_template, template_updated
            
        except Exception as e:
            print(f"Errore durante l'estrazione: {str(e)}")
            return saved_template, False
