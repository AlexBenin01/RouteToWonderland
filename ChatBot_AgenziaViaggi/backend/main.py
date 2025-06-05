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
from librerie.master_template_lib import MasterTemplateManager
from librerie.template_manager import TemplateManager
from librerie.riepilogo import process_riepilogo
import logging
import sys

# Configura il logger per gestire correttamente i caratteri Unicode
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    encoding='utf-8'
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

# Dizionario per mantenere il contesto della conversazione per ogni template
CONTESTO_CONVERSAZIONE = {}

# Contatore per le richieste di uscita
EXIT_COUNTER = 0

# Lista dei template obbligatori
TEMPLATE_OBBLIGATORI = ["intro", "contatti", "trasporto"]

# Inizializzazione del TemplateManager e caricamento dei template
template_manager = TemplateManager()
template_manager.load_templates()
template_manager.set_active_template("intro")
template_manager.update_template_sequence(["intro", "contatti","trasporto"])

ollama_manager = OllamaManager()
nu_extract = NuExtract()
master_template_manager = MasterTemplateManager()

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

def create_empty_template(empty: Dict[str, Any]) -> Dict[str, Any]:
    template_vuoto = {key: None for key in empty.keys()}
    logger.info(f"Template vuoto creato: {template_vuoto}")
    return template_vuoto

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

def aggiorna_contesto_conversazione(template_attivo: str, messaggio_utente: str, risposta_bot: str):
    """
    Aggiorna il contesto della conversazione per il template attivo
    
    Args:
        template_attivo: Il template attivo
        messaggio_utente: Il messaggio dell'utente
        risposta_bot: La risposta del bot
    """
    global CONTESTO_CONVERSAZIONE
    
    # Inizializza il contesto per tutti i template se non esiste
    for template in template_manager.get_template_sequence():
        if template not in CONTESTO_CONVERSAZIONE:
            CONTESTO_CONVERSAZIONE[template] = []
    
    # Aggiungi il nuovo scambio al contesto del template attivo
    CONTESTO_CONVERSAZIONE[template_attivo].append({
        "utente": messaggio_utente,
        "bot": risposta_bot
    })
    
    logger.info(f"Contesto aggiornato per il template {template_attivo}")
    logger.debug(f"Nuovo contesto: {CONTESTO_CONVERSAZIONE[template_attivo]}")

def get_contesto_conversazione(template_attivo: str) -> str:
    """
    Ottiene il contesto della conversazione per il template attivo
    
    Args:
        template_attivo: Il template attivo
        
    Returns:
        str: Il contesto della conversazione formattato
    """
    # Inizializza il contesto per tutti i template se non esiste
    for template in template_manager.get_template_sequence():
        if template not in CONTESTO_CONVERSAZIONE:
            CONTESTO_CONVERSAZIONE[template] = []
    
    if template_attivo not in CONTESTO_CONVERSAZIONE:
        return ""
    
    contesto = []
    for scambio in CONTESTO_CONVERSAZIONE[template_attivo]:
        contesto.append(f"Utente: {scambio['utente']}")
        contesto.append(f"Bot: {scambio['bot']}")
    
    return "\n".join(contesto)

