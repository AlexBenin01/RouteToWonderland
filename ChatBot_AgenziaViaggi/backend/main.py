# backend/main.py
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import json
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from librerie.ollama_lib import OllamaManager
from librerie.NuEstractLib import NuExtract
from librerie.intro_lib import IntroTemplate
from services.drools_service import DroolsService
import logging

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
    allow_origins=["*"],  # oppure ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # Consenti tutti i metodi
    allow_headers=["*"],  # Consenti tutti gli header
)

# Inizializza i manager
ollama_manager = OllamaManager()
nu_extract = NuExtract()
intro_template = IntroTemplate()

 # Prepara la risposta
response = {
            "guide_phrase": "",
            "template_usato": "",
            "stato_conversazione": "",
            "warnings": [],
            "errors": [],
            "next_template": "",
            "nuovo_template": False
        }

# Carica i template dai file JSON
def load_template(template_name: str) -> Dict[str, Any]:
    template_path = f"template/{template_name}.json"
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Errore nel caricamento del template {template_name}: {str(e)}")
        return {}

# Carica tutti i template
TEMPLATES = {
    "intro": load_template("intro"),
    "contatti": load_template("contatti"),
    "alloggi": load_template("alloggi"),
    "noleggi": load_template("noleggi"),
    "naturalistico": load_template("naturalistico"),
    "avventura": load_template("avventura"),
    "montagna": load_template("montagna"),
    "mare": load_template("mare"),
    "gastronomia": load_template("gastronomia"),
    "citta_arte": load_template("citta_arte"),
    "benessere": load_template("benessere")
}



# Variabile globale per il template attivo
TEMPLATE_ATTIVO = "intro"
# Variabile globale per lo stato della conversazione in formato JSON
STATO_CONVERSAZIONE_JSON = "{}"
# Sequenza dei template (inizialmente vuota, verrà popolata dalle regole Drools)
TEMPLATES_SEQUENCE = ["intro", "contatti"]


# Estrai le chiavi dai template
TEMPLATE_KEYS = {
    template_name: list(template.keys())
    for template_name, template in TEMPLATES.items()
}

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

