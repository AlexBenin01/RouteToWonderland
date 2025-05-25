"""
Backend principale per l'applicazione RouteToWonderland
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from librerie.ollama_lib import OllamaManager
from librerie.NuEstractLib import NuExtract
from librerie.intro_lib import IntroTemplate
from librerie.contatti_lib import ContattiTemplate
from librerie.trasporto_lib import TrasportoTemplate
from librerie.alloggi_lib import AlloggiTemplate
from librerie.noleggi_lib import NoleggiTemplate
from librerie.naturalistico_lib import NaturalisticoTemplate
from librerie.avventura_lib import AvventuraTemplate
from librerie.montagna_lib import MontagnaTemplate
from librerie.mare_lib import MareTemplate
from librerie.gastronomia_lib import GastronomiaTemplate
from librerie.citta_arte_lib import CittaArteTemplate
from librerie.benessere_lib import BenessereTemplate
from librerie.famiglia_lib import FamigliaTemplate
from services.drools_service import DroolsService
import logging
from librerie.template_manager import TemplateManager

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Avvia FastAPI
app = FastAPI()

# Aggiungi il supporto CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variabile globale per lo stato della conversazione in formato JSON
STATO_CONVERSAZIONE_JSON = "{}"

# Inizializzazione dei servizi
template_manager = TemplateManager()
template_manager.load_templates()
template_manager.set_active_template("intro")
template_manager.update_template_sequence(["intro", "contatti","trasporto"])

ollama_manager = OllamaManager()
nu_extract = NuExtract()

# Inizializzazione di tutti i template
templates = {
    "intro": IntroTemplate(template_manager),
    "contatti": ContattiTemplate(template_manager),
    "trasporto": TrasportoTemplate(template_manager),
    "alloggi": AlloggiTemplate(template_manager),
    "noleggi": NoleggiTemplate(template_manager),
    "naturalistico": NaturalisticoTemplate(template_manager),
    "avventura": AvventuraTemplate(template_manager),
    "montagna": MontagnaTemplate(template_manager),
    "mare": MareTemplate(template_manager),
    "gastronomia": GastronomiaTemplate(template_manager),
    "citta_arte": CittaArteTemplate(template_manager),
    "benessere": BenessereTemplate(template_manager),
    "famiglia": FamigliaTemplate(template_manager)
}
# Inizializzazione del servizio Drools
drools_service = DroolsService()

class SimpleRequest(BaseModel):
    text: str
    campo: Optional[str] = None

class TemplateChangeRequest(BaseModel):
    template_type: str

class TravelPreferenceRequest(BaseModel):
    nazione_destinazione: str
    regione_citta_destinazione: str
    numero_partecipanti: int
    tipo_partecipanti: str
    departure_date: str
    trip_duration: int
    mood_vacanza: List[str]
    budget_viaggio: int

def normalize_template_value(value: Any) -> Any:
    """
    Normalizza i valori del template:
    - Ritorna None se il valore è una stringa o un numero
    - Ritorna [] se il valore può contenere più oggetti
    
    Args:
        value: Il valore da normalizzare
        
    Returns:
        Any: Il valore normalizzato
    """
    if isinstance(value, (str, int, float)):
        return None
    elif isinstance(value, list):
        return []
    elif isinstance(value, dict):
        # Se è un dizionario, normalizza i suoi valori
        return {k: normalize_template_value(v) for k, v in value.items()}
    return value

def get_empty_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea un template vuoto normalizzando tutti i valori
    
    Args:
        template: Il template originale
        
    Returns:
        Dict[str, Any]: Il template con valori normalizzati
    """
    return {k: normalize_template_value(v) for k, v in template.items()}

