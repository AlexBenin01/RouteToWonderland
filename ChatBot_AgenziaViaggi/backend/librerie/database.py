"""
Modulo per la gestione delle connessioni al database
"""

import psycopg2
import logging
from psycopg2 import pool
from typing import Optional

logger = logging.getLogger(__name__)

# Configurazione del connection pool
connection_pool = None

def init_connection_pool():
    """
    Inizializza il connection pool per il database.
    """
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname="routeToWonderland",
            user="postgres",
            password="admin",
            host="localhost",
            port=5432
        )
        logger.info("Connection pool inizializzato con successo")
    except Exception as e:
        logger.error(f"Errore nell'inizializzazione del connection pool: {str(e)}")
        raise

def get_db_connection():
    """
    Ottiene una connessione dal pool.
    
    Returns:
        psycopg2.extensions.connection: Connessione al database
    """
    global connection_pool
    
    if connection_pool is None:
        init_connection_pool()
    
    try:
        return connection_pool.getconn()
    except Exception as e:
        logger.error(f"Errore nell'ottenere una connessione dal pool: {str(e)}")
        raise

def release_connection(conn):
    """
    Rilascia una connessione nel pool.
    
    Args:
        conn: Connessione da rilasciare
    """
    global connection_pool
    if connection_pool is not None:
        connection_pool.putconn(conn)

def close_all_connections():
    """
    Chiude tutte le connessioni nel pool.
    """
    global connection_pool
    if connection_pool is not None:
        connection_pool.closeall()
        logger.info("Tutte le connessioni sono state chiuse") 