@app.post("/extract_simple")
async def extract_simple(request: SimpleRequest):
    global STATO_CONVERSAZIONE_JSON, EXIT_COUNTER
    
    logger.info("\n=== INIZIO RICHIESTA EXTRACT_SIMPLE ===")
    logger.info(f"Testo ricevuto: {request.text}")
    logger.info(f"Template attivo: {template_manager.active_template}")
    logger.info(f"Sequenza template: {template_manager.get_template_sequence()}")
    
    try:
        # Carica lo stato attuale
        stato_attuale = json.loads(STATO_CONVERSAZIONE_JSON)
        logger.info(f"Stato attuale: {stato_attuale}")
        
        # Ottieni il template attivo
        template_attivo = stato_attuale.get(template_manager.active_template, create_empty_template(template_manager.get_active_template()))
        logger.info(f"Template attivo corrente: {template_attivo}")
        
        # Ottieni il contesto della conversazione
        contesto = get_contesto_conversazione(template_manager.active_template)
        logger.info(f"Contesto della conversazione: {contesto}")
        
        # Prepara il testo completo includendo il contesto
        testo_completo = f"{contesto}\nUtente: {request.text}" if contesto else request.text
        logging.info(f"testo_completo della conversazione: {testo_completo}")
        # Estrai le informazioni dal testo usando NuExtract
        template_aggiornato = nu_extract.process_extraction(
            text=testo_completo, 
            empty_template=template_manager.get_active_template(),
            saved_template=template_attivo
        )

        # Aggiorna il template master con le nuove informazioni
        # Processa il template master con NuExtract solo se template_attivo è "intro"
        
        if template_manager.active_template == "intro":
            master_template = master_template_manager.process_extraction(testo_completo)

        template_modificato = False
        
        # Confronta template_aggiornato con template_attivo
        logger.info("=== INIZIO CONFRONTO TEMPLATE ===")
        logger.info(f"Template attivo: {json.dumps(template_attivo, ensure_ascii=False, indent=2)}")
        logger.info(f"Template aggiornato: {json.dumps(template_aggiornato, ensure_ascii=False, indent=2)}")
        
        # Se template_attivo è vuoto, consideriamo il template come modificato
        if not template_attivo:
            logger.info("Template attivo vuoto - Template modificato")
            template_modificato = True
        else:
            # Verifica se ci sono chiavi nuove in template_aggiornato
            nuove_chiavi = set(template_aggiornato.keys()) - set(template_attivo.keys())
            if nuove_chiavi:
                logger.info(f"Trovate nuove chiavi: {nuove_chiavi} - Template modificato")
                template_modificato = True
            else:
                # Confronta i valori per ogni chiave esistente
                for key in template_attivo:
                    if key not in template_aggiornato:
                        logger.info(f"Chiave {key} mancante in template_aggiornato - Template modificato")
                        template_modificato = True
                        break
                        
                    valore_aggiornato = template_aggiornato[key]
                    valore_attivo = template_attivo[key]
                    
                    logger.info(f"\nConfronto chiave: {key}")
                    logger.info(f"Valore aggiornato: {valore_aggiornato}")
                    logger.info(f"Valore attivo: {valore_attivo}")
                    
                    # Confronto diretto dei valori, indipendentemente dal tipo
                    if valore_aggiornato != valore_attivo:
                        logger.info(f"Valori diversi per la chiave {key} - Template modificato")
                        template_modificato = True
                        break
                    else:
                        logger.info(f"Valori uguali per la chiave {key}")
        
        logger.info(f"=== FINE CONFRONTO TEMPLATE - Template modificato: {template_modificato} ===")
        logger.info(f"Template aggiornato: {template_aggiornato}")
        if not template_modificato:
            logger.info("Nessuna modifica al template, verifica se è una richiesta di uscita")
            # Verifica se è una richiesta di uscita
            template_exit = nu_extract.process_exit(
                text=request.text,
                empty_template=template_manager.get_exit_template()
            )
            
            if template_exit is None or template_exit == 'null':
                logger.info("Imposto template_exit = False")
                template_exit = False

            if template_exit or EXIT_COUNTER >= 1:
                logger.info("Richiesta di uscita o nessuna modifica per due volte consecutive")
                if template_manager.active_template in TEMPLATE_OBBLIGATORI:
                    logger.info("Template obbligatorio, invio risposta personalizzata")
                    risposta = ollama_manager.campi_obbligatori()
                    response = {
                        "guide_phrase": risposta,
                        "template_usato": template_manager.active_template,
                        "stato_conversazione": stato_attuale,
                        "exit": False
                    }
                    logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE (risposta personalizzata) ===")
                    return response
                else:
                    logger.info("Richiesta di uscita template_exit:True")
                    EXIT_COUNTER = 0  # Reset del contatore se è una richiesta di uscita valida
                    risposta = ollama_manager.get_exit()
                    logger.info(risposta)
                    response = {
                        "guide_phrase": risposta,
                        "template_usato": template_manager.active_template,
                        "stato_conversazione": stato_attuale,
                        "exit": True
                    }
                    logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE (cambio template) ===")
                    return response
            else:
                EXIT_COUNTER += 1
                if EXIT_COUNTER >= 2:
                    logger.info("Raggiunto il limite di tentativi, verifica se template obbligatorio")
                    if template_manager.active_template in TEMPLATE_OBBLIGATORI:
                        logger.info("Template obbligatorio, invio risposta personalizzata")
                        risposta = ollama_manager.campi_obbligatori()
                        response = {
                            "guide_phrase": risposta,
                            "template_usato": template_manager.active_template,
                            "stato_conversazione": stato_attuale,
                            "exit": False
                        }
                        logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE (risposta personalizzata) ===")
                        return response
                    else:
                        logger.info("Richiesta di uscita")
                        risposta = ollama_manager.get_exit()
                        logger.info(risposta)
                        response = {
                            "guide_phrase": risposta,
                            "template_usato": template_manager.active_template,
                            "stato_conversazione": stato_attuale,
                            "exit": True
                        }
                        logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE (cambio template) ===")
                        return response
                else:
                    logger.info(f"Tentativo {EXIT_COUNTER} di 2, continuo con la conversazione")
                    risposta = ollama_manager.get_response(
                        template_type=template_manager.active_template,
                        template=template_aggiornato
                    )
                    response = {
                        "guide_phrase": risposta,
                        "template_usato": template_manager.active_template,
                        "stato_conversazione": stato_attuale,
                        "exit": False
                    }
                    logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE (cambio template) ===")
                    return response

        EXIT_COUNTER = 0  # Reset del contatore se ci sono state modifiche al template
        # Ottieni l'istanza del template corrente
        logger.info("Aggiornamento stato conversazione")
        stato_attuale[template_manager.active_template] = template_aggiornato
        STATO_CONVERSAZIONE_JSON = json.dumps(stato_attuale, ensure_ascii=False)
        logger.info(f"Stato aggiornato per il template {template_manager.active_template}")
        logger.info(f"Stato completo: {STATO_CONVERSAZIONE_JSON}")
        current_template = templates.get(template_manager.active_template)
        if current_template:
            logger.info(f"Tipo di current_template: {type(current_template)}")
            logger.info(f"Classi base di current_template: {type(current_template).__bases__}")
            # Verifica il template usando il metodo della classe base
            template_aggiornato, template_modificato, warnings, errors = current_template.verifica_template(template_aggiornato)
            if errors:
                logger.warning(f"Errori nel template {template_manager.active_template}: {errors}")
            if warnings:
                logger.warning(f"Warning nel template {template_manager.active_template}: {warnings}")
        else:
            warnings = []
            errors = []
        logger.info("template modificato: %s", template_modificato)
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
        
        while template_completo:
            logger.info(f"Template {template_manager.active_template} completato")
            # Aggiorna il contesto della conversazione
            aggiorna_contesto_conversazione(template_manager.active_template, request.text, "")

            # Gestione speciale per il template intro
            if template_manager.active_template == "intro":

                # Processa il template intro con i dati dal master
                template_aggiornato = master_template_manager.process_template(
                    template_manager.active_template,
                    template_aggiornato
                )

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

                # Processa il nuovo template con i dati dal master
                empty_template = master_template_manager.process_template(
                    template_manager.active_template,
                    empty_template
                )

                # Verifica il template usando il metodo della classe base
                current_template = templates.get(template_manager.active_template)
                if current_template:
                    logger.info(f"Verifica template {template_manager.active_template}")
                    empty_template, template_modificato, warnings, errors = current_template.verifica_template(empty_template)
                    if errors:
                        logger.warning(f"Errori nel template {template_manager.active_template}: {errors}")
                    if warnings:
                        logger.warning(f"Warning nel template {template_manager.active_template}: {warnings}")
                else:
                    warnings = []
                    errors = []

                # Aggiorna lo stato della conversazione
                
                logger.info("Aggiornamento stato conversazione")
                stato_attuale[template_manager.active_template] = empty_template
                STATO_CONVERSAZIONE_JSON = json.dumps(stato_attuale, ensure_ascii=False)
                logger.info(f"Stato aggiornato per il template {template_manager.active_template}")
                logger.info(f"Stato completo: {STATO_CONVERSAZIONE_JSON}")

                # Verifica se il template è completo usando il metodo della classe base
                template_completo = all(
                    campo in empty_template and (
                        empty_template[campo] is not None and 
                        (isinstance(empty_template[campo], bool) or empty_template[campo])
                    )
                    for campo in template_manager.get_active_template().keys()
                )
                logger.info(f"Template completo: {template_completo}")
                if not template_completo:
                    logger.info(f"Il template {next_template} non è completo, continuazione con il nuovo template")
                    
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
                        "exit": False
                    }
                    logger.info("=== FINE RICHIESTA EXTRACT_SIMPLE (cambio template) ===")
                    return response
            else:
                logger.info("Non ci sono più template nella sequenza")
                riepilogo = await get_summary()
                return {
                    "guide_phrase": "Hai completato tutti i template disponibili. Ecco il riepilogo completo:",
                    "template_usato": template_manager.active_template,
                    "stato_conversazione": stato_attuale,
                    "nuovo_template": False,
                    "exit": False,
                    "riepilogo": riepilogo
                }
        
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
        
        # Aggiorna il contesto della conversazione
        aggiorna_contesto_conversazione(template_manager.active_template, request.text, risposta)
        
        # Prepara la risposta finale
        response = {
            "guide_phrase": risposta,
            "template_usato": template_manager.active_template,
            "stato_conversazione": stato_attuale,
            "exit": False
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
        "sequenza_template": template_manager.get_template_sequence(),
        "contesto_conversazione": CONTESTO_CONVERSAZIONE
    }

