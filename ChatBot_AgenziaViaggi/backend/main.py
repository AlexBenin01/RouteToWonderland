# backend/main.py
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import NuEstractLib
import json
from pydantic import BaseModel

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

# Carica il modello una volta sola
model_path = './NuExtract-2-2B-experimental'

# Template per l'introduzione
TEMPLATE_INTRO = """{
  "destinazione": "nome della città o località di destinazione",
  "numero_partecipanti": "numero totale di persone che parteciperanno al viaggio",
  "data_partenza": "data prevista per la partenza, nel formato YYYY-MM-DD",
  "data_ritorno": "data prevista per il ritorno, nel formato YYYY-MM-DD",
  "budget_viaggio": "budget totale previsto per il viaggio, in numero"
}"""


# Template per i luoghi
TEMPLATE_LUOGHI = """{
      "nome_luogo": "nome del luogo da visitare ( museo, monumento, città, piazza, chiesa, etc)",
      "richiesta_guida": "true se si desidera una guida turistica, altrimenti false",
      "lingua_guida": "lingua preferita per la guida turistica",
      "attivita_extra": "attività aggiuntive richieste, elencate come singole frasi o parole (es. 'visita in cantina', 'crociera al tramonto')",
      "partecipanti_visita": "numero di persone che parteciperanno a questa attività",
      "orario_visita": "indica la data e l'orario precisi della visita, nel formato anno-mese-giornoTora:minuti, ad esempio: 2025-05-07T14:30"
}"""


# Template per gli alloggi
TEMPLATE_ALLOGGI = """{
  "tipo_alloggio": "tipo della struttura ricettiva in cui soggiorna il paziente, ad esempio: hotel, bed and breakfast, appartamento, agriturismo",
  "zona_struttura": "zona o quartiere in cui si trova la struttura (es. centro città, zona stazione, vicino all'ospedale)"
}
"""


# Template per i noleggi
TEMPLATE_NOLEGGI = """{
  "richiesta_auto": "true se è richiesto un noleggio auto, false se non serve",
  "posti_auto": "numero minimo di posti richiesti",
  "tipo_auto": "preferenze sul tipo di veicolo (es. elettrica, SUV, automatico, marca specifica come Ferrari, etc)",
  "budget_auto": "budget massimo disponibile per il noleggio"
}"""

# Template per i contatti
TEMPLATE_CONTATTI = """{
  "nominativo_completo": "Nome e cognome della persona così come appaiono nel testo, inclusi eventuali titoli o formule di cortesia (es. 'Dott.ssa Maria Bianchi').",
  "nome": "Il nome proprio della persona (es. Maria, Giovanni), da estrarre anche se incluso nel nome completo o preceduto da formule di cortesia come 'Sig.', 'Sig.ra', 'Dott.', ecc.",
  "cognome": "Il cognome della persona (es. Rossi, Bianchi), da estrarre anche se incluso nel nome completo o seguito da titoli (es. 'Rossi' in 'Dott. Giovanni Rossi').",
  "numero_cellulare": "Il campo numero_cellulare deve contenere solo il numero di telefono cellulare, idealmente con prefisso internazionale (es. +39 XXX XXXXXXX). Escludere qualsiasi testo aggiuntivo come 'cell:', 'tel.:'.",
  "email": "Il campo email deve contenere solo l'indirizzo email valido per comunicazioni (es. utente@dominio.it). Escludere qualsiasi testo aggiuntivo come 'email:', 'posta elettronica:'.",
  "note_aggiuntive": "Eventuali osservazioni personali, preferenze o qualsiasi altra informazione rilevante non catturata dagli altri campi."
}"""
 


# Centralizza i template in un dizionario
TEMPLATES = {
    "intro": TEMPLATE_INTRO,
    "luoghi": TEMPLATE_LUOGHI,
    "alloggi": TEMPLATE_ALLOGGI,
    "noleggi": TEMPLATE_NOLEGGI,
    "contatti": TEMPLATE_CONTATTI,
}



# Sequenza dei template
TEMPLATES_SEQUENCE = ["intro", "luoghi", "alloggi", "noleggi", "contatti"]

# Chiavi richieste per ogni template
TEMPLATE_KEYS = {
    "intro": ["destinazione", "numero_partecipanti", "data_partenza", "data_ritorno", "budget_viaggio"],
    "luoghi": ["nome_luogo","partecipanti_visita","orario_visita","richiesta_guida","lingua_guida","attivita_extra"],
    "alloggi": ["tipo_alloggio", "zona_struttura"],
    "noleggi": ["richiesta_auto", "posti_auto", "tipo_auto", "budget_auto"],
    "contatti": ["nominativo_completo", "nome", "cognome", "numero_cellulare", "email", "note_aggiuntive"],
}

