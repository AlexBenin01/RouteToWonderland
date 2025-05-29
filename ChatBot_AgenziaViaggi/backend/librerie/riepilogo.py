"""
Libreria per la gestione del riepilogo dei template
"""

import json
import logging
import requests
from typing import Dict, Any, Tuple
from database import get_db_connection, release_connection

logger = logging.getLogger(__name__)

def algoritmoABC(totale_speso: float, fatturato_annuale: float) -> str:
    """
    Interroga il servizio Drools per determinare il grado di sconto del cliente
    basato sul totale speso e il fatturato annuale.
    
    Args:
        totale_speso: Il totale speso dal cliente
        fatturato_annuale: Il fatturato annuale dell'azienda
        
    Returns:
        str: La lettera (A, B o C) che indica il grado di sconto
    """
    try:
        # Preparo i dati per la chiamata a Drools
        payload = {
            "totale_speso": totale_speso,
            "fatturato_annuale": fatturato_annuale
        }
        
        # Chiamata al servizio Drools
        response = requests.post(
            "http://localhost:8080/drools-service/api/calcola-sconto",
            json=payload
        )
        
        if response.status_code == 200:
            risultato = response.json()
            grado_sconto = risultato.get("grado_sconto", "C")  # Default a C se non specificato
            logger.info(f"Grado sconto calcolato: {grado_sconto}")
            return grado_sconto
        else:
            logger.error(f"Errore nella chiamata a Drools: {response.status_code}")
            return "C"  # Default a C in caso di errore
            
    except Exception as e:
        logger.error(f"Errore nell'algoritmo ABC: {str(e)}")
        return "C"  # Default a C in caso di errore
























def process_riepilogo(stato_conversazione_json: str) -> Dict[str, Any]:
    """
    Processa lo stato della conversazione per generare il riepilogo
    
    Args:
        stato_conversazione_json: Stringa JSON contenente lo stato della conversazione
        
    Returns:
        Dict[str, Any]: Dizionario contenente il riepilogo elaborato
    """
    try:
        # Converti la stringa JSON in dizionario
        stato_conversazione = json.loads(stato_conversazione_json)
        logger.info("Stato conversazione caricato correttamente")
        
        # Dizionario per mappare i nomi dei template alle loro funzioni di processamento
        template_processors = {
            'trasporto': process_trasporto,
            'alloggi': process_alloggi,
            'noleggi': process_noleggi,
            'naturalistico': process_naturalistico,
            'avventura': process_avventura,
            'montagna': process_montagna,
            'mare': process_mare,
            'gastronomia': process_gastronomia,
            'citta_arte': process_citta_arte
        }
        
        # Dizionario per memorizzare i risultati elaborati
        riepilogo_elaborato = {}
        
        # Variabili globali
        budget_originale = None
        budget_viaggio = None
        costo_totale = 0
        grado_sconto = "C"
        
        # Elabora prima i template intro e contatti
        try:
            # Elabora il template intro
            if 'intro' in stato_conversazione:
                logger.info("Elaborazione del template intro")
                riepilogo_elaborato['intro'] = stato_conversazione['intro']
                riepilogo_elaborato['intro']['regione_citta_destinazione'] = process_intro(
                    stato_conversazione['intro']
                )
                logger.info("Template intro elaborato con successo")
                # Estrai il budget dal template intro
                budget_originale = stato_conversazione['intro'].get('budget_viaggio')
                budget_viaggio = budget_originale
                luogo = riepilogo_elaborato['intro'].get('regione_citta_destinazione')
                logger.info(f"Budget originale estratto: {budget_originale}")
                logger.info(f"Luogo estratto: {luogo}")
            else:
                logger.warning("Template intro non presente nello stato della conversazione")
                intro_data = {}
            
            bambini = 0
            if 'famiglia' in stato_conversazione:
                bambini = stato_conversazione['famiglia'].get('bambini', 0)
            
            # Elabora il template contatti
            if 'contatti' in stato_conversazione:
                logger.info("Elaborazione del template contatti")
                riepilogo_elaborato['contatti'] = stato_conversazione['contatti']
                grado_sconto = process_contatti(stato_conversazione['contatti'])
                
                # Applica lo sconto al budget in base al grado
                if budget_viaggio is not None:
                    if grado_sconto == "A":
                        budget_viaggio = budget_viaggio * 1.30  # +30% per grado A
                    elif grado_sconto == "B":
                        budget_viaggio = budget_viaggio * 1.15  # +15% per grado B
                    
                    # Aggiorna il budget nel riepilogo
                    riepilogo_elaborato['intro']['budget_viaggio'] = budget_viaggio
                    logger.info(f"Budget aggiornato con sconto grado {grado_sconto}: {budget_viaggio}")
                
                logger.info("Template contatti elaborato con successo")
            else:
                logger.warning("Template contatti non presente nello stato della conversazione")
                contatti_data = {}
            
            # Elabora il template alloggi
            if 'alloggi' in stato_conversazione:
                logger.info("Elaborazione del template alloggi")
                risultato = process_alloggi(
                    stato_conversazione['alloggi'],
                    stato_conversazione.get('benessere', {}),
                    luogo,
                    riepilogo_elaborato.get('intro', {}).get('numero_partecipanti', 1),
                    riepilogo_elaborato.get('intro', {}).get('trip_duration', 1),
                    bambini,
                    [budget_viaggio] if budget_viaggio else [0]
                )
                riepilogo_elaborato['alloggi'] = risultato
                if risultato and 'costo_totale' in risultato:
                    costo_totale += risultato['costo_totale']
                logger.info("Template alloggi elaborato con successo")
            
            # Elabora il template noleggi
            if 'noleggi' in stato_conversazione:
                logger.info("Elaborazione del template noleggi")
                risultato = process_noleggi(
                    stato_conversazione['noleggi'],
                    riepilogo_elaborato.get('intro', {}).get('trip_duration', 1),
                    [budget_viaggio] if budget_viaggio else [0]
                )
                riepilogo_elaborato['noleggi'] = risultato
                if risultato and 'costo_totale' in risultato:
                    costo_totale += risultato['costo_totale']
                logger.info("Template noleggi elaborato con successo")
                
        except Exception as e:
            logger.error(f"Errore nell'elaborazione dei template intro/contatti/benessere/alloggi: {str(e)}")
            raise
        
        # Processa gli altri template presenti nello stato della conversazione
        for template_name, template_data in stato_conversazione.items():
            if template_name in template_processors and template_name not in ['intro', 'contatti', 'benessere', 'alloggi', 'noleggi']:
                logger.info(f"Elaborazione del template: {template_name}")
                try:
                    risultato = template_processors[template_name](
                        template_data,
                        luogo,
                        riepilogo_elaborato.get('intro', {}).get('numero_partecipanti', 1),
                        [budget_viaggio] if budget_viaggio else [0]
                    )
                    riepilogo_elaborato[template_name] = risultato
                    if risultato and 'costo_totale' in risultato:
                        costo_totale += risultato['costo_totale']
                    logger.info(f"Template {template_name} elaborato con successo")
                except Exception as e:
                    logger.error(f"Errore nell'elaborazione del template {template_name}: {str(e)}")
                    riepilogo_elaborato[template_name] = {"error": str(e)}
            elif template_name not in ['intro', 'contatti', 'benessere', 'alloggi', 'noleggi']:
                # Se il template non ha una funzione di processamento associata, lo segnala
                logger.warning(f"Template {template_name} non ha una funzione di processamento associata")
        
        # Aggiungi il riepilogo dei costi e dello sconto
        riepilogo_elaborato['riepilogo_costi'] = {
            'costo_totale': costo_totale,
            'costo_totale_con_sconto': costo_totale * (0.7 if grado_sconto == "A" else 0.85 if grado_sconto == "B" else 1),
            'budget_iniziale': budget_originale,
            'budget_rimanente': budget_viaggio - costo_totale if budget_viaggio else 0,
            'grado_sconto': grado_sconto,
            'percentuale_sconto': {
                'A': '30%',
                'B': '15%',
                'C': '0%'
            }.get(grado_sconto, '0%')
        }
        
        return riepilogo_elaborato
        
    except json.JSONDecodeError as e:
        logger.error(f"Errore nel parsing dello stato conversazione: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Errore nel processamento del riepilogo: {str(e)}")
        raise
















































