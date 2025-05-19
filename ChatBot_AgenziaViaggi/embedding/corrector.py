            # 📌 Import Librerie di Machine Learning  
import torch  
from sentence_transformers import SentenceTransformer  

# 📌 Import Librerie Standard  
import os  
from pathlib import Path  
import psycopg2
import numpy as np

# 📌 Import FastAPI e Gestione delle Eccezioni
from fastapi import HTTPException

VECTOR_SEARCH = '''
                SELECT luogo, embedding_luogo <=> %s::vector as distanza
                FROM destinazioni_locali
                WHERE embedding_luogo IS NOT NULL
                ORDER BY distanza ASC
                LIMIT 1
'''

def text_to_embeddings(model_path: str = None, text: str ="", query: bool=False ):
    """
    Classe per generare embeddings da testo utilizzando SentenceTransformer.
    :param model_path: Percorso del modello personalizzato. Se None, utilizza il modello predefinito.
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    # Correggo il percorso per puntare alla directory principale del progetto
    default_path = Path(__file__).resolve().parent.parent / 'nomic-embed-text-v1.5'
    model_path = model_path or str(default_path)
    
    print(f"🔍 Caricamento modello da: {model_path}")
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Il modello non è stato trovato in: {model_path}")
    
    model = SentenceTransformer(model_path, trust_remote_code=True)
    model = model.to(device)
    """
    Converte un testo in embeddings.
    
    :param text: Il testo da convertire in embedding.
    :return: Lista di valori numerici che rappresentano l'embedding del testo.
    """
    if not text:
        raise HTTPException(status_code=500, detail="Unknown error key, "+ text)
    if query:
        sentence = f'search_query: {text}'
        embeddings = model.encode(sentence, device=device)  
        return embeddings.tolist()
    else:
        sentences = f'search_document: {text}'
        embeddings = model.encode(sentences, device=device)  
        return embeddings.tolist()

def cerca_simile(embedding):
    """
    Cerca la regione più simile nel database usando l'embedding fornito
    """
    try:
        conn = psycopg2.connect(
            dbname="routeToWonderland",
            user="postgres",
            password="admin",
            host="localhost",
            port=5432
        )
        cursor = conn.cursor()
        
        # Converti l'embedding in una stringa nel formato corretto per PostgreSQL
        embedding_str = '[' + ','.join(map(str, embedding)) + ']'
        
        cursor.execute(VECTOR_SEARCH, (embedding_str,))
        risultato = cursor.fetchall()
        print(risultato)
        
        if risultato:
            luogo, distanza = risultato
            return luogo, distanza
        return None, None
        
    except Exception as e:
        print(f"❌ Errore durante la ricerca nel database: {str(e)}")
        return None, None
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Test della funzione con diversi input
    test_cases = [
        ("Venekmia", True),    # Test con query
        ("Romeeaaa", True),     # Test con documento
        ("Miao", True),    # Test con query
        ("Napoliiii", True),   # Test con documento
    ]
    
    print("🔍 Test della funzione text_to_embeddings")
    print("=" * 50)
    
    for index, (text, is_query) in enumerate(test_cases):
        try:
            print(f"\n📝 Test con testo: '{text}' (query={is_query})")
            embeddings = text_to_embeddings(text=text, query=is_query)
            print(f"✅ Embedding generato con successo")
            print(f"📊 Dimensione embedding: {len(embeddings)}")
            print(f"📈 5 valori: {embeddings[index]}")
            
            # Cerca la regione più simile
            luogo, distanza = cerca_simile(embeddings)
            if luogo:
                print(f"🎯 Luogo trovato: {luogo}")
                print(f"📏 Distanza: {distanza}")
            else:
                print("❌ Nessun luogo simile trovato")
                
        except Exception as e:
            print(f"❌ Errore durante il test: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Test completati")


    

