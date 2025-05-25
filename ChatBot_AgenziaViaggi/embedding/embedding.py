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
    cursor.execute("ALTER TABLE tag ADD COLUMN IF NOT EXISTS embedding_tag VECTOR(768);")
    cursor.execute("ALTER TABLE alloggi ADD COLUMN IF NOT EXISTS embedding_alloggi VECTOR(768);")
    cursor.execute("ALTER TABLE attivita_avventura ADD COLUMN IF NOT EXISTS embedding_attivita VECTOR(768);")
    cursor.execute("ALTER TABLE difficolta ADD COLUMN IF NOT EXISTS embedding_difficolta VECTOR(768);")
    cursor.execute("ALTER TABLE degustazione ADD COLUMN IF NOT EXISTS embedding_degustazione VECTOR(768);")
    cursor.execute("ALTER TABLE trattamenti ADD COLUMN IF NOT EXISTS embedding_trattamento VECTOR(768);")
    cursor.execute("ALTER TABLE attivita_citta ADD COLUMN IF NOT EXISTS embedding_attivita VECTOR(768);")
    cursor.execute("ALTER TABLE attivita_mare ADD COLUMN IF NOT EXISTS embedding_attivita VECTOR(768);")
    cursor.execute("ALTER TABLE attivita_montagna ADD COLUMN IF NOT EXISTS embedding_attivita VECTOR(768);")
    cursor.execute("ALTER TABLE attivita_naturalistiche ADD COLUMN IF NOT EXISTS embedding_attivita VECTOR(768);")
    cursor.execute("ALTER TABLE tipo_trasporto ADD COLUMN IF NOT EXISTS embedding_veicolo VECTOR(768);")
    cursor.execute("ALTER TABLE tipo_alloggi ADD COLUMN IF NOT EXISTS embedding_tipo_alloggi VECTOR(768);")
    cursor.execute("ALTER TABLE tipo_cambio ADD COLUMN IF NOT EXISTS embedding_tipo_cambio VECTOR(768);")
    cursor.execute("ALTER TABLE linguaggio ADD COLUMN IF NOT EXISTS embedding_lingua VECTOR(768);")
    conn.commit()

    # 1. Recupera valori unici
    cursor.execute("SELECT DISTINCT stato FROM destinazione_generica WHERE stato IS NOT NULL;")
    stati = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT regione FROM destinazioni_regionali WHERE regione IS NOT NULL;")
    regioni = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT luogo FROM destinazioni_locali WHERE luogo IS NOT NULL;")
    luoghi = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT nome_tag FROM tag WHERE nome_tag IS NOT NULL;")
    tags = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT nome FROM alloggi WHERE nome IS NOT NULL;")
    alloggi = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT attivita FROM attivita_avventura WHERE attivita IS NOT NULL;")
    attivita_avventura = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT difficolta FROM difficolta WHERE difficolta IS NOT NULL;")
    difficolta = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT trattamento FROM trattamenti WHERE trattamento IS NOT NULL;")
    trattamenti = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT attivita FROM attivita_citta WHERE attivita IS NOT NULL;")
    attivita_citta = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT attivita FROM attivita_mare WHERE attivita IS NOT NULL;")
    attivita_mare = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT attivita FROM attivita_montagna WHERE attivita IS NOT NULL;")
    attivita_montagna = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT attivita FROM attivita_naturalistiche WHERE attivita IS NOT NULL;")
    attivita_naturalistiche = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT degustazione FROM degustazione WHERE degustazione IS NOT NULL;")
    degustazioni = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT veicolo FROM tipo_trasporto WHERE veicolo IS NOT NULL;")
    veicoli = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT alloggi FROM tipo_alloggi WHERE alloggi IS NOT NULL;")
    alloggi = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT cambio FROM tipo_cambio WHERE cambio IS NOT NULL;")
    cambio = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT lingua FROM linguaggio WHERE lingua IS NOT NULL;")
    lingue = [row[0] for row in cursor.fetchall()]

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

    print("Generazione embedding per tag...")
    emb_tags = genera_embedding(tags)

    print("Generazione embedding per alloggi...")
    emb_alloggi = genera_embedding(alloggi)

    print("Generazione embedding per attività avventura...")
    emb_attivita_avventura = genera_embedding(attivita_avventura)

    print("Generazione embedding per difficoltà...")
    emb_difficolta = genera_embedding(difficolta)

    print("Generazione embedding per trattamenti...")
    emb_trattamenti = genera_embedding(trattamenti)

    print("Generazione embedding per attività città...")
    emb_attivita_citta = genera_embedding(attivita_citta)

    print("Generazione embedding per attività mare...")
    emb_attivita_mare = genera_embedding(attivita_mare)

    print("Generazione embedding per attività montagna...")
    emb_attivita_montagna = genera_embedding(attivita_montagna)

    print("Generazione embedding per attività naturalistiche...")
    emb_attivita_naturalistiche = genera_embedding(attivita_naturalistiche)

    print("Generazione embedding per degustazioni...")
    emb_degustazioni = genera_embedding(degustazioni)

    print("Generazione embedding per tipo_trasporto...")
    emb_tipo_trasporto = genera_embedding(veicoli)
    print("Generazione embedding per tipo_alloggi...")
    emb_tipo_alloggi = genera_embedding(alloggi)

    print("Generazione embedding per tipo_cambio...")
    emb_tipo_cambio = genera_embedding(cambio)

    print("Generazione embedding per lingue...")
    emb_lingue = genera_embedding(lingue)





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

    for nome_tag, emb in zip(tags, emb_tags):
        cursor.execute("""
            UPDATE tag
            SET embedding_tag = %s
            WHERE nome_tag = %s
        """, (emb, nome_tag))

    for nome, emb in zip(alloggi, emb_alloggi):
        cursor.execute("""
            UPDATE alloggi
            SET embedding_alloggi = %s
            WHERE nome = %s
        """, (emb, nome))

    for attivita, emb in zip(attivita_avventura, emb_attivita_avventura):
        cursor.execute("""
            UPDATE attivita_avventura
            SET embedding_attivita = %s
            WHERE attivita = %s
        """, (emb, attivita))

    for difficolta, emb in zip(difficolta, emb_difficolta):
        cursor.execute("""
            UPDATE difficolta
            SET embedding_difficolta = %s
            WHERE difficolta = %s
        """, (emb, difficolta))

    for trattamento, emb in zip(trattamenti, emb_trattamenti):
        cursor.execute("""
            UPDATE trattamenti
            SET embedding_trattamento = %s
            WHERE trattamento = %s
        """, (emb, trattamento))

    for degustazione, emb in zip(degustazioni, emb_degustazioni):
        cursor.execute("""
            UPDATE degustazione
            SET embedding_degustazione = %s
            WHERE degustazione = %s
        """, (emb, degustazione))
    
    for attivita, emb in zip(attivita_citta, emb_attivita_citta):
        cursor.execute("""
            UPDATE attivita_citta
            SET embedding_attivita = %s
            WHERE attivita = %s
        """, (emb, attivita))
    
    for attivita, emb in zip(attivita_mare, emb_attivita_mare):
        cursor.execute("""
            UPDATE attivita_mare
            SET embedding_attivita = %s
            WHERE attivita = %s
        """, (emb, attivita))
    
    for attivita, emb in zip(attivita_montagna, emb_attivita_montagna):
        cursor.execute("""
            UPDATE attivita_montagna
            SET embedding_attivita = %s
            WHERE attivita = %s
        """, (emb, attivita))
    
    for attivita, emb in zip(attivita_naturalistiche, emb_attivita_naturalistiche):
        cursor.execute("""
            UPDATE attivita_naturalistiche
            SET embedding_attivita = %s
            WHERE attivita = %s
        """, (emb, attivita))
    
    for veicolo, emb in zip(veicoli, emb_tipo_trasporto):
        cursor.execute("""
            UPDATE tipo_trasporto
            SET embedding_veicolo = %s
            WHERE veicolo = %s
        """, (emb, veicolo)),
    for veicolo, emb in zip(alloggi, emb_tipo_trasporto):
        cursor.execute("""
            UPDATE tipo_alloggi
            SET embedding_tipo_alloggi = %s
            WHERE alloggi = %s
        """, (emb, veicolo))
    
    for cambio, emb in zip(cambio, emb_tipo_cambio):
        cursor.execute("""
            UPDATE tipo_cambio
            SET embedding_tipo_cambio = %s
            WHERE cambio = %s
        """, (emb, cambio))

    for lingua, emb in zip(lingue, emb_lingue):
        cursor.execute("""
            UPDATE linguaggio
            SET embedding_lingua = %s
            WHERE lingua = %s
        """, (emb, lingua))
    

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