def process_intro(template_data: Dict[str, Any]) -> str:
    """
    Processa il template intro e restituisce la città di destinazione.
    Se il campo regione_citta_destinazione è una regione, cerca la città con più mood_vacanza
    in quella regione e la restituisce.
    
    Args:
        template_data: Dizionario contenente i dati del template intro
    Returns:
        str: La città di destinazione (originale o trovata nella regione)
    """
    try:
        # Verifica se il campo regione_citta_destinazione è presente
        regione_citta = template_data.get("regione_citta_destinazione")
        if not regione_citta:
            logger.warning("Campo regione_citta_destinazione non presente nel template")
            return ""
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Verifica se è una regione
            cursor.execute("SELECT regione FROM destinazioni_regionali WHERE regione = %s", (regione_citta,))
            is_regione = cursor.fetchone() is not None
            
            if is_regione:
                logger.info(f"'{regione_citta}' è una regione, cerco la città con più mood_vacanza")
                # Trova la città con più mood_vacanza nella regione
                query = """
                    SELECT dl.luogo, COUNT(dlt.tag_id) as num_tags
                    FROM destinazioni_locali dl
                    LEFT JOIN destinazioni_locali_tag dlt ON dl.luogo = dlt.luogo
                    WHERE dl.regione = %s
                    GROUP BY dl.luogo
                    ORDER BY num_tags DESC
                    LIMIT 1
                """
                cursor.execute(query, (regione_citta,))
                result = cursor.fetchone()
                
                if result:
                    citta, num_tags = result
                    logger.info(f"Trovata città '{citta}' con {num_tags} mood_vacanza")
                    return citta
                else:
                    logger.warning(f"Nessuna città trovata nella regione '{regione_citta}'")
                    return regione_citta
            else:
                logger.info(f"'{regione_citta}' non è una regione, mantengo il valore originale")
                return regione_citta
        
        finally:
            cursor.close()
            release_connection(conn)
        
    except Exception as e:
        logger.error(f"Errore nell'elaborazione del template intro: {str(e)}")
        # In caso di errore, restituisci il valore originale
        return regione_citta if regione_citta else ""

