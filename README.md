
[![Test Coverage](https://img.shields.io/badge/coverage-76.27%25-brightgreen)](coverage.txt)
[![Python Version](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success)]()
[![Last Commit](https://img.shields.io/github/last-commit/AlexBenin01/RouteToWonderland)]()
[![Open Issues](https://img.shields.io/github/issues/AlexBenin01/RouteToWonderland)]()
[![Stars](https://img.shields.io/github/stars/AlexBenin01/RouteToWonderland?style=social)]()

# RouteToWonderland

RouteToWonderland è una piattaforma intelligente per la creazione di viaggi personalizzati, pensata per agenzie di viaggio e utenti finali. Il sistema sfrutta l'intelligenza artificiale per estrarre automaticamente le informazioni chiave da richieste testuali e guidare l'utente nella pianificazione di un viaggio su misura.

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
  - React  
  - Vite  
  - ESLint  
- **Backend**:  
  - Python  
  - FastAPI  
  - Pydantic  
  - Modello AI custom (locale, non incluso nel repository)

---

## Requisiti e installazione

### Prerequisiti

- Python 3.10
- Node.js 16+
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
pip install "torch>=2.1" "nncf>=2.7" "transformers>=4.40.0" "onnx<1.16.2" "optimum>=1.16.1" "accelerate" "datasets>=2.14.6" "git+https://github.com/huggingface/optimum-intel.git" --extra-index-url https://download.pytorch.org/whl/cpu
pip install fastapi uvicorn
```

### Installazione dipendenze per embedding

```bash
pip install nomic psycopg2-binary pgvector
```

### Note modello AI

Assicurati che la cartella `NuExtract-2-xB-experimental` contenga il modello AI (non incluso nel repository).

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

- Le cartelle `NuExtract-2-xB-experimental` e `nomic-embed-text-v1.5` sono escluse dal repository (`.gitignore`) perché contiene file di grandi dimensioni e modelli proprietari.
- Per il corretto funzionamento, assicurati di avere i file del modello nella posizione corretta.

---

## Licenza

Questo progetto è distribuito sotto licenza Apache 2.0. Vedi il file `LICENSE` per i dettagli.

---