# Frasi guida per ogni chiave
GUIDE_PHRASES = {
    "intro": {
        "destinazione": "Che bello! Dove ti piacerebbe andare? Dimmi la destinazione e cominciamo a immaginare il viaggio.",
        "numero_partecipanti": "Va benissimo! Quante persone partiranno con te? Così possiamo adattare tutto alle vostre esigenze.",
        "data_partenza": "Fantastico! Quando vuoi partire? Con la data di inizio possiamo iniziare a costruire l'itinerario.",
        "data_ritorno": "Perfetto! Quando pensi di rientrare? Così possiamo definire bene la durata del viaggio.",
        "budget_viaggio": "Benissimo! Hai un budget a disposizione? Mi aiuterà a proporti le soluzioni più adatte.",
    },
    "luoghi": {
        "nome_luogo": "Qual è il prossimo luogo che vorresti visitare? (Es. museo, monumento, città...)",
        "partecipanti_visita": "Quante persone parteciperanno a questa visita?",
        "orario_visita": "Quando vorresti fare questa visita? Indica data e orario.",
        "richiesta_guida": "Vuoi una guida turistica per questa visita? Rispondi sì o no.",
        "lingua_guida": "Se desideri una guida, in quale lingua preferisci che sia?",
        "attivita_extra": "Ci sono attività extra che ti piacerebbe aggiungere per questa tappa? (Es. escursioni, degustazioni...)"
    },
    "alloggi": {
        "tipo_alloggio": "Perfetto! Hai una preferenza per il tipo di alloggio? (Es. hotel, B&B, appartamento...)",
        "zona_struttura": "Va bene! Conosci la zona o la città? Mi sarà utile per cercare opzioni vicine.",
    },
    "noleggi": {
        "richiesta_auto": "Chiaro! Hai bisogno di un'auto a noleggio per gli spostamenti?",
        "posti_auto": "Perfetto, quante persone devono starci in macchina? Così valutiamo le giuste dimensioni.",
        "tipo_auto": "Bene! Hai preferenze sul tipo di veicolo? Come ad esempio SUV, elettrica o cambio automatico?",
        "budget_auto": "Capito! Hai un budget massimo per il noleggio? Mi aiuterà a filtrare le opzioni.",
    },
    "contatti": {
        "nome": "Come ti chiami?",
        "cognome": "E il tuo cognome?",
        "numero_cellulare": "Perfetto! Hai un numero di cellulare da lasciarmi in caso servisse contattarti?",
        "email": "Benissimo! Qual è il tuo indirizzo email per inviarti le informazioni?",
        "note_aggiuntive": "Se vuoi, raccontami qualcosa di personale o qualche dettaglio extra che può aiutarmi a creare qualcosa su misura per te."
    },
}

# Variabile globale per il template attivo
TEMPLATE_ATTIVO = "intro"
# Variabile globale per lo stato della conversazione in formato JSON
STATO_CONVERSAZIONE_JSON = "{}"

class SimpleRequest(BaseModel):
    text: str
    campo: str = None

class TemplateChangeRequest(BaseModel):
    template_type: str

@app.post("/extract_simple")
def extract_simple(request: SimpleRequest):
    global STATO_CONVERSAZIONE_JSON
    # Delega tutta la logica a NuEstractLib
    try:
        result = NuEstractLib.process_extraction(
            text=request.text,
            template_attivo=TEMPLATE_ATTIVO,
            stato_conversazione_json=STATO_CONVERSAZIONE_JSON,
            templates=TEMPLATES,
            template_keys=TEMPLATE_KEYS,
            guide_phrases=GUIDE_PHRASES,
            model_path=model_path,
            campo=request.campo
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # Aggiorna lo stato globale solo se è cambiato
    stato_precedente = json.loads(STATO_CONVERSAZIONE_JSON)
    STATO_CONVERSAZIONE_JSON = result["stato_conversazione_json"]
    stato_attuale = result["stato_conversazione"]
    # Determina se è stato attivato un nuovo template (cioè se il template attuale non era presente nello stato precedente)
    response = {
        "guide_phrase": result["guide_phrase"],
        "template_usato": result["template_usato"],
        "stato_conversazione": stato_attuale
    }
    # Se c'è next_template (salto step), passalo e forza nuovo_template a True
    if "next_template" in result:
        response["next_template"] = result["next_template"]
        response["nuovo_template"] = True
    else:
        nuovo_template = False
        if result["template_usato"] not in stato_precedente and result["template_usato"] in stato_attuale:
            nuovo_template = True
        response["nuovo_template"] = nuovo_template

    if result["template_usato"] == "luoghi":
        response["luogo_completato"] = result["luogo_completato"]
    return response

@app.post("/set_template")
def set_template(request: TemplateChangeRequest):
    global TEMPLATE_ATTIVO
    global STATO_CONVERSAZIONE_JSON
    if request.template_type not in TEMPLATES:
        raise HTTPException(status_code=400, detail="Template non valido")
    TEMPLATE_ATTIVO = request.template_type
    # Se si passa a un template diverso da 'luoghi', cancella luogo_in_corso
    stato = json.loads(STATO_CONVERSAZIONE_JSON)
    if TEMPLATE_ATTIVO != 'luoghi' and 'luogo_in_corso' in stato:
        del stato['luogo_in_corso']
        STATO_CONVERSAZIONE_JSON = json.dumps(stato, ensure_ascii=False, indent=2)
    return {"template_attivo": TEMPLATE_ATTIVO}

@app.get("/debug_stato")
def debug_stato():
    global STATO_CONVERSAZIONE_JSON
    return {"stato_conversazione": json.loads(STATO_CONVERSAZIONE_JSON)}


