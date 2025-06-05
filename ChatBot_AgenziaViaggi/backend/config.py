import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazione del servizio Drools
DROOLS_SERVICE_URL = os.getenv("DROOLS_SERVICE_URL", "http://localhost:8080") 