@app.post("/extract_simple")
async def extract_simple(request: SimpleRequest):
    global STATO_CONVERSAZIONE_JSON, TEMPLATE_ATTIVO, TEMPLATES_SEQUENCE
    
    logger.info(f"Ricevuta richiesta extract_simple con testo: {request.text}")
    logger.info(f"Template attivo: {TEMPLATE_ATTIVO}")
    
    try:
        # Carica lo stato attuale
        stato_attuale = json.loads(STATO_CONVERSAZIONE_JSON)
        logger.debug(f"Stato attuale: {stato_attuale}")
        
        # Ottieni il template attivo o inizializzalo se non esiste
        template_attivo = stato_attuale.get(TEMPLATE_ATTIVO)
        if template_attivo is None:
            template_attivo = {}
            stato_attuale[TEMPLATE_ATTIVO] = template_attivo
            STATO_CONVERSAZIONE_JSON = json.dumps(stato_attuale, ensure_ascii=False)
        
        logger.debug(f"Template attivo: {template_attivo}")
        
        # Estrai le informazioni dal testo usando NuExtract
        template_aggiornato, template_modificato = nu_extract.process_extraction(
            text=request.text,
            empty_template=TEMPLATES[TEMPLATE_ATTIVO],
            saved_template=template_attivo
        )
        logger.info(f"Template modificato: {template_modificato}")
        logger.info(f"Template aggiornato: {template_aggiornato}")
        
        # Se il template è "intro", verifica tutti i campi
        errors = []
        warnings = []
        if TEMPLATE_ATTIVO == "intro":

            template_aggiornato, warnings, errors = intro_template.verifica_template(template_aggiornato)
            if errors:
                logger.warning(f"Errori nel template intro: {errors}")
        
        # Aggiorna lo stato solo se ci sono state modifiche
        if template_modificato:
            stato_attuale[TEMPLATE_ATTIVO] = template_aggiornato
            STATO_CONVERSAZIONE_JSON = json.dumps(stato_attuale, ensure_ascii=False)
            logger.info(f"Stato aggiornato per il template {TEMPLATE_ATTIVO}")
            logger.info(f"Stato aggiornato: {STATO_CONVERSAZIONE_JSON}")
            logger.info(f"Stato aggiornato per il dato {template_aggiornato}")
            
        
         # Verifica se il template è completo
        template_completo = all(
            campo in template_aggiornato and template_aggiornato[campo]
            for campo in TEMPLATES[TEMPLATE_ATTIVO].keys()
        )
        
        if template_completo:
            logger.info(f"Template {TEMPLATE_ATTIVO} completato")
            # Se il template "intro" è completo, chiama evaluate_preferences
            if TEMPLATE_ATTIVO == "intro":
                logger.info("Template intro completato, chiamata a evaluate_preferences")
                # Prepara la richiesta per evaluate_preferences
                preference_request = TravelPreferenceRequest(**template_aggiornato)
                # Chiama evaluate_preferences per aggiornare la sequenza
                await evaluate_preferences(preference_request)
            
            # Trova il prossimo template nella sequenza
            current_index = TEMPLATES_SEQUENCE.index(TEMPLATE_ATTIVO)
            if current_index < len(TEMPLATES_SEQUENCE) - 1:
                next_template = TEMPLATES_SEQUENCE[current_index + 1]
                risposta = ollama_manager.get_response(
                template_type=TEMPLATE_ATTIVO,
                template=template_aggiornato
                )
                response = {
                "guide_phrase": risposta,
                "template_usato": TEMPLATE_ATTIVO,
                "stato_conversazione": stato_attuale,
                "nuovo_template": True,
                "next_template": next_template,
                "warnings": warnings if TEMPLATE_ATTIVO == "intro" else [],
                "errors": errors if TEMPLATE_ATTIVO == "intro" else []
                }
                logger.info(f"Prossimo template: {next_template}")
                return response
        
        # Ottieni la risposta da Ollama
        try:
            risposta = ollama_manager.get_response(
                template_type=TEMPLATE_ATTIVO,
                template=template_aggiornato
            )
            logger.info(f"Risposta ottenuta da Ollama: {risposta}")
        except Exception as ollama_error:
            logger.error(f"Errore nella comunicazione con Ollama: {str(ollama_error)}")
            # Risposta di fallback basata sul template attivo
            if TEMPLATE_ATTIVO == "intro":
                if errors:
                    risposta = "Mi dispiace, non ho capito bene. Potresti fornirmi più dettagli sulla destinazione del tuo viaggio?"
                else:
                    risposta = "Benvenuto! Sono qui per aiutarti a pianificare il tuo viaggio. Puoi dirmi dove vorresti andare?"
            else:
                risposta = "Mi dispiace, sto riscontrando alcuni problemi tecnici. Potresti ripetere la tua richiesta?"
        
        # Prepara la risposta finale
        response = {
            "guide_phrase": risposta,
            "template_usato": TEMPLATE_ATTIVO,
            "stato_conversazione": stato_attuale,
            "warnings": warnings if TEMPLATE_ATTIVO == "intro" else [],
            "errors": errors if TEMPLATE_ATTIVO == "intro" else []
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Errore in extract_simple: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set_template")
def set_template(request: TemplateChangeRequest):
    global TEMPLATE_ATTIVO
    logger.info(f"Richiesta cambio template a: {request.template_type}")
    
    if request.template_type not in TEMPLATES:
        logger.error(f"Template non valido: {request.template_type}")
        raise HTTPException(status_code=400, detail="Template non valido")
    
    TEMPLATE_ATTIVO = request.template_type
    logger.info(f"Template attivo aggiornato a: {TEMPLATE_ATTIVO}")
    return {"template_attivo": TEMPLATE_ATTIVO}

@app.get("/debug_stato")
def debug_stato():
    global STATO_CONVERSAZIONE_JSON
    logger.info("Richiesta debug_stato")
    stato = json.loads(STATO_CONVERSAZIONE_JSON)
    return {
        "stato_conversazione": stato,
        "template_attivo": TEMPLATE_ATTIVO,
        "sequenza_template": TEMPLATES_SEQUENCE
    }

@app.post("/evaluate_preferences")
async def evaluate_preferences(request: TravelPreferenceRequest):
    global TEMPLATES_SEQUENCE
    
    logger.info("Inizio valutazione preferenze")
    logger.debug(f"Preferenze ricevute: {request.dict()}")
    
    try:
        # Converti la richiesta in formato JSON
        preference_json = request.dict()
        
        # Chiama il servizio Drools per ottenere i template attivi
        active_templates = await DroolsService.evaluate_preferences(preference_json)
        logger.info(f"Template attivi ottenuti da Drools: {active_templates}")
        
        # Crea una nuova sequenza di template basata sui template attivi
        # Mantieni sempre "intro" e "contatti" all'inizio
        new_sequence = ["intro", "contatti"]
        
        # Aggiungi i template attivi in ordine
        for template in active_templates:
            if template not in new_sequence:
                new_sequence.append(template)
        
        # Aggiorna la sequenza globale
        TEMPLATES_SEQUENCE = new_sequence
        logger.info(f"Nuova sequenza template: {TEMPLATES_SEQUENCE}")
        
        return {
            "active_templates": active_templates,
            "new_sequence": TEMPLATES_SEQUENCE,
            "message": "Sequenza dei template aggiornata con successo"
        }
        
    except Exception as e:
        logger.error(f"Errore in evaluate_preferences: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