@app.post("/evaluate_preferences")
async def evaluate_preferences(request: TravelPreferenceRequest):
    logger.info("Inizio valutazione preferenze")
    logger.debug(f"Preferenze ricevute: {request.dict()}")
    
    try:
        # Converti la richiesta in formato JSON
        preference_json = request.dict()
        
        # Chiama il servizio Drools per ottenere i template attivi
        active_templates = await drools_service.evaluate_Templates(preference_json)
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

@app.post("/skip_template")
async def skip_template():
    """Endpoint per saltare il template corrente e passare al successivo"""
    global STATO_CONVERSAZIONE_JSON, EXIT_COUNTER
    
    logger.info("\n=== INIZIO RICHIESTA SKIP_TEMPLATE ===")
    logger.info(f"Template attivo prima del salto: {template_manager.active_template}")
    
    try:
        # Carica lo stato attuale
        stato_attuale = json.loads(STATO_CONVERSAZIONE_JSON)
        
        # Ottieni l'indice del template corrente
        current_index = template_manager.get_template_sequence().index(template_manager.active_template)
        
        if current_index < len(template_manager.get_template_sequence()) - 1:
            # Ottieni il prossimo template
            next_template = template_manager.get_template_sequence()[current_index + 1]
            logger.info(f"Passaggio al prossimo template: {next_template}")
            
            # Cambia il template attivo
            template_manager.set_active_template(next_template)
            
            # Ottieni il template vuoto per il nuovo template
            empty_template = get_empty_template(template_manager.get_active_template())
            
            # Processa il nuovo template con i dati dal master
            empty_template = master_template_manager.process_template(
                template_manager.active_template,
                empty_template
            )
            
            # Verifica il template usando il metodo della classe base
            current_template = templates.get(template_manager.active_template)
            if current_template:
                logger.info(f"Verifica template {template_manager.active_template}")
                empty_template, template_modificato, warnings, errors = current_template.verifica_template(empty_template)
                if errors:
                    logger.warning(f"Errori nel template {template_manager.active_template}: {errors}")
                if warnings:
                    logger.warning(f"Warning nel template {template_manager.active_template}: {warnings}")
            else:
                warnings = []
                errors = []
            
            # Verifica se il template è già completo
            template_completo = all(
                campo in empty_template and (
                    empty_template[campo] is not None and 
                    (isinstance(empty_template[campo], bool) or empty_template[campo])
                )
                for campo in template_manager.get_active_template().keys()
            )
            
            # Aggiorna lo stato della conversazione
            stato_attuale[template_manager.active_template] = empty_template
            STATO_CONVERSAZIONE_JSON = json.dumps(stato_attuale, ensure_ascii=False)
            
            # Resetta il contatore di uscita
            EXIT_COUNTER = 0
            
            if template_completo:
                logger.info(f"Il template {next_template} è già completo grazie al master template")
                # Se il template è completo, passa automaticamente al successivo
                return await skip_template()
            
            # Ottieni la risposta iniziale per il nuovo template
            try:
                risposta = ollama_manager.get_response(
                    template_type=template_manager.active_template,
                    template=empty_template
                )
            except Exception as e:
                logger.error(f"Errore nella generazione della risposta per il nuovo template: {str(e)}")
                risposta = f"Benvenuto al template {next_template}. Come posso aiutarti?"
            
            response = {
                "guide_phrase": risposta,
                "template_usato": template_manager.active_template,
                "stato_conversazione": stato_attuale,
                "nuovo_template": True,
                "next_template": next_template,
                "exit": False
            }
            
            logger.info("=== FINE RICHIESTA SKIP_TEMPLATE ===")
            return response
        else:
            logger.info("Non ci sono più template nella sequenza")
            riepilogo = await get_summary()
            return {
                "guide_phrase": "Hai completato tutti i template disponibili. Ecco il riepilogo completo:",
                "template_usato": template_manager.active_template,
                "stato_conversazione": stato_attuale,
                "nuovo_template": False,
                "exit": False,
                "riepilogo": riepilogo
            }
            
    except Exception as e:
        logger.error(f"Errore in skip_template: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/get_continue")