def process_contatti(template_data: Dict[str, Any]) -> str:
    """
    Processa il template contatti verificando l'esistenza del profilo nel database
    usando il codice fiscale o partita IVA e restituendo il totale speso se esiste.
    Se il profilo non esiste, lo crea con tutti i campi necessari e budget inizializzato a 0.
    Inoltre, recupera il fatturato dell'anno corrente e calcola il grado di sconto.
    
    Args:
        template_data: Dizionario contenente i dati del template contatti
        
    Returns:
        str: La lettera (A, B o C) che indica il grado di sconto
    """
    try:
        identificativo = template_data.get('codice_fiscale_o_partita_iva')
        full_name = template_data.get('full_name')
        cellulare = template_data.get('numero_cellulare')
        email = template_data.get('email')
        
        if not identificativo:
            logger.warning("Codice fiscale o partita IVA non presente nei dati contatti")
            return "C"
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Verifica se esiste il profilo usando il codice fiscale o partita IVA
            cursor.execute("SELECT budget_tot_speso FROM clieti WHERE identificativo = %s", (identificativo,))
            risultato = cursor.fetchone()
            
            # Query per ottenere il fatturato dell'anno corrente
            cursor.execute("""
                SELECT COALESCE(SUM(importo), 0) 
                FROM azienda 
                WHERE identificativo = %s 
                AND EXTRACT(YEAR FROM data_fattura) = EXTRACT(YEAR FROM CURRENT_DATE)
            """, (identificativo,))
            fatturato_annuale = cursor.fetchone()[0]
            
            if risultato:
                totale_speso = risultato[0]
                # Calcola il grado di sconto usando l'algoritmo ABC
                grado_sconto = algoritmoABC(totale_speso, fatturato_annuale)
                
                logger.info(f"Profilo trovato per identificativo {identificativo}, totale speso: {totale_speso}, "
                           f"fatturato annuale: {fatturato_annuale}, grado sconto: {grado_sconto}")
                
                return grado_sconto
            else:
                # Inserisci nuovo profilo con tutti i campi necessari
                cursor.execute(
                    """
                    INSERT INTO clieti (
                        full_name, 
                        identificativo, 
                        cellulare, 
                        email, 
                        budget_tot_speso
                    ) VALUES (%s, %s, %s, %s, 0) 
                    RETURNING budget_tot_speso
                    """,
                    (full_name, identificativo, cellulare, email)
                )
                conn.commit()
                
                # Per un nuovo profilo, il grado sconto sarà sempre C
                logger.info(f"Nuovo profilo creato per identificativo {identificativo} con budget inizializzato a 0")
                return "C"
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database: {str(e)}")
        return "C"

