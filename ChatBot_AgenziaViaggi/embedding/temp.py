import psycopg2
from nomic import embed
import numpy as np
from pathlib import Path  

try:
    # Connessione al database
    conn = psycopg2.connect(
        dbname="routeToWonderland",
        user="postgres",       # <-- cambia con il tuo utente
        password="admin",   # <-- cambia con la tua password
        host="localhost",           # o altro host
        port=5432
    )
    cursor = conn.cursor()

    # Assicurati che i campi VECTOR esistano
    cursor.execute("ALTER TABLE alloggi ADD COLUMN IF NOT EXISTS tipo VARCHAR(50) CHECK (tipo IN ('hotel', 'campeggio', 'villaggio turistico', 'resort'));")
    cursor.execute("UPDATE alloggi SET tipo = (CASE floor(random() * 4)::int WHEN 0 THEN 'hotel' WHEN 1 THEN 'campeggio' WHEN 2 THEN 'villaggio turistico' WHEN 3 THEN 'resort' END);")
    # Commit e chiusura
    conn.commit()
    print("✅ Embedding generati e salvati con successo.")

except Exception as e:
    print(f"❌ Errore durante l'elaborazione: {str(e)}")
    if 'conn' in locals():
        conn.rollback()

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