async def get_continue():
    """Endpoint per riproporre la domanda del primo campo libero del template attivo"""
    global STATO_CONVERSAZIONE_JSON
    
    logger.info("\n=== INIZIO RICHIESTA GET_CONTINUE ===")
    logger.info(f"Template attivo: {template_manager.active_template}")
    
    try:
        # Carica lo stato attuale
        stato_attuale = json.loads(STATO_CONVERSAZIONE_JSON)
        logger.info(f"Stato attuale: {json.dumps(stato_attuale, ensure_ascii=False, indent=2)}")
        
        # Ottieni il template attivo
        template_attivo = stato_attuale.get(template_manager.active_template, {})
        logger.info(f"Template attivo corrente: {json.dumps(template_attivo, ensure_ascii=False, indent=2)}")
        
        # Ottieni il template vuoto per il template attivo
        empty_template = get_empty_template(template_manager.get_active_template())
        logger.info(f"Template vuoto: {json.dumps(empty_template, ensure_ascii=False, indent=2)}")
        
        # Ottieni la risposta da Ollama per il primo campo libero
        try:
            logger.info("Richiesta risposta a Ollama...")
            risposta = ollama_manager.get_response(
                template_type=template_manager.active_template,
                template=template_attivo
            )
            logger.info(f"Risposta ottenuta da Ollama: {risposta}")
        except Exception as ollama_error:
            logger.error(f"Errore nella comunicazione con Ollama: {str(ollama_error)}")
            risposta = f"Mi dispiace, sto riscontrando alcuni problemi tecnici. Potresti ripetere la tua richiesta?"
        
        response = {
            "guide_phrase": risposta,
            "template_usato": template_manager.active_template,
            "stato_conversazione": stato_attuale,
            "exit": False
        }
        
        logger.info(f"Risposta finale: {json.dumps(response, ensure_ascii=False, indent=2)}")
        logger.info("=== FINE RICHIESTA GET_CONTINUE ===")
        return response
        
    except Exception as e:
        logger.error(f"Errore in get_continue: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_summary")
