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
    cursor.execute("ALTER TABLE destinazione_generica ADD COLUMN IF NOT EXISTS embedding_stato VECTOR(768);")
    cursor.execute("ALTER TABLE destinazioni_regionali ADD COLUMN IF NOT EXISTS embedding_regione VECTOR(768);")
    cursor.execute("ALTER TABLE destinazioni_locali ADD COLUMN IF NOT EXISTS embedding_luogo VECTOR(768);")
    conn.commit()

    # 1. Recupera valori unici
    cursor.execute("SELECT DISTINCT stato FROM destinazione_generica WHERE stato IS NOT NULL;")
    stati = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT regione FROM destinazioni_regionali WHERE regione IS NOT NULL;")
    regioni = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT luogo FROM destinazioni_locali WHERE luogo IS NOT NULL;")
    luoghi = [row[0] for row in cursor.fetchall()]

    # 2. Embedding con Nomic
    def genera_embedding(lista_valori):
        if not lista_valori:
            return []
        try:
            print("Generazione embedding con modello nomic-embed-text-v1.5...")
            result = embed.text(
                lista_valori, 
                model='nomic-embed-text-v1.5',  # Usiamo il nome del modello predefinito
                task_type='search_query'
            )
            return result['embeddings']
        except Exception as e:
            print(f"Errore durante la generazione degli embedding: {str(e)}")
            return []

    print("Generazione embedding per stati...")
    emb_stati = genera_embedding(stati)
    
    print("Generazione embedding per regioni...")
    emb_regioni = genera_embedding(regioni)
    
    print("Generazione embedding per luoghi...")
    emb_luoghi = genera_embedding(luoghi)

    # 3. Salva nel DB
    print("Salvataggio embedding nel database...")
    
    for stato, emb in zip(stati, emb_stati):
        cursor.execute("""
            UPDATE destinazione_generica
            SET embedding_stato = %s
            WHERE stato = %s
        """, (emb, stato))

    for regione, emb in zip(regioni, emb_regioni):
        cursor.execute("""
            UPDATE destinazioni_regionali
            SET embedding_regione = %s
            WHERE regione = %s
        """, (emb, regione))

    for luogo, emb in zip(luoghi, emb_luoghi):
        cursor.execute("""
            UPDATE destinazioni_locali
            SET embedding_luogo = %s
            WHERE luogo = %s
        """, (emb, luogo))

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