@app.post("/extract_simple")
async def extract_simple(request: SimpleRequest):
    global STATO_CONVERSAZIONE_JSON
    
    logger.info("\n=== INIZIO RICHIESTA EXTRACT_SIMPLE ===")
    logger.info(f"Testo ricevuto: {request.text}")
    logger.info(f"Template attivo: {template_manager.active_template}")
    logger.info(f"Sequenza template: {template_manager.get_template_sequence()}")
    
    try:
        # Carica lo stato attuale
        stato_attuale = json.loads(STATO_CONVERSAZIONE_JSON)
        logger.info(f"Stato attuale: {stato_attuale}")
        
        # Ottieni il template attivo
        template_attivo = stato_attuale.get(template_manager.active_template, {})
        logger.info(f"Template attivo corrente: {template_attivo}")
        
        # Estrai le informazioni dal testo
        template_aggiornato, template_modificato = nu_extract.process_extraction(
            text=request.text,
            empty_template=template_manager.get_active_template(),
            saved_template=template_attivo
        )
        logger.info(f"Template modificato: {template_modificato}")
        logger.info(f"Template aggiornato: {template_aggiornato}")
        
        # Ottieni l'istanza del template corrente
        current_template = templates.get(template_manager.active_template)
        if current_template:
            logger.info(f"Tipo di current_template: {type(current_template)}")
            logger.info(f"Classi base di current_template: {type(current_template).__bases__}")
            # Verifica il template usando il metodo della classe base
            template_aggiornato, warnings, errors = current_template.verifica_template(template_aggiornato)
            if errors:
                logger.warning(f"Errori nel template {template_manager.active_template}: {errors}")
            if warnings:
                logger.warning(f"Warning nel template {template_manager.active_template}: {warnings}")
        else:
            warnings = []
            errors = []
        
        # Aggiorna lo stato solo se ci sono state modifiche
        if template_modificato:
            logger.info("Aggiornamento stato conversazione")
            stato_attuale[template_manager.active_template] = template_aggiornato
            STATO_CONVERSAZIONE_JSON = json.dumps(stato_attuale, ensure_ascii=False)
            logger.info(f"Stato aggiornato per il template {template_manager.active_template}")
            logger.info(f"Stato completo: {STATO_CONVERSAZIONE_JSON}")
        
        # Verifica se il template è completo usando il metodo della classe base
        template_completo = all(
            campo in template_aggiornato and (
                template_aggiornato[campo] is not None and 
                (isinstance(template_aggiornato[campo], bool) or template_aggiornato[campo])
            )
            for campo in template_manager.get_active_template().keys()
        )
        logger.info(f"Template completo: {template_completo}")
        
        if template_completo:
            logger.info(f"Template {template_manager.active_template} completato")
            
            # Gestione speciale per il template intro
            if template_manager.active_template == "intro":
                logger.info("Template intro completato, preparazione chiamata evaluate_preferences")
                # Prepara la richiesta per evaluate_preferences
                preference_request = TravelPreferenceRequest(**template_aggiornato)
                logger.info(f"Richiesta preferences: {preference_request.dict()}")
                # Chiama evaluate_preferences per aggiornare la sequenza
                await evaluate_preferences(preference_request)
            
            # Trova il prossimo template nella sequenza
            current_index = template_manager.get_template_sequence().index(template_manager.active_template)
            logger.info(f"Indice template corrente: {current_index}")
            
            if current_index < len(template_manager.get_template_sequence()) - 1:
                next_template = template_manager.get_template_sequence()[current_index + 1]
                logger.info(f"Passaggio al prossimo template: {next_template}")
                
                # Cambia il template attivo
                template_manager.set_active_template(next_template)
                logger.info(f"Nuovo template attivo: {template_manager.active_template}")
                
                # Ottieni il template vuoto per il nuovo template
                empty_template = get_empty_template(template_manager.get_active_template())
                logger.info(f"Template vuoto per {next_template}: {empty_template}")
                logger.info(f"Template attivo: {template_manager.active_template}")
                
                try:
                    risposta = ollama_manager.get_response(
                        template_type=template_manager.active_template,
                        template=empty_template
                    )
                    logger.info(f"Risposta per il nuovo template: {risposta}")
                except Exception as e:
                    logger.error(f"Errore nella generazione della risposta per il nuovo template: {str(e)}")
                    risposta = f"Benvenuto al template {next_template}. Come posso aiutarti?"
                
                response = {
                    "guide_phrase": risposta,
                    "template_usato": template_manager.active_template,
                    "stato_conversazione": stato_attuale,
                    "nuovo_template": True,
                    "next_template": next_template,
                    "warnings": warnings,
                    "errors": errors
                }
                logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE (cambio template) ===")
                return response
        
        # Ottieni la risposta da Ollama
        try:
            logger.info("Richiesta risposta a Ollama")
            risposta = ollama_manager.get_response(
                template_type=template_manager.active_template,
                template=template_aggiornato
            )
            logger.info(f"Risposta ottenuta da Ollama: {risposta}")
        except Exception as ollama_error:
            logger.error(f"Errore nella comunicazione con Ollama: {str(ollama_error)}")
            # Risposta di fallback basata sul template attivo
            if errors:
                risposta = "Mi dispiace, sto riscontrando alcuni problemi tecnici. Potresti ripetere la tua richiesta?"
        
        # Prepara la risposta finale
        response = {
            "guide_phrase": risposta,
            "template_usato": template_manager.active_template,
            "stato_conversazione": stato_attuale,
            "warnings": warnings,
            "errors": errors
        }
        
        logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE ===")
        return response
        
    except Exception as e:
        logger.error(f"Errore in extract_simple: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set_template")
