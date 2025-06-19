[![Test Coverage](https://img.shields.io/badge/coverage-76.27%25-brightgreen)](coverage.txt)
[![Python Version](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success)]()
[![Last Commit](https://img.shields.io/github/last-commit/AlexBenin01/RouteToWonderland)]()
[![Open Issues](https://img.shields.io/github/issues/AlexBenin01/RouteToWonderland)]()
[![Stars](https://img.shields.io/github/stars/AlexBenin01/RouteToWonderland?style=social)]()

# RouteToWonderland

RouteToWonderland è una piattaforma all'avanguardia che trasforma la pianificazione dei viaggi attraverso l'intelligenza artificiale. Combinando il modello NuExtract 2.0 di estrazione dati con un sistema di conversazione naturale basato su Qwen3, la piattaforma offre un'esperienza di pianificazione viaggi completamente automatizzata e personalizzata.

Progettata sia per agenzie di viaggio che per viaggiatori individuali, RouteToWonderland analizza automaticamente le richieste, estrae informazioni chiave e guida l'utente attraverso un processo di pianificazione intuitivo. La piattaforma si distingue per la sua capacità di comprendere il contesto, adattarsi alle preferenze specifiche e generare suggerimenti pertinenti, tutto questo attraverso un'interfaccia moderna e reattiva.

## Caratteristiche distintive

- 🤖 **Intelligenza Artificiale Avanzata**: 
  - Doppio sistema AI che combina estrazione intelligente di informazioni e generazione di risposte naturali
  - Modello NuExtract per l'analisi precisa delle richieste
  - Integrazione con Qwen3 per conversazioni fluide e contestuali

- 🎯 **Personalizzazione senza precedenti**:
  - Analisi automatica delle preferenze e dei requisiti
  - Suggerimenti intelligenti basati sul contesto
  - Adattamento dinamico alle esigenze specifiche

- 💡 **Interfaccia moderna e intuitiva**:
  - Design reattivo ottimizzato per tutti i dispositivi
  - Esperienza utente fluida e coinvolgente
  - Navigazione semplice e guidata

- 🔒 **Sicurezza e affidabilità**:
  - Elaborazione locale dei dati sensibili
  - Architettura robusta e scalabile
  - Performance ottimizzate

---

## Struttura del progetto

- **ChatBot_AgenziaViaggi/frontend**  
  Interfaccia utente sviluppata in React con Vite, moderna e reattiva.
- **ChatBot_AgenziaViaggi/backend**  
  Backend in Python con FastAPI, integra modelli AI per l'estrazione delle informazioni e la gestione della conversazione.
- **ChatBot_AgenziaViaggi/backend/NuExtract-2-xB-experimental**  
  Modello AI locale (non incluso nel repository) per l'estrazione delle entità e la comprensione del linguaggio naturale.

---

## Funzionalità principali

- **Estrazione automatica delle informazioni**:  
  Il backend utilizza modelli AI per estrarre dati strutturati da richieste testuali (destinazione, date, partecipanti, preferenze, ecc.).
- **Conversazione guidata**:  
  Il sistema guida l'utente passo-passo nella definizione del viaggio, suggerendo domande e raccogliendo tutte le informazioni necessarie.
- **Personalizzazione avanzata**:  
  Possibilità di specificare preferenze su alloggi, attività, noleggi, guide turistiche e altro.
- **Frontend intuitivo**:  
  Interfaccia moderna e reattiva, facile da usare anche su dispositivi mobili.

---

## Tecnologie utilizzate

- **Frontend**:
  - Node.js 
  - React  
  - Vite  
  - ESLint  
- **Backend**:  
  - Python  
  - FastAPI  
  - Pydantic  
  - Modello AI custom (locale, non incluso nel repository)
  - Ollama con modello Qwen3 ("qwen3:1.7b") per la generazione di risposte in linguaggio naturale

### Database e Embedding

- **Database PostgreSQL**:
  - Database relazionale per la gestione dei dati strutturati
  - File `routeToWonderland.sql` contiene la struttura completa del database e dati di esempio
  - Estensione pgvector per supportare operazioni con vettori

- **Sistema di Embedding**:
  - Utilizza il modello nomic-embed-text-v1.5 per generare embedding semantici
  - Converte testo in vettori 768-dimensionali per ricerca semantica
  - Applicato a vari campi come destinazioni, attività, alloggi, ecc.
  - Permette ricerche semantiche avanzate nel database
  - Gli embedding vengono generati e salvati automaticamente nel database

---

## Requisiti e installazione

### Prerequisiti
- Node.js
- Python 3.10
- JDK 17 (per Droll_Service)
- Maven (per Droll_Service)

### (Opzionale) Ambiente virtuale Python

Se vuoi isolare le dipendenze Python, puoi creare un ambiente virtuale:

```bash
# Step 1: Crea ambiente virtuale
py -3.10 -m venv venv
# Step 2: Attiva ambiente virtuale
venv\Scripts\activate
# Step 3: Aggiorna pip
py -m pip install --upgrade pip
```

### Creazione e setup del frontend React

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios
npm install react-router-dom
```

### Installazione dipendenze Python (backend)

Posizionati nella cartella backend:

```bash
pip install dotenv
pip install einops
pip install timm
pip install sentence_transformers
pip install tiktoken
pip install torchvision
pip install sentencepiece
pip install langdetect
pip install qwen_vl_utils
pip install "torch>=2.1" "nncf>=2.7" "transformers>=4.40.0" "onnx<1.16.2" "optimum>=1.16.1" "accelerate" "datasets>=2.14.6" "git+https://github.com/huggingface/optimum-intel.git" --extra-index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn
```

### Installazione dipendenze per embedding

```bash
pip install nomic psycopg2-binary pgvector
```

### Note modello AI

Il sistema utilizza due modelli AI principali:

1. **NuExtract-2.0-xB**:
   - Modello locale per l'estrazione delle entità e la comprensione del linguaggio naturale
   - Non incluso nel repository per motivi di dimensione e proprietà intellettuale
   - Deve essere posizionato nella cartella `backend/NuExtract-2.0-xB`

2. **Ollama con Qwen3**:
   - Utilizza il modello "qwen3:1.7b" tramite Ollama per la generazione di risposte in linguaggio naturale
   - Richiede l'installazione di Ollama sul sistema
   - Genera risposte in italiano per la conversazione con l'utente
   - Configurato per operare su `localhost:11434`

Per il corretto funzionamento, assicurati di:
- Avere i file del modello NuExtract nella posizione corretta
- Aver installato e avviato Ollama sul sistema
- Aver scaricato il modello Qwen3 tramite Ollama (`ollama pull qwen3:1.7b`)

---

## Avvio completo

### Backend

```bash
cd backend
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

### Droll_Service

Assicurati di avere JDK 17 installato e Maven configurato con le variabili d'ambiente corrette. Poi esegui:

```bash
mvn spring-boot:run
```

Ora puoi accedere all'applicazione su [http://localhost:5173](http://localhost:5173) e inviare testo al modello per vedere i dati estratti.

---

## Note importanti

- Le cartelle `NuExtract-2.0-xB` e `nomic-embed-text-v1.5` sono escluse dal repository (`.gitignore`) perché contiene file di grandi dimensioni e modelli proprietari.
- Per il corretto funzionamento, assicurati di avere i file del modello nella posizione corretta.

---

## Licenza

Questo progetto è distribuito sotto licenza Apache 2.0. Vedi il file `LICENSE` per i dettagli.

---