async def get_summary():
    """Endpoint per ottenere il riepilogo completo di tutti i template"""
    global STATO_CONVERSAZIONE_JSON
    
    logger.info("\n=== INIZIO RICHIESTA GET_SUMMARY ===")
    
    try:
        # Copia la sequenza dei template
        template_sequence = template_manager.get_template_sequence().copy()
        logger.info(f"Sequenza template copiata: {template_sequence}")
        
        # Copia lo stato della conversazione
        stato_attuale = json.loads(STATO_CONVERSAZIONE_JSON)
        logger.info(f"Stato conversazione copiato: {json.dumps(stato_attuale, ensure_ascii=False, indent=2)}")
        
        # Ottieni l'indice del template attivo
        current_index = template_sequence.index(template_manager.active_template)
        logger.info(f"Indice template attivo: {current_index}")
        
        # Per ogni template successivo a quello attivo nella sequenza
        for template_name in template_sequence[current_index + 1:]:
            # Ottieni il template vuoto
            empty_template = get_empty_template(template_manager.get_template(template_name))
            
            # Processa il template con i dati dal master
            completed_template = master_template_manager.process_template(
                template_name,
                empty_template
            )
            
            # Aggiorna lo stato della conversazione con il template completato
            stato_attuale[template_name] = completed_template
            
            logger.info(f"Template {template_name} completato e aggiunto al riepilogo")
        
        logger.info(f"Stato aggiornato per il riepilogo: {json.dumps(stato_attuale, ensure_ascii=False, indent=2)}")
        
        # Processa il riepilogo completo
        riepilogo_elaborato = process_riepilogo(json.dumps(stato_attuale))
        logger.info("Riepilogo elaborato con successo")
        
        # Pulisci i dati rimuovendo le chiavi con valori vuoti
        def clean_empty_dicts(data):
            if isinstance(data, dict):
                return {
                    k: clean_empty_dicts(v)
                    for k, v in data.items()
                    if v != {} and v is not None
                }
            elif isinstance(data, list):
                return [clean_empty_dicts(item) for item in data if item != {} and item is not None]
            return data
        
        riepilogo_pulito = clean_empty_dicts(riepilogo_elaborato)
        logger.info("Riepilogo pulito dai dati vuoti")
        logger.info(f"Riepilogo finale: {json.dumps(riepilogo_pulito, ensure_ascii=False, indent=2)}")
        
        # Prepara la risposta con il riepilogo e la flag
        response = {
            "data": riepilogo_pulito,
            "show_summary": True  # flag per indicare che deve essere mostrato nella pagina riepilogo
        }
        
        logger.info("=== FINE RICHIESTA GET_SUMMARY ===")
        return response
        
    except Exception as e:
        logger.error(f"Errore in get_summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))