def process_trasporto(template_data: Dict[str, Any], luogo: str, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template trasporto cercando nel database il mezzo di trasporto più adatto
    in base al tipo di veicolo, luogo di partenza, luogo di arrivo e budget disponibile.
    Se il veicolo scelto costa più del budget o non viene trovato, restituisce l'opzione meno costosa.
    Decrementa il budget_viaggio del costo del trasporto scelto.
    
    Args:
        template_data: Dizionario contenente i dati del template trasporto
        luogo: Stringa contenente il luogo di arrivo
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli del trasporto trovato
    """
    try:
        tipo_veicolo = template_data.get('tipo_veicolo')
        luogo_partenza = template_data.get('luogo_partenza')
        luogo_arrivo = luogo
        
        if not tipo_veicolo or not luogo_partenza or not luogo_arrivo:
            logger.warning("Tipo veicolo, luogo partenza o luogo arrivo non specificati")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Prima prova a trovare il veicolo specificato che rientra nel budget
            if budget_viaggio[0]:
                cursor.execute("""
                    SELECT veicolo, luogo_partenza, luogo_arrivo, costo 
                    FROM trasporti 
                    WHERE veicolo = %s 
                    AND luogo_partenza = %s 
                    AND luogo_arrivo = %s 
                    AND costo <= %s
                    ORDER BY costo ASC
                    LIMIT 1
                """, (tipo_veicolo, luogo_partenza, luogo_arrivo, budget_viaggio[0]))
            else:
                cursor.execute("""
                    SELECT veicolo, luogo_partenza, luogo_arrivo, costo 
                    FROM trasporti 
                    WHERE veicolo = %s 
                    AND luogo_partenza = %s 
                    AND luogo_arrivo = %s
                    ORDER BY costo ASC
                    LIMIT 1
                """, (tipo_veicolo, luogo_partenza, luogo_arrivo))
            
            risultato = cursor.fetchone()
            
            # Se non trova il veicolo specificato o costa troppo, cerca l'opzione meno costosa
            if not risultato:
                logger.info(f"Veicolo {tipo_veicolo} non trovato o troppo costoso, cerco l'opzione meno costosa")
                if budget_viaggio[0]:
                    cursor.execute("""
                        SELECT veicolo, luogo_partenza, luogo_arrivo, costo 
                        FROM trasporti 
                        WHERE luogo_partenza = %s 
                        AND luogo_arrivo = %s 
                        AND costo <= %s
                        ORDER BY costo ASC
                        LIMIT 1
                    """, (luogo_partenza, luogo_arrivo, budget_viaggio[0]))
                else:
                    cursor.execute("""
                        SELECT veicolo, luogo_partenza, luogo_arrivo, costo 
                        FROM trasporti 
                        WHERE luogo_partenza = %s 
                        AND luogo_arrivo = %s
                        ORDER BY costo ASC
                        LIMIT 1
                    """, (luogo_partenza, luogo_arrivo))
                risultato = cursor.fetchone()
            
            if risultato:
                veicolo, partenza, arrivo, costo = risultato
                # Decrementa il budget
                if budget_viaggio[0]:
                    budget_viaggio[0] -= costo
                logger.info(f"Trovato trasporto: {veicolo} da {partenza} a {arrivo} al costo di {costo}")
                return {
                    "veicolo": veicolo,
                    "luogo_partenza": partenza,
                    "luogo_arrivo": arrivo,
                    "costo": costo
                }
            else:
                logger.warning(f"Nessun trasporto trovato da {luogo_partenza} a {luogo_arrivo} nel budget disponibile")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database trasporti: {str(e)}")
        return {}

def process_alloggi(template_data: Dict[str, Any], benessere: Dict[str, Any], luogo: str, persone: int, giorni: int, bambini: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template alloggi cercando nel database strutture che soddisfino i criteri specificati.
    Il costo totale viene calcolato come: costo_albergo * [(persone-bambini) + bambini/2] * giorni
    Cerca l'alloggio ottimale partendo dall'80% del budget fino al 15%.
    
    Args:
        template_data: Dizionario contenente i dati del template alloggi
        benessere: Dizionario contenente le preferenze di benessere
        luogo: Stringa contenente il luogo di destinazione
        persone: Numero totale di persone
        giorni: Durata del soggiorno in giorni
        bambini: Numero di bambini
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli dell'alloggio trovato
    """
    try:
        tipo_alloggio = template_data.get('tipo_alloggio', [])
        if not tipo_alloggio:
            logger.warning("Tipo alloggio non specificato")
            return {}
            
        # Estrai le preferenze di benessere
        ha_benessere = bool(benessere.get('trattamenti', []))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Inizializza le variabili per il ciclo
            percentuale_budget = 0.80  # Inizia dall'80%
            alloggio_trovato = None
            budget_originale = budget_viaggio[0]
            
            while percentuale_budget >= 0.15:  # Continua fino al 15%
                # Calcola il budget per questa iterazione
                budget_attuale = budget_originale * percentuale_budget
                budget_per_notte = budget_attuale / (giorni * ((persone - bambini) + (bambini / 2)))
                
                logger.info(f"Ricerca alloggio con {percentuale_budget*100}% del budget ({budget_per_notte} per notte)")
                
                # Query per trovare l'alloggio
                query = """
                    SELECT nome, stelle, benessere, luogo, tipo, costo 
                    FROM alloggi 
                    WHERE tipo = ANY(%s)
                    AND benessere = %s
                    AND luogo = %s
                    AND costo <= %s
                    ORDER BY stelle DESC, costo ASC
                    LIMIT 1
                """
                
                cursor.execute(query, (tipo_alloggio, ha_benessere, luogo, budget_per_notte))
                risultato = cursor.fetchone()
                
                if risultato:
                    nome, stelle, benessere, luogo, tipo, costo = risultato
                    costo_totale = costo * ((persone - bambini) + (bambini / 2)) * giorni
                    
                    # Se il costo totale è nel budget originale, abbiamo trovato l'alloggio ottimale
                    if costo_totale <= budget_originale:
                        alloggio_trovato = {
                            "nome": nome,
                            "stelle": stelle,
                            "benessere": benessere,
                            "luogo": luogo,
                            "tipo": tipo,
                            "costo_per_notte": costo,
                            "costo_totale": costo_totale,
                            "giorni": giorni,
                            "persone": persone,
                            "bambini": bambini,
                            "percentuale_budget_usata": costo_totale / budget_originale
                        }
                        logger.info(f"Trovato alloggio ottimale: {nome} ({tipo}) a {luogo} con {stelle} stelle")
                        logger.info(f"Costo per notte: {costo}, Costo totale: {costo_totale}")
                        break
                
                # Riduci la percentuale del budget per la prossima iterazione
                percentuale_budget -= 0.05
            
            # Se non abbiamo trovato un alloggio ottimale, cerca il meno costoso
            if not alloggio_trovato:
                logger.info("Nessun alloggio ottimale trovato, cerco il meno costoso")
                query = """
                    SELECT nome, stelle, benessere, luogo, tipo, costo 
                    FROM alloggi 
                    WHERE tipo = ANY(%s)
                    AND benessere = %s
                    AND luogo = %s
                    ORDER BY costo ASC
                    LIMIT 1
                """
                
                cursor.execute(query, (tipo_alloggio, ha_benessere, luogo))
                risultato = cursor.fetchone()
                
                if risultato:
                    nome, stelle, benessere, luogo, tipo, costo = risultato
                    costo_totale = costo * ((persone - bambini) + (bambini / 2)) * giorni
                    
                    alloggio_trovato = {
                        "nome": nome,
                        "stelle": stelle,
                        "benessere": benessere,
                        "luogo": luogo,
                        "tipo": tipo,
                        "costo_per_notte": costo,
                        "costo_totale": costo_totale,
                        "giorni": giorni,
                        "persone": persone,
                        "bambini": bambini,
                        "percentuale_budget_usata": costo_totale / budget_originale
                    }
                    logger.info(f"Trovato alloggio meno costoso: {nome} ({tipo}) a {luogo} con {stelle} stelle")
                    logger.info(f"Costo per notte: {costo}, Costo totale: {costo_totale}")
            
            if alloggio_trovato:
                # Decrementa il budget
                budget_viaggio[0] -= alloggio_trovato["costo_totale"]
                return alloggio_trovato
            else:
                logger.warning(f"Nessun alloggio trovato per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database alloggi: {str(e)}")
        return {}

def process_noleggi(template_data: Dict[str, Any], giorni: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template noleggi cercando nel database il veicolo più adatto
    in base al numero di posti, tipo di cambio e budget disponibile.
    Se il numero di posti richiesto è maggiore di 9, cerca più veicoli che sommati
    coprano il numero di posti necessario.
    Se non è possibile coprire tutti i posti, restituisce comunque i veicoli trovati.
    Se il tipo di cambio non è specificato, cerca veicoli con qualsiasi tipo di cambio.
    Il costo totale non deve superare l'80% del budget rimanente.
    Il costo in tabella è al giorno, quindi viene moltiplicato per i giorni totali.
    
    Args:
        template_data: Dizionario contenente i dati del template noleggi
        giorni: Numero di giorni di noleggio
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli dei veicoli noleggiati
    """
    try:
        n_posti = template_data.get('n_posti')
        tipo_cambio = template_data.get('tipo_cambio')
        
        if not n_posti:
            logger.warning("Numero posti non specificato")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Calcola il budget massimo per il noleggio (80% del budget rimanente)
            budget_max_noleggio = budget_viaggio[0] * 0.80
            budget_giornaliero = budget_max_noleggio / giorni
            
            logger.info(f"Ricerca veicoli con budget giornaliero di {budget_giornaliero}")
            
            veicoli = []
            posti_rimanenti = n_posti
            costo_totale = 0
            posti_coperti = 0
            
            while posti_rimanenti > 0:
                # Query per trovare il veicolo più adatto
                query = """
                    SELECT nome, marca, n_posti, cambio, costo 
                    FROM veicoli 
                    WHERE n_posti <= %s
                    AND costo <= %s
                """
                params = [posti_rimanenti, budget_giornaliero]
                
                if tipo_cambio:
                    query += " AND cambio = %s"
                    params.append(tipo_cambio)
                
                query += " ORDER BY n_posti DESC, costo ASC LIMIT 1"
                
                cursor.execute(query, params)
                risultato = cursor.fetchone()
                
                if risultato:
                    nome, marca, posti, cambio, costo_giornaliero = risultato
                    costo_veicolo = costo_giornaliero * giorni
                    
                    veicolo = {
                        "nome": nome,
                        "marca": marca,
                        "n_posti": posti,
                        "cambio": cambio,
                        "costo_giornaliero": costo_giornaliero,
                        "costo_totale": costo_veicolo
                    }
                    
                    veicoli.append(veicolo)
                    posti_rimanenti -= posti
                    posti_coperti += posti
                    costo_totale += costo_veicolo
                    
                    logger.info(f"Trovato veicolo: {marca} {nome} con {posti} posti e cambio {cambio}")
                    logger.info(f"Costo giornaliero: {costo_giornaliero}, Costo totale: {costo_veicolo}")
                else:
                    logger.warning(f"Impossibile trovare altri veicoli per coprire i posti rimanenti: {posti_rimanenti}")
                    break
            
            if veicoli:
                risultato = {
                    "veicoli": veicoli,
                    "costo_totale": costo_totale,
                    "posti_richiesti": n_posti,
                    "posti_coperti": posti_coperti,
                    "posti_mancanti": n_posti - posti_coperti,
                    "numero_veicoli": len(veicoli)
                }
                
                # Decrementa il budget
                budget_viaggio[0] -= costo_totale
                
                return risultato
            else:
                logger.warning("Nessun veicolo trovato per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database veicoli: {str(e)}")
        return {}

def process_naturalistico(template_data: Dict[str, Any], luogo: str, persone: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template naturalistico cercando nel database le attività disponibili
    in base al tipo di attività, luogo e budget disponibile.
    Se è richiesta una guida, aggiunge il costo fisso di 35€.
    
    Args:
        template_data: Dizionario contenente i dati del template naturalistico
        luogo: Stringa contenente il luogo di destinazione
        persone: Numero di persone partecipanti
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli delle attività trovate
    """
    try:
        attivita = template_data.get('attivita', [])
        guida_richiesta = template_data.get('guida_esperta', False)
        lingua_guida = template_data.get('lingua_guida', 'italiano')
        
        if not attivita:
            logger.warning("Nessuna attività specificata nel template naturalistico")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            attivita_trovate = []
            costo_totale = 0
            
            for tipo in attivita[0]:  # attivita è una lista di liste
                # Inizializza le variabili per il ciclo
                tentativi = 0
                max_tentativi = 10
                attivita_trovata = None
                
                # Query base per trovare l'attività
                query_base = """
                    SELECT nome_societa, tipo, prezzo_persona, luogo
                    FROM naturalistiche
                    WHERE tipo = %s
                    AND luogo = %s
                """
                
                # Prima prova con selezione casuale
                while tentativi < max_tentativi:
                    query = query_base + " ORDER BY RANDOM() LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome_societa, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome_societa": nome_societa,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita
                            }
                            break
                    
                    tentativi += 1
                
                # Se non è stata trovata un'attività nel budget dopo i tentativi casuali,
                # prova con la più economica
                if not attivita_trovata:
                    query = query_base + " ORDER BY prezzo_persona ASC LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome_societa, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome_societa": nome_societa,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita
                            }
                
                if attivita_trovata:
                    attivita_trovate.append(attivita_trovata)
                    costo_totale += attivita_trovata["costo_totale"]
                    
                    logger.info(f"Trovata attività: {tipo} con {attivita_trovata['nome_societa']} a {luogo}")
                    logger.info(f"Prezzo per persona: {attivita_trovata['prezzo_persona']}, Costo totale: {attivita_trovata['costo_totale']}")
                else:
                    logger.warning(f"Nessuna attività di tipo {tipo} trovata per {luogo} nel budget disponibile")
            
            # Aggiungi il costo della guida se richiesta
            if guida_richiesta:
                costo_guida = 35
                costo_totale += costo_guida
                logger.info(f"Aggiunto costo guida: {costo_guida}")
            
            if attivita_trovate:
                risultato = {
                    "attivita": attivita_trovate,
                    "costo_totale": costo_totale,
                    "guida": {
                        "richiesta": guida_richiesta,
                        "lingua": lingua_guida,
                        "costo": 35 if guida_richiesta else 0
                    } if guida_richiesta else None
                }
                
                # Decrementa il budget
                budget_viaggio[0] -= costo_totale
                
                return risultato
            else:
                logger.warning("Nessuna attività trovata per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database naturalistiche: {str(e)}")
        return {}

