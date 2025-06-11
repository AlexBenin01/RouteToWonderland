"""
Libreria per la gestione delle interazioni con Ollama.
Utilizza il modello Qwen3 ("qwen3:1.7b") tramite Ollama per generare risposte in linguaggio naturale.
Le risposte sono sempre formulate in italiano.
"""

import requests
import json
from typing import Dict, Any, Optional, List
import logging
import re
import sys

# Configurazione del logger per supportare UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Forza l'encoding UTF-8 per stdout
sys.stdout.reconfigure(encoding='utf-8')

class OllamaManager:
    def __init__(self, model_name: str = "qwen3:1.7b"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434/api"
        self.frasi_guida = self._load_frasi_guida()
        
    def _load_frasi_guida(self) -> Dict[str, Dict[str, str]]:
        """Carica le frasi guida dal file JSON"""
        try:
            with open("frasi_guida.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Errore nel caricamento delle frasi guida: {str(e)}")
            return {}
        
    def _create_prompt(self, template_type: str, template: Dict[str, Any]) -> str:
        """Restituisce la frase guida per il prossimo campo da compilare"""
        # Se il template è vuoto, restituisci la frase guida per il primo campo del template
        logging.getLogger(__name__).info(f"Template: {template}")
        if not template:
            # Ottieni la prima frase guida disponibile per questo tipo di template
            first_field = next(iter(self.frasi_guida.get(template_type, {})), None)
            if first_field:
                return self.frasi_guida[template_type][first_field]
            return f"Per favore, fornisci informazioni per il template {template_type}"
            
        # Trova i campi vuoti
        empty_fields = [field for field, value in template.items() if not value]
        if not empty_fields:
            return "Tutti i campi sono stati compilati."
            
        next_field = empty_fields[0]
        
        # Crea un prompt contestuale basato sui dati già presenti
        context = []
        for field, value in template.items():
            if value:
                if isinstance(value, list):
                    context.append(f"{field}: {', '.join(str(v) for v in value)}")
                else:
                    context.append(f"{field}: {value}")
        
        context_str = "\n".join(context) if context else "Nessuna informazione precedente"
        
        # Ottieni la frase guida specifica per il campo
        frase_guida = self.frasi_guida.get(template_type, {}).get(
            next_field,
            f"Per favore, fornisci informazioni per il campo {next_field}"
        )
        
        # Costruisci il prompt completo
        prompt = f"""Sei un assistente di viaggio esperto e cordiale. Il tuo compito è fare domande per raccogliere informazioni sul viaggio.

Contesto attuale:
{context_str}

Devi chiedere informazioni per il campo: {next_field}
Frase guida di riferimento: {frase_guida}

IMPORTANTE: NON ripetere la frase guida. Invece, formula una domanda naturale e conversazionale basata sulla frase guida.
La domanda deve essere:
- In italiano
- Diretta e specifica
- Naturale e conversazionale
- Pertinente al contesto fornito

Ora, formula la tua domanda:"""
        
        return prompt

    def get_response(self, template_type: str, template: Dict[str, Any]) -> str:
        """Ottiene una risposta personalizzata da Ollama"""
        try:
            prompt = self._create_prompt(template_type, template)
            logging.getLogger(__name__).info(f"Frase guida inviata ad Ollama: {prompt}")
            logging.getLogger(__name__).info(f"Template aggiornato: {json.dumps(template, ensure_ascii=False, indent=2)}")
            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "system": "Sei un assistente di viaggio esperto e cordiale. Rispondi sempre in italiano."
                    }
                }
            )
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "Mi dispiace, non sono riuscito a generare una risposta appropriata.")
                # Estrai solo il testo in italiano (dopo l'ultima riga vuota)
                _text = response_text.split('\n\n')[-1].strip()
                # Rimuovi le emoji dalla risposta
                #_text = re.sub(r'[^\x00-\x7F]+', '', _text)
                return _text
            else:
                return f"Errore nella comunicazione con Ollama: {response.status_code}"
        except Exception as e:
            return f"Si è verificato un errore: {str(e)}"

    def validate_response(self, response: str, expected_type: str) -> bool:
        """Valida la risposta in base al tipo di campo atteso"""
        try:
            if expected_type == "integer":
                int(response)
                return True
            elif expected_type == "boolean":
                return response.lower() in ["true", "false", "sì", "no", "si"]
            elif expected_type == "date":
                # Implementare la validazione della data
                return True
            else:
                return bool(response.strip())
        except:
            return False 
        
    def get_exit(self) -> str:
        """Restituisce una frase guida per chiedere se concludere la conversazione"""
        try:
            prompt = """Sei un assistente di viaggio esperto e cordiale. Il tuo compito è chiedere all'utente se desidera concludere la conversazione.

IMPORTANTE:
- La domanda deve essere in italiano
- Deve essere naturale e conversazionale
- Deve dare l'impressione che l'assistente sia disponibile a continuare se l'utente lo desidera
- Non deve essere troppo diretta o brusca

Ora, formula la tua domanda:"""

            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "system": "Sei un assistente di viaggio esperto e cordiale. Rispondi sempre in italiano."
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "Mi dispiace, non sono riuscito a generare una risposta appropriata.")
                # Estrai solo il testo in italiano (dopo l'ultima riga vuota)
                _text = response_text.split('\n\n')[-1].strip()
                # Rimuovi le emoji dalla risposta
                #_text = re.sub(r'[^\x00-\x7F]+', '', _text)
                return _text
            else:
                return f"Errore nella comunicazione con Ollama: {response.status_code}"
        except Exception as e:
            return f"Si è verificato un errore: {str(e)}" 
    
    def campi_obbligatori(self) -> str:
        """Restituisce una frase guida per chiedere se concludere la conversazione"""
        try:
            prompt = """Sei un assistente di viaggio esperto e cordiale. Il tuo compito è comunicare all'utente che ci sono ancora domande obbligatorie da completare.

IMPORTANTE:
- La risposta deve essere: "Abbiamo ancora delle domande obbligatorie prima di passare alla fattura di viaggio"
- La risposta deve essere in italiano
- Non modificare la frase fornita
- Non aggiungere altro testo

Ora, formula la tua risposta:"""

            response = requests.post(
                f"{self.base_url}/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "system": "Sei un assistente di viaggio esperto e cordiale. Rispondi sempre in italiano."
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "Mi dispiace, non sono riuscito a generare una risposta appropriata.")
                # Estrai solo il testo in italiano (dopo l'ultima riga vuota)
                _text = response_text.split('\n\n')[-1].strip()
                # Rimuovi le emoji dalla risposta
                #_text = re.sub(r'[^\x00-\x7F]+', '', _text)
                return _text
            else:
                return f"Errore nella comunicazione con Ollama: {response.status_code}"
        except Exception as e:
            return f"Si è verificato un errore: {str(e)}" 
        