def set_template(request: TemplateChangeRequest):
    logger.info(f"Richiesta cambio template a: {request.template_type}")
    
    if not template_manager.set_active_template(request.template_type):
        logger.error(f"Template non valido: {request.template_type}")
        raise HTTPException(status_code=400, detail="Template non valido")
    
    logger.info(f"Template attivo aggiornato a: {template_manager.active_template}")
    return {"template_attivo": template_manager.active_template}

@app.get("/debug_stato")
def debug_stato():
    global STATO_CONVERSAZIONE_JSON
    logger.info("Richiesta debug_stato")
    stato = json.loads(STATO_CONVERSAZIONE_JSON)
    return {
        "stato_conversazione": stato,
        "template_attivo": template_manager.active_template,
        "sequenza_template": template_manager.get_template_sequence()
    }

@app.post("/evaluate_preferences")
async def evaluate_preferences(request: TravelPreferenceRequest):
    logger.info("Inizio valutazione preferenze")
    logger.debug(f"Preferenze ricevute: {request.dict()}")
    
    try:
        # Converti la richiesta in formato JSON
        preference_json = request.dict()
        
        # Chiama il servizio Drools per ottenere i template attivi
        active_templates = await DroolsService.evaluate_preferences(preference_json)
        logger.info(f"Template attivi ottenuti da Drools: {active_templates}")
        
        # Crea una nuova sequenza di template basata sui template attivi
        # Mantieni sempre "intro",  "contatti" e "traporto" all'inizio
        new_sequence = ["intro", "contatti", "trasporto"]
        
        # Aggiungi i template attivi in ordine
        for template in active_templates:
            if template not in new_sequence:
                new_sequence.append(template)
        
        # Aggiorna la sequenza nel template manager
        template_manager.update_template_sequence(new_sequence)
        logger.info(f"Nuova sequenza template: {new_sequence}")
        
        return {
            "active_templates": active_templates,
            "new_sequence": new_sequence,
            "message": "Sequenza dei template aggiornata con successo"
        }
        
    except Exception as e:
        logger.error(f"Errore in evaluate_preferences: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_templates")
async def get_templates():
    """Endpoint per ottenere tutti i template disponibili"""
    return template_manager.get_all_templates()

@app.get("/get_template_sequence")
async def get_template_sequence():
    """Endpoint per ottenere la sequenza dei template"""
    return template_manager.get_template_sequence()