def process_avventura(template_data: Dict[str, Any], luogo: str, persone: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template avventura cercando nel database le attività disponibili
    in base al tipo di attività, livello di difficoltà, luogo e budget disponibile.
    Se è richiesta una guida, aggiunge il costo fisso di 35€.
    
    Args:
        template_data: Dizionario contenente i dati del template avventura
        luogo: Stringa contenente il luogo di destinazione
        persone: Numero di persone partecipanti
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli delle attività trovate
    """
    try:
        attivita = template_data.get('attivita', [])
        livelli_difficolta = template_data.get('livello_difficoltà', [])
        guida_richiesta = template_data.get('guida_esperta', False)
        lingua_guida = template_data.get('lingua_guida', 'italiano')
        
        if not attivita or not livelli_difficolta:
            logger.warning("Attività o livelli di difficoltà non specificati nel template avventura")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            attivita_trovate = []
            costo_totale = 0
            
            for tipo in attivita[0]:  # attivita è una lista di liste
                # Inizializza le variabili per il ciclo
                tentativi = 0
                max_tentativi = 10
                attivita_trovata = None
                
                # Query base per trovare l'attività
                query_base = """
                    SELECT nome, tipo, livello_difficolta, prezzo_persona, luogo
                    FROM avventure
                    WHERE tipo = %s
                    AND luogo = %s
                    AND livello_difficolta = ANY(%s)
                """
                
                # Prima prova con selezione casuale
                while tentativi < max_tentativi:
                    query = query_base + " ORDER BY RANDOM() LIMIT 1"
                    cursor.execute(query, (tipo, luogo, livelli_difficolta))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome, tipo, livello, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome": nome,
                                "tipo": tipo,
                                "livello_difficolta": livello,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita
                            }
                            break
                    
                    tentativi += 1
                
                # Se non è stata trovata un'attività nel budget dopo i tentativi casuali,
                # prova con la più economica
                if not attivita_trovata:
                    query = query_base + " ORDER BY prezzo_persona ASC LIMIT 1"
                    cursor.execute(query, (tipo, luogo, livelli_difficolta))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome, tipo, livello, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome": nome,
                                "tipo": tipo,
                                "livello_difficolta": livello,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita
                            }
                
                if attivita_trovata:
                    attivita_trovate.append(attivita_trovata)
                    costo_totale += attivita_trovata["costo_totale"]
                    
                    logger.info(f"Trovata attività: {tipo} con {attivita_trovata['nome']} a {luogo}")
                    logger.info(f"Livello: {attivita_trovata['livello_difficolta']}, Prezzo per persona: {attivita_trovata['prezzo_persona']}, Costo totale: {attivita_trovata['costo_totale']}")
                else:
                    logger.warning(f"Nessuna attività di tipo {tipo} trovata per {luogo} nel budget disponibile")
            
            # Aggiungi il costo della guida se richiesta
            if guida_richiesta:
                costo_guida = 35
                costo_totale += costo_guida
                logger.info(f"Aggiunto costo guida: {costo_guida}")
            
            if attivita_trovate:
                risultato = {
                    "attivita": attivita_trovate,
                    "costo_totale": costo_totale,
                    "guida": {
                        "richiesta": guida_richiesta,
                        "lingua": lingua_guida,
                        "costo": 35 if guida_richiesta else 0
                    } if guida_richiesta else None
                }
                
                # Decrementa il budget
                budget_viaggio[0] -= costo_totale
                
                return risultato
            else:
                logger.warning("Nessuna attività trovata per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database avventure: {str(e)}")
        return {}

def process_montagna(template_data: Dict[str, Any], luogo: str, persone: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template montagna cercando nel database le attività disponibili
    in base al tipo di attività, luogo e budget disponibile.
    Se è richiesta l'attrezzatura, aggiunge il costo fisso di 15€ per persona.
    
    Args:
        template_data: Dizionario contenente i dati del template montagna
        luogo: Stringa contenente il luogo di destinazione
        persone: Numero di persone partecipanti
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli delle attività trovate
    """
    try:
        attivita = template_data.get('attivita', [])
        attrezzatura_richiesta = template_data.get('attrezzatura', False)
        
        if not attivita:
            logger.warning("Nessuna attività specificata nel template montagna")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            attivita_trovate = []
            costo_totale = 0
            
            for tipo in attivita[0]:  # attivita è una lista di liste
                # Inizializza le variabili per il ciclo
                tentativi = 0
                max_tentativi = 10
                attivita_trovata = None
                
                # Query base per trovare l'attività
                query_base = """
                    SELECT nome_societa, tipo, prezzo_persona, luogo
                    FROM montagna
                    WHERE tipo = %s
                    AND luogo = %s
                """
                
                # Prima prova con selezione casuale
                while tentativi < max_tentativi:
                    query = query_base + " ORDER BY RANDOM() LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome_societa, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        # Aggiungi il costo dell'attrezzatura se richiesta
                        if attrezzatura_richiesta:
                            costo_attivita += 15 * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome_societa": nome_societa,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita,
                                "attrezzatura": {
                                    "richiesta": attrezzatura_richiesta,
                                    "costo": 15 * persone if attrezzatura_richiesta else 0
                                } if attrezzatura_richiesta else None
                            }
                            break
                    
                    tentativi += 1
                
                # Se non è stata trovata un'attività nel budget dopo i tentativi casuali,
                # prova con la più economica
                if not attivita_trovata:
                    query = query_base + " ORDER BY prezzo_persona ASC LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome_societa, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        # Aggiungi il costo dell'attrezzatura se richiesta
                        if attrezzatura_richiesta:
                            costo_attivita += 15 * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome_societa": nome_societa,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita,
                                "attrezzatura": {
                                    "richiesta": attrezzatura_richiesta,
                                    "costo": 15 * persone if attrezzatura_richiesta else 0
                                } if attrezzatura_richiesta else None
                            }
                
                if attivita_trovata:
                    attivita_trovate.append(attivita_trovata)
                    costo_totale += attivita_trovata["costo_totale"]
                    
                    logger.info(f"Trovata attività: {tipo} con {attivita_trovata['nome_societa']} a {luogo}")
                    logger.info(f"Prezzo per persona: {attivita_trovata['prezzo_persona']}, Costo totale: {attivita_trovata['costo_totale']}")
                    if attrezzatura_richiesta:
                        logger.info(f"Costo attrezzatura: {15 * persone}")
                else:
                    logger.warning(f"Nessuna attività di tipo {tipo} trovata per {luogo} nel budget disponibile")
            
            if attivita_trovate:
                risultato = {
                    "attivita": attivita_trovate,
                    "costo_totale": costo_totale
                }
                
                # Decrementa il budget
                budget_viaggio[0] -= costo_totale
                
                return risultato
            else:
                logger.warning("Nessuna attività trovata per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database montagna: {str(e)}")
        return {}

def process_mare(template_data: Dict[str, Any], luogo: str, persone: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template mare cercando nel database le attività disponibili
    in base al tipo di attività, luogo e budget disponibile.
    Se è richiesta l'attrezzatura, aggiunge il costo fisso di 15€ per persona.
    
    Args:
        template_data: Dizionario contenente i dati del template mare
        luogo: Stringa contenente il luogo di destinazione
        persone: Numero di persone partecipanti
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli delle attività trovate
    """
    try:
        attivita = template_data.get('attivita', [])
        attrezzatura_richiesta = template_data.get('attrezzatura', False)
        
        if not attivita:
            logger.warning("Nessuna attività specificata nel template mare")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            attivita_trovate = []
            costo_totale = 0
            
            for tipo in attivita[0]:  # attivita è una lista di liste
                # Inizializza le variabili per il ciclo
                tentativi = 0
                max_tentativi = 10
                attivita_trovata = None
                
                # Query base per trovare l'attività
                query_base = """
                    SELECT nome_societa, tipo, prezzo_persona, luogo
                    FROM mare
                    WHERE tipo = %s
                    AND luogo = %s
                """
                
                # Prima prova con selezione casuale
                while tentativi < max_tentativi:
                    query = query_base + " ORDER BY RANDOM() LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome_societa, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        # Aggiungi il costo dell'attrezzatura se richiesta
                        if attrezzatura_richiesta:
                            costo_attivita += 15 * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome_societa": nome_societa,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita,
                                "attrezzatura": {
                                    "richiesta": attrezzatura_richiesta,
                                    "costo": 15 * persone if attrezzatura_richiesta else 0
                                } if attrezzatura_richiesta else None
                            }
                            break
                    
                    tentativi += 1
                
                # Se non è stata trovata un'attività nel budget dopo i tentativi casuali,
                # prova con la più economica
                if not attivita_trovata:
                    query = query_base + " ORDER BY prezzo_persona ASC LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome_societa, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        # Aggiungi il costo dell'attrezzatura se richiesta
                        if attrezzatura_richiesta:
                            costo_attivita += 15 * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome_societa": nome_societa,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita,
                                "attrezzatura": {
                                    "richiesta": attrezzatura_richiesta,
                                    "costo": 15 * persone if attrezzatura_richiesta else 0
                                } if attrezzatura_richiesta else None
                            }
                
                if attivita_trovata:
                    attivita_trovate.append(attivita_trovata)
                    costo_totale += attivita_trovata["costo_totale"]
                    
                    logger.info(f"Trovata attività: {tipo} con {attivita_trovata['nome_societa']} a {luogo}")
                    logger.info(f"Prezzo per persona: {attivita_trovata['prezzo_persona']}, Costo totale: {attivita_trovata['costo_totale']}")
                    if attrezzatura_richiesta:
                        logger.info(f"Costo attrezzatura: {15 * persone}")
                else:
                    logger.warning(f"Nessuna attività di tipo {tipo} trovata per {luogo} nel budget disponibile")
            
            if attivita_trovate:
                risultato = {
                    "attivita": attivita_trovate,
                    "costo_totale": costo_totale
                }
                
                # Decrementa il budget
                budget_viaggio[0] -= costo_totale
                
                return risultato
            else:
                logger.warning("Nessuna attività trovata per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database mare: {str(e)}")
        return {}

def process_gastronomia(template_data: Dict[str, Any], luogo: str, persone: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template gastronomia cercando nel database le attività disponibili
    in base al tipo di degustazione, luogo e budget disponibile.
    Se sono richiesti corsi di cucina, aggiunge il costo fisso di 20€ per persona.
    
    Args:
        template_data: Dizionario contenente i dati del template gastronomia
        luogo: Stringa contenente il luogo di destinazione
        persone: Numero di persone partecipanti
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli delle attività trovate
    """
    try:
        degustazioni = template_data.get('degustazioni', [])
        corsi_richiesti = template_data.get('corsi_cucina', False)
        
        if not degustazioni:
            logger.warning("Nessuna degustazione specificata nel template gastronomia")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            attivita_trovate = []
            costo_totale = 0
            
            for tipo in degustazioni[0]:  # degustazioni è una lista di liste
                # Inizializza le variabili per il ciclo
                tentativi = 0
                max_tentativi = 10
                attivita_trovata = None
                
                # Query base per trovare l'attività
                query_base = """
                    SELECT nome, degustazioni, prezzo_persona, luogo
                    FROM gastronomia
                    WHERE degustazioni = %s
                    AND luogo = %s
                """
                
                # Prima prova con selezione casuale
                while tentativi < max_tentativi:
                    query = query_base + " ORDER BY RANDOM() LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome, degustazioni, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        # Aggiungi il costo dei corsi di cucina se richiesti
                        if corsi_richiesti:
                            costo_attivita += 20 * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome": nome,
                                "tipo": degustazioni,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita,
                                "corsi_cucina": {
                                    "richiesti": corsi_richiesti,
                                    "costo": 20 * persone if corsi_richiesti else 0
                                } if corsi_richiesti else None
                            }
                            break
                    
                    tentativi += 1
                
                # Se non è stata trovata un'attività nel budget dopo i tentativi casuali,
                # prova con la più economica
                if not attivita_trovata:
                    query = query_base + " ORDER BY prezzo_persona ASC LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome, degustazioni, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        # Aggiungi il costo dei corsi di cucina se richiesti
                        if corsi_richiesti:
                            costo_attivita += 20 * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome": nome,
                                "tipo": degustazioni,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita,
                                "corsi_cucina": {
                                    "richiesti": corsi_richiesti,
                                    "costo": 20 * persone if corsi_richiesti else 0
                                } if corsi_richiesti else None
                            }
                
                if attivita_trovata:
                    attivita_trovate.append(attivita_trovata)
                    costo_totale += attivita_trovata["costo_totale"]
                    
                    logger.info(f"Trovata degustazione: {degustazioni} con {attivita_trovata['nome']} a {luogo}")
                    logger.info(f"Prezzo per persona: {attivita_trovata['prezzo_persona']}, Costo totale: {attivita_trovata['costo_totale']}")
                    if corsi_richiesti:
                        logger.info(f"Costo corsi di cucina: {20 * persone}")
                else:
                    logger.warning(f"Nessuna degustazione di tipo {tipo} trovata per {luogo} nel budget disponibile")
            
            if attivita_trovate:
                risultato = {
                    "attivita": attivita_trovate,
                    "costo_totale": costo_totale
                }
                
                # Decrementa il budget
                budget_viaggio[0] -= costo_totale
                
                return risultato
            else:
                logger.warning("Nessuna attività trovata per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database gastronomia: {str(e)}")
        return {}

def process_citta_arte(template_data: Dict[str, Any], luogo: str, persone: int, budget_viaggio: list) -> Dict[str, Any]:
    """
    Processa il template città e arte cercando nel database le attività culturali disponibili
    in base al tipo di attività, luogo e budget disponibile.
    Se è richiesta una guida, aggiunge il costo fisso di 35€.
    
    Args:
        template_data: Dizionario contenente i dati del template città e arte
        luogo: Stringa contenente il luogo di destinazione
        persone: Numero di persone partecipanti
        budget_viaggio: Lista contenente il budget disponibile per il viaggio [budget]
        
    Returns:
        Dict[str, Any]: Dizionario contenente i dettagli delle attività trovate
    """
    try:
        attivita = template_data.get('attivita', [])
        guida_richiesta = template_data.get('guida_turistica', False)
        lingua_guida = template_data.get('lingua_guida', 'italiano')
        
        if not attivita:
            logger.warning("Nessuna attività specificata nel template città e arte")
            return {}
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            attivita_trovate = []
            costo_totale = 0
            
            for tipo in attivita[0]:  # attivita è una lista di liste
                # Inizializza le variabili per il ciclo
                tentativi = 0
                max_tentativi = 10
                attivita_trovata = None
                
                # Query base per trovare l'attività
                query_base = """
                    SELECT nome, tipo, prezzo_persona, luogo
                    FROM citta_arte
                    WHERE tipo = %s
                    AND luogo = %s
                """
                
                # Prima prova con selezione casuale
                while tentativi < max_tentativi:
                    query = query_base + " ORDER BY RANDOM() LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome": nome,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita
                            }
                            break
                    
                    tentativi += 1
                
                # Se non è stata trovata un'attività nel budget dopo i tentativi casuali,
                # prova con la più economica
                if not attivita_trovata:
                    query = query_base + " ORDER BY prezzo_persona ASC LIMIT 1"
                    cursor.execute(query, (tipo, luogo))
                    risultato = cursor.fetchone()
                    
                    if risultato:
                        nome, tipo, prezzo_persona, luogo = risultato
                        costo_attivita = prezzo_persona * persone
                        
                        if costo_attivita <= budget_viaggio[0]:
                            attivita_trovata = {
                                "nome": nome,
                                "tipo": tipo,
                                "prezzo_persona": prezzo_persona,
                                "luogo": luogo,
                                "costo_totale": costo_attivita
                            }
                
                if attivita_trovata:
                    attivita_trovate.append(attivita_trovata)
                    costo_totale += attivita_trovata["costo_totale"]
                    
                    logger.info(f"Trovata attività: {tipo} con {attivita_trovata['nome']} a {luogo}")
                    logger.info(f"Prezzo per persona: {attivita_trovata['prezzo_persona']}, Costo totale: {attivita_trovata['costo_totale']}")
                else:
                    logger.warning(f"Nessuna attività di tipo {tipo} trovata per {luogo} nel budget disponibile")
            
            # Aggiungi il costo della guida se richiesta
            if guida_richiesta:
                costo_guida = 35
                costo_totale += costo_guida
                logger.info(f"Aggiunto costo guida: {costo_guida}")
            
            if attivita_trovate:
                risultato = {
                    "attivita": attivita_trovate,
                    "costo_totale": costo_totale,
                    "guida": {
                        "richiesta": guida_richiesta,
                        "lingua": lingua_guida,
                        "costo": 35 if guida_richiesta else 0
                    } if guida_richiesta else None
                }
                
                # Decrementa il budget
                budget_viaggio[0] -= costo_totale
                
                return risultato
            else:
                logger.warning("Nessuna attività trovata per i criteri specificati")
                return {}
                
        finally:
            cursor.close()
            release_connection(conn)
            
    except Exception as e:
        logger.error(f"Errore nell'interrogazione del database citta_arte: {str(e)}")
        return {}

