import pytest
from unittest.mock import patch, MagicMock
import json
from backend.librerie.riepilogo import (
    algoritmoABC, process_riepilogo, process_intro, process_contatti,
    process_trasporto, process_alloggi, process_noleggi, process_naturalistico,
    process_avventura, process_montagna, process_mare, process_gastronomia,
    process_citta_arte
)
import requests
from decimal import Decimal

@pytest.fixture
def mock_db():
    """Fixture per il mock del database"""
    mock = MagicMock()
    cursor_mock = MagicMock()
    
    # Configura il mock per fetchone
    cursor_mock.fetchone.side_effect = [
        (100,),  # Per clienti (budget_tot_speso)
        (5000,),  # Per azienda (importo_annuale)
        ("aereo", "Roma", "Firenze", 100),  # Per trasporti
        ("hotel", "Firenze", 100),  # Per alloggi
        ("autobus", "Firenze", 100),  # Per noleggi
        ("birdwatching", "Firenze", 100),  # Per attività naturalistiche
        ("rafting", "Firenze", 100),  # Per attività avventura
        ("sci", "Firenze", 100),  # Per attività montagna
        ("snorkeling", "Firenze", 100),  # Per attività mare
        ("vini", "Firenze", 100),  # Per attività gastronomiche
        ("museo", "Firenze", 100)  # Per attività città d'arte
    ]
    
    # Configura il mock per fetchall
    cursor_mock.fetchall.return_value = [
        {"costo": 100, "descrizione": "Test"}
    ]
    
    # Configura il mock per execute
    def mock_execute(query, params=None):
        if "clienti" in query:
            return (100,)
        elif "azienda" in query:
            return (5000,)
        elif "trasporti" in query:
            return ("aereo", "Roma", "Firenze", 100)
        elif "alloggi" in query:
            return ("hotel", "Firenze", 100)
        elif "veicoli" in query:
            return ("autobus", "Firenze", 100)
        elif "attivita" in query:
            return ("attivita", "Firenze", 100)
        return None
    
    cursor_mock.execute.side_effect = mock_execute
    
    mock.cursor.return_value.__enter__.return_value = cursor_mock
    return mock

def test_algoritmoABC_success():
    """Test dell'algoritmo ABC con valori validi"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"grado_sconto": "B"}
        mock_post.return_value = mock_response
        assert algoritmoABC(1000, 5000) == "B"

def test_algoritmoABC_error():
    """Test dell'algoritmo ABC con valori non validi"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Errore di connessione")
        assert algoritmoABC(1000, 5000) == "C"

def test_algoritmoABC_connection_error():
    """Test dell'algoritmo ABC con errore di connessione"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Errore di connessione")
        assert algoritmoABC(1000, 5000) == "C"

def test_algoritmoABC_timeout():
    """Test dell'algoritmo ABC con timeout"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        assert algoritmoABC(1000, 5000) == "C"

def test_algoritmoABC_request_error():
    """Test dell'algoritmo ABC con errore nella richiesta"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Errore nella richiesta")
        assert algoritmoABC(1000, 5000) == "C"

def test_algoritmoABC_generic_error():
    """Test dell'algoritmo ABC con errore generico"""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("Errore generico")
        assert algoritmoABC(1000, 5000) == "C"

def test_algoritmoABC_decimal_input():
    """Test dell'algoritmo ABC con input Decimal"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"grado_sconto": "A"}
        mock_post.return_value = mock_response
        assert algoritmoABC(Decimal('1000.50'), Decimal('5000.75')) == "A"

def test_algoritmoABC_invalid_response():
    """Test dell'algoritmo ABC con risposta non valida"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Risposta senza grado_sconto
        mock_post.return_value = mock_response
        assert algoritmoABC(1000, 5000) == "C"

def test_algoritmoABC_negative_values():
    """Test dell'algoritmo ABC con valori negativi"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"grado_sconto": "C"}
        mock_post.return_value = mock_response
        assert algoritmoABC(-1000, -5000) == "C"

def test_process_intro():
    """Test del processamento dell'intro"""
    template_data = {
        "nazione_destinazione": "Italia",
        "regione_citta_destinazione": "Toscana, Firenze",
        "departure_date": "2024-07-01",
        "numero_partecipanti": 2,
        "tipo_partecipanti": "adulti",
        "mood_vacanza": ["citta_arte", "gastronomia"],
        "budget_viaggio": 1000,
        "trip_duration": 7
    }
    result = process_intro(template_data)
    assert isinstance(result, str)
    assert "Firenze" in result

def test_process_intro_missing_regione_citta():
    """Test process_intro con regione_citta_destinazione mancante"""
    template_data = {}
    result = process_intro(template_data)
    assert result == ""

def test_process_intro_regione_non_esistente(monkeypatch):
    """Test process_intro con una regione che non esiste"""
    template_data = {"regione_citta_destinazione": "RegioneFinta"}
    class FakeCursor:
        def execute(self, *a, **kw): pass
        def fetchone(self): return None
        def close(self): pass
    class FakeConn:
        def cursor(self): return FakeCursor()
    monkeypatch.setattr("backend.librerie.riepilogo.get_db_connection", lambda: FakeConn())
    monkeypatch.setattr("backend.librerie.riepilogo.release_connection", lambda conn: None)
    result = process_intro(template_data)
    assert result == "RegioneFinta"

def test_process_intro_citta_specificata(monkeypatch):
    """Test process_intro con una città già specificata"""
    template_data = {"regione_citta_destinazione": "Firenze"}
    class FakeCursor:
        def execute(self, *a, **kw):
            if "destinazioni_regionali" in a[0]:
                self._is_regione = False
        def fetchone(self): return None
        def close(self): pass
    class FakeConn:
        def cursor(self): return FakeCursor()
    monkeypatch.setattr("backend.librerie.riepilogo.get_db_connection", lambda: FakeConn())
    monkeypatch.setattr("backend.librerie.riepilogo.release_connection", lambda conn: None)
    result = process_intro(template_data)
    assert result == "Firenze"

def test_process_intro_with_all_fields():
    """Test process_intro con tutti i campi presenti"""
    template_data = {
        "nazione_destinazione": "Italia",
        "regione_citta_destinazione": "Toscana, Firenze",
        "departure_date": "2024-07-01",
        "numero_partecipanti": 2,
        "tipo_partecipanti": "adulti",
        "mood_vacanza": ["citta_arte", "gastronomia"],
        "budget_viaggio": 1000,
        "trip_duration": 7,
        "note_aggiuntive": "Test note"
    }
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Toscana", "Firenze")
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        result = process_intro(template_data)
        assert isinstance(result, str)
        assert "Firenze" in result

def test_process_intro_with_invalid_date():
    """Test process_intro con data non valida"""
    template_data = {
        "regione_citta_destinazione": "Toscana, Firenze",
        "departure_date": "invalid-date"
    }
    result = process_intro(template_data)
    assert isinstance(result, str)
    assert "Firenze" in result

def test_process_intro_with_special_characters():
    """Test process_intro con caratteri speciali"""
    template_data = {
        "regione_citta_destinazione": "Toscana, Firenze",
        "note_aggiuntive": "Test con caratteri speciali: !@#$%^&*()"
    }
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Toscana", "Firenze")
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        result = process_intro(template_data)
        assert isinstance(result, str)
        assert "Firenze" in result

def test_process_contatti():
    """Test del processamento dei contatti"""
    template_data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
        "numero_cellulare": "+39 123 456 7890",
        "email": "mario.rossi@example.com"
    }
    with patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"):
        result = process_contatti(template_data)
        assert isinstance(result, str)
        assert result in ["A", "B", "C"]

def test_process_contatti_identificativo_mancante():
    """Test process_contatti con identificativo mancante"""
    template_data = {"full_name": "Mario Rossi"}
    result = process_contatti(template_data)
    assert result == "C"

def test_process_contatti_profilo_esistente(monkeypatch):
    """Test process_contatti con profilo già esistente"""
    template_data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
        "numero_cellulare": "+39 123 456 7890",
        "email": "mario.rossi@example.com"
    }
    class FakeCursor:
        def execute(self, query, params=None):
            if "clienti" in query:
                self._call = "clienti"
            elif "azienda" in query:
                self._call = "azienda"
        def fetchone(self):
            if hasattr(self, '_call') and self._call == "clienti":
                return (100,)
            elif hasattr(self, '_call') and self._call == "azienda":
                return (5000,)
            return None
        def close(self): pass
    class FakeConn:
        def cursor(self): return FakeCursor()
    monkeypatch.setattr("backend.librerie.riepilogo.get_db_connection", lambda: FakeConn())
    monkeypatch.setattr("backend.librerie.riepilogo.release_connection", lambda conn: None)
    monkeypatch.setattr("backend.librerie.riepilogo.algoritmoABC", lambda a, b: "B")
    result = process_contatti(template_data)
    assert result == "B"

def test_process_contatti_nuovo_profilo(monkeypatch):
    """Test process_contatti con nuovo profilo (inserimento)"""
    template_data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
        "numero_cellulare": "+39 123 456 7890",
        "email": "mario.rossi@example.com"
    }
    class FakeCursor:
        def __init__(self): self._inserted = False
        def execute(self, query, params=None):
            if "clienti" in query and "SELECT" in query:
                self._call = "clienti"
            elif "azienda" in query:
                self._call = "azienda"
            elif "INSERT" in query:
                self._inserted = True
        def fetchone(self):
            if hasattr(self, '_call') and self._call == "clienti":
                return None
            elif hasattr(self, '_call') and self._call == "azienda":
                return (5000,)
            return None
        def close(self): pass
    class FakeConn:
        def cursor(self): return FakeCursor()
        def commit(self): pass
    monkeypatch.setattr("backend.librerie.riepilogo.get_db_connection", lambda: FakeConn())
    monkeypatch.setattr("backend.librerie.riepilogo.release_connection", lambda conn: None)
    result = process_contatti(template_data)
    assert result == "C"

def test_process_contatti_db_error(monkeypatch):
    """Test process_contatti con errore nel database"""
    template_data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
        "numero_cellulare": "+39 123 456 7890",
        "email": "mario.rossi@example.com"
    }
    monkeypatch.setattr("backend.librerie.riepilogo.get_db_connection", lambda: (_ for _ in ()).throw(Exception("DB error")))
    result = process_contatti(template_data)
    assert result == "C"

def test_process_contatti_with_invalid_email():
    """Test process_contatti con email non valida"""
    template_data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
        "numero_cellulare": "+39 123 456 7890",
        "email": "invalid-email"
    }
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        result = process_contatti(template_data)
        assert result == "C"

def test_process_contatti_with_invalid_phone():
    """Test process_contatti con numero di telefono non valido"""
    template_data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
        "numero_cellulare": "invalid-phone",
        "email": "mario.rossi@example.com"
    }
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        result = process_contatti(template_data)
        assert result == "C"

def test_process_contatti_with_invalid_fiscal_code():
    """Test process_contatti con codice fiscale non valido"""
    template_data = {
        "full_name": "Mario Rossi",
        "codice_fiscale_o_partita_iva": "invalid-fiscal-code",
        "numero_cellulare": "+39 123 456 7890",
        "email": "mario.rossi@example.com"
    }
    with patch('backend.librerie.riepilogo.algoritmoABC', return_value="C"):
        result = process_contatti(template_data)
        assert result == "C"

def test_process_trasporto():
    """Test del processamento del trasporto con dati validi e budget sufficiente"""
    template_data = {
        "tipo_veicolo": "aereo",
        "luogo_partenza": "Roma",
        "luogo_arrivo": "Firenze",
        "posti_auto": 2
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]  # Budget sufficiente
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("aereo", "Roma", "Firenze", 100)
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_trasporto(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["veicolo"] == "aereo"
        assert result["luogo_partenza"] == "Roma"
        assert result["luogo_arrivo"] == "Firenze"
        assert result["costo_base"] == 100
        assert result["costo_totale"] == 400  # 100 * 2 persone * 2 (andata e ritorno)
        assert budget_viaggio[0] == 9600  # 10000 - 400

def test_process_trasporto_alternative_vehicle():
    """Test del processamento del trasporto quando il veicolo specificato non è disponibile"""
    template_data = {
        "tipo_veicolo": "aereo",
        "luogo_partenza": "Roma",
        "luogo_arrivo": "Firenze",
        "posti_auto": 2
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            None,  # Prima query (veicolo specificato)
            ("treno", "Roma", "Firenze", 50)  # Seconda query (alternativa più economica)
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_trasporto(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["veicolo"] == "treno"
        assert result["luogo_partenza"] == "Roma"
        assert result["luogo_arrivo"] == "Firenze"
        assert result["costo_base"] == 50
        assert result["costo_totale"] == 200  # 50 * 2 persone * 2 (andata e ritorno)
        assert budget_viaggio[0] == 9800  # 10000 - 200

def test_process_trasporto_no_budget():
    """Test del processamento del trasporto senza budget specificato"""
    template_data = {
        "tipo_veicolo": "aereo",
        "luogo_partenza": "Roma",
        "luogo_arrivo": "Firenze",
        "posti_auto": 2
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [0]  # Nessun budget
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("aereo", "Roma", "Firenze", 100)
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_trasporto(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["veicolo"] == "aereo"
        assert result["luogo_partenza"] == "Roma"
        assert result["luogo_arrivo"] == "Firenze"
        assert result["costo_base"] == 100
        assert result["costo_totale"] == 400
        assert budget_viaggio[0] == 0  # Budget non modificato

def test_process_trasporto_budget_exceeded():
    """Test del processamento del trasporto quando il budget viene superato"""
    template_data = {
        "tipo_veicolo": "aereo",
        "luogo_partenza": "Roma",
        "luogo_arrivo": "Firenze",
        "posti_auto": 2
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [100]  # Budget molto basso
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            None,  # Prima query (veicolo specificato)
            ("treno", "Roma", "Firenze", 50)  # Seconda query (alternativa più economica)
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_trasporto(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["veicolo"] == "treno"
        assert result["luogo_partenza"] == "Roma"
        assert result["luogo_arrivo"] == "Firenze"
        assert result["costo_base"] == 50
        assert result["costo_totale"] == 200
        assert budget_viaggio[0] == -100  # 100 - 200

def test_process_alloggi(mock_db):
    """Test del processamento degli alloggi"""
    template_data = {
        "tipo_alloggio": ["hotel"],
        "adulti": 2,
        "bambini": 0,
        "luogo": "Firenze"
    }
    benessere = {}
    luogo = "Firenze"
    persone = 2
    giorni = 7
    bambini = 0
    budget_viaggio = [10000]  # Budget aumentato
    
    with patch('backend.librerie.riepilogo.get_db_connection', return_value=mock_db), \
         patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"):
        result = process_alloggi(template_data, benessere, luogo, persone, giorni, bambini, budget_viaggio)
        assert isinstance(result, dict)
        assert result is not None

def test_process_noleggi(mock_db):
    """Test del processamento dei noleggi"""
    template_data = {
        "tipo_veicolo": "autobus",
        "posti_auto": 2,
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    giorni = 7
    budget_viaggio = [10000]  # Budget aumentato
    
    with patch('backend.librerie.riepilogo.get_db_connection', return_value=mock_db), \
         patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"):
        result = process_noleggi(template_data, luogo, persone, giorni, budget_viaggio)
        assert isinstance(result, dict)
        assert result is not None

def test_process_naturalistico(mock_db):
    """Test del processamento delle attività naturalistiche"""
    template_data = {
        "attivita_naturalistico": ["birdwatching"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]  # Budget aumentato
    
    with patch('backend.librerie.riepilogo.get_db_connection', return_value=mock_db), \
         patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"):
        result = process_naturalistico(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result is not None

def test_process_avventura():
    """Test del processamento delle attività di avventura con dati validi"""
    template_data = {
        "attivita_avventura": ["rafting", "arrampicata"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Rafting", "Firenze", 80, "Discesa in rafting")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_avventura(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Rafting"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 80
        assert result["costo_totale"] == 160  # 80 * 2 persone
        assert result["descrizione"] == "Discesa in rafting"
        assert budget_viaggio[0] == 840  # 1000 - 160

def test_process_avventura_budget_exceeded():
    """Test del processamento delle attività di avventura quando il budget viene superato"""
    template_data = {
        "attivita_avventura": ["rafting", "arrampicata"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [100]  # Budget molto basso

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Rafting", "Firenze", 80, "Discesa in rafting")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_avventura(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 100  # Budget non modificato

def test_process_avventura_db_error():
    """Test del processamento delle attività di avventura con errore del database"""
    template_data = {
        "attivita_avventura": ["rafting", "arrampicata"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_avventura(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato

def test_process_montagna(mock_db):
    """Test del processamento delle attività in montagna"""
    template_data = {
        "attivita_montagna": ["sci"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]  # Budget aumentato
    
    with patch('backend.librerie.riepilogo.get_db_connection', return_value=mock_db), \
         patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"):
        result = process_montagna(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result is not None

def test_process_mare():
    """Test del processamento delle attività al mare con dati validi"""
    template_data = {
        "attivita_mare": ["snorkeling", "subacquea"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Snorkeling", "Firenze", 40, "Esplorazione subacquea")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_mare(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Snorkeling"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 40
        assert result["costo_totale"] == 80  # 40 * 2 persone
        assert result["descrizione"] == "Esplorazione subacquea"
        assert budget_viaggio[0] == 920  # 1000 - 80

def test_process_mare_multiple_activities():
    """Test del processamento delle attività al mare con multiple attività"""
    template_data = {
        "attivita_mare": ["snorkeling", "subacquea"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Snorkeling", "Firenze", 40, "Esplorazione subacquea"),
            ("Subacquea", "Firenze", 90, "Immersione con bombole")
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_mare(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["costo_totale"] == 260  # (40 + 90) * 2 persone
        assert budget_viaggio[0] == 740  # 1000 - 260

def test_process_mare_no_results():
    """Test del processamento delle attività al mare senza risultati"""
    template_data = {
        "attivita_mare": ["snorkeling", "subacquea"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_mare(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato

def test_process_gastronomia(mock_db):
    """Test del processamento delle attività gastronomiche"""
    template_data = {
        "degustazioni": ["vini", "formaggi"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Degustazione Vini", "Firenze", 60, "Assaggio di vini locali")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_gastronomia(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Degustazione Vini"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 60
        assert result["costo_totale"] == 120  # 60 * 2 persone
        assert result["descrizione"] == "Assaggio di vini locali"
        assert budget_viaggio[0] == 880  # 1000 - 120

def test_process_gastronomia_multiple_activities():
    """Test del processamento delle attività gastronomiche con multiple attività"""
    template_data = {
        "degustazioni": ["vini", "formaggi"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Degustazione Vini", "Firenze", 60, "Assaggio di vini locali"),
            ("Degustazione Formaggi", "Firenze", 40, "Assaggio di formaggi locali")
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_gastronomia(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["costo_totale"] == 200  # (60 + 40) * 2 persone
        assert budget_viaggio[0] == 800  # 1000 - 200

def test_process_gastronomia_no_results():
    """Test del processamento delle attività gastronomiche senza risultati"""
    template_data = {
        "degustazioni": ["vini", "formaggi"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_gastronomia(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato

def test_process_citta_arte():
    """Test del processamento delle attività in città d'arte con dati validi"""
    template_data = {
        "attivita_citta_arte": ["museo", "galleria"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Museo Uffizi", "Firenze", 25, "Visita guidata")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_citta_arte(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Museo Uffizi"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 25
        assert result["costo_totale"] == 50  # 25 * 2 persone
        assert result["descrizione"] == "Visita guidata"
        assert budget_viaggio[0] == 950  # 1000 - 50

def test_process_citta_arte_multiple_activities():
    """Test del processamento delle attività in città d'arte con multiple attività"""
    template_data = {
        "attivita_citta_arte": ["museo", "galleria"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Museo Uffizi", "Firenze", 25, "Visita guidata"),
            ("Galleria Accademia", "Firenze", 20, "Visita guidata")
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_citta_arte(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["costo_totale"] == 90  # (25 + 20) * 2 persone
        assert budget_viaggio[0] == 910  # 1000 - 90

def test_process_citta_arte_no_results():
    """Test del processamento delle attività in città d'arte senza risultati"""
    template_data = {
        "attivita_citta_arte": ["attivita_non_esistente"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_citta_arte(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato

def test_process_riepilogo():
    """Test del processamento del riepilogo completo"""
    stato_conversazione = {
        "intro": {
            "nazione_destinazione": "Italia",
            "regione_citta_destinazione": "Toscana, Firenze",
            "departure_date": "2024-07-01",
            "numero_partecipanti": 2,
            "tipo_partecipanti": "adulti",
            "mood_vacanza": ["citta_arte", "gastronomia"],
            "budget_viaggio": 1000,
            "trip_duration": 7
        },
        "contatti": {
            "full_name": "Mario Rossi",
            "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
            "numero_cellulare": "+39 123 456 7890",
            "email": "mario.rossi@example.com"
        }
    }
    
    with patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"), \
         patch('backend.librerie.riepilogo.process_intro', return_value="Intro test"), \
         patch('backend.librerie.riepilogo.process_contatti', return_value="B"), \
         patch('backend.librerie.riepilogo.process_trasporto', return_value={"costo_totale": 200}), \
         patch('backend.librerie.riepilogo.process_alloggi', return_value={"costo_totale": 300}), \
         patch('backend.librerie.riepilogo.process_noleggi', return_value={"costo_totale": 100}), \
         patch('backend.librerie.riepilogo.process_naturalistico', return_value={"costo_totale": 50}), \
         patch('backend.librerie.riepilogo.process_avventura', return_value={"costo_totale": 50}), \
         patch('backend.librerie.riepilogo.process_montagna', return_value={"costo_totale": 50}), \
         patch('backend.librerie.riepilogo.process_mare', return_value={"costo_totale": 50}), \
         patch('backend.librerie.riepilogo.process_gastronomia', return_value={"costo_totale": 100}), \
         patch('backend.librerie.riepilogo.process_citta_arte', return_value={"costo_totale": 100}):
        
        result = process_riepilogo(json.dumps(stato_conversazione))
        assert isinstance(result, dict)
        assert "intro" in result
        assert "contatti" in result
        assert "riepilogo_costi" in result
        assert isinstance(result["riepilogo_costi"], dict)

def test_process_riepilogo_invalid_json():
    """Test del processamento del riepilogo con JSON non valido"""
    with pytest.raises(json.JSONDecodeError):
        process_riepilogo("invalid json")

def test_process_riepilogo_missing_intro():
    """Test del processamento del riepilogo senza template intro"""
    stato_conversazione = {
        "contatti": {
            "full_name": "Mario Rossi",
            "codice_fiscale_o_partita_iva": "RCCMNL83S18D969H",
            "numero_cellulare": "+39 123 456 7890",
            "email": "mario.rossi@example.com"
        }
    }
    
    with patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"), \
         patch('backend.librerie.riepilogo.process_contatti', return_value="B"):
        result = process_riepilogo(json.dumps(stato_conversazione))
        assert isinstance(result, dict)
        assert "intro" not in result
        assert "contatti" in result
        assert "riepilogo_costi" in result

def test_process_riepilogo_missing_contatti():
    """Test del processamento del riepilogo senza template contatti"""
    stato_conversazione = {
        "intro": {
            "nazione_destinazione": "Italia",
            "regione_citta_destinazione": "Toscana, Firenze",
            "departure_date": "2024-07-01",
            "numero_partecipanti": 2,
            "tipo_partecipanti": "adulti",
            "mood_vacanza": ["citta_arte", "gastronomia"],
            "budget_viaggio": 1000,
            "trip_duration": 7
        }
    }
    
    with patch('backend.librerie.riepilogo.algoritmoABC', return_value="B"), \
         patch('backend.librerie.riepilogo.process_intro', return_value="Intro test"):
        result = process_riepilogo(json.dumps(stato_conversazione))
        assert isinstance(result, dict)
        assert "intro" in result
        assert "contatti" not in result
        assert "riepilogo_costi" in result

def test_process_alloggi_with_benessere():
    """Test del processamento degli alloggi con servizi di benessere"""
    template_data = {
        "tipo_alloggio": ["hotel"],
        "adulti": 2,
        "bambini": 1,
        "luogo": "Firenze"
    }
    benessere = {
        "trattamenti": ["spa", "massaggio"]
    }
    luogo = "Firenze"
    persone = 3
    giorni = 7
    bambini = 1
    budget_viaggio = [5000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Hotel Test", 4, True, "Firenze", "hotel", 100)
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_alloggi(template_data, benessere, luogo, persone, giorni, bambini, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Hotel Test"
        assert result["stelle"] == 4
        assert result["benessere"] is True
        assert result["costo_totale"] == 1750  # 100 * (2 + 0.5) * 7

def test_process_alloggi_no_benessere():
    """Test del processamento degli alloggi senza servizi di benessere"""
    template_data = {
        "tipo_alloggio": ["hotel"],
        "adulti": 2,
        "bambini": 0,
        "luogo": "Firenze"
    }
    benessere = {}
    luogo = "Firenze"
    persone = 2
    giorni = 7
    bambini = 0
    budget_viaggio = [5000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Hotel Test", 3, False, "Firenze", "hotel", 80)
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_alloggi(template_data, benessere, luogo, persone, giorni, bambini, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Hotel Test"
        assert result["stelle"] == 3
        assert result["benessere"] is False
        assert result["costo_totale"] == 1120  # 80 * 2 * 7

def test_process_alloggi_budget_iterations():
    """Test del processamento degli alloggi con diverse iterazioni di budget"""
    template_data = {
        "tipo_alloggio": ["hotel"],
        "adulti": 2,
        "bambini": 0,
        "luogo": "Firenze"
    }
    benessere = {}
    luogo = "Firenze"
    persone = 2
    giorni = 7
    bambini = 0
    budget_viaggio = [5000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        # Simula nessun risultato per i primi tentativi
        mock_cursor.fetchone.side_effect = [
            None,  # 40% del budget
            None,  # 50% del budget
            ("Hotel Test", 3, False, "Firenze", "hotel", 80)  # 60% del budget
        ]
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_alloggi(template_data, benessere, luogo, persone, giorni, bambini, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Hotel Test"
        assert result["costo_totale"] == 1120

def test_process_alloggi_no_results():
    """Test del processamento degli alloggi quando non vengono trovati risultati"""
    template_data = {
        "tipo_alloggio": ["hotel"],
        "adulti": 2,
        "bambini": 0,
        "luogo": "Firenze"
    }
    benessere = {}
    luogo = "Firenze"
    persone = 2
    giorni = 7
    bambini = 0
    budget_viaggio = [5000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_alloggi(template_data, benessere, luogo, persone, giorni, bambini, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_trasporto_exception(mock_db):
    """Test del processamento del trasporto con eccezione"""
    template_data = {
        "tipo_veicolo": "aereo",
        "luogo_partenza": "Roma",
        "luogo_arrivo": "Firenze",
        "posti_auto": 2
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]
    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_trasporto(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_alloggi_exception(mock_db):
    """Test del processamento degli alloggi con eccezione"""
    template_data = {
        "tipo_alloggio": ["hotel"],
        "adulti": 2,
        "bambini": 0,
        "luogo": "Firenze"
    }
    benessere = {}
    luogo = "Firenze"
    persone = 2
    giorni = 7
    bambini = 0
    budget_viaggio = [10000]
    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_alloggi(template_data, benessere, luogo, persone, giorni, bambini, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_noleggi_exception(mock_db):
    """Test del processamento dei noleggi con eccezione"""
    template_data = {
        "tipo_veicolo": "autobus",
        "posti_auto": 2,
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    giorni = 7
    budget_viaggio = [10000]
    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_noleggi(template_data, luogo, persone, giorni, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_naturalistico_exception(mock_db):
    """Test del processamento delle attività naturalistiche con eccezione"""
    template_data = {
        "attivita_naturalistico": ["birdwatching"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]
    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_naturalistico(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_montagna_exception(mock_db):
    """Test del processamento delle attività in montagna con eccezione"""
    template_data = {
        "attivita_montagna": ["sci"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]
    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_montagna(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_gastronomia_exception(mock_db):
    """Test del processamento delle attività gastronomiche con eccezione"""
    template_data = {
        "degustazioni": ["vini"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]
    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_gastronomia(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_citta_arte_exception(mock_db):
    """Test del processamento delle attività in città d'arte con eccezione"""
    template_data = {
        "attivita_citta_arte": ["museo"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [10000]
    with patch('backend.librerie.riepilogo.get_db_connection', side_effect=Exception("Errore DB")):
        result = process_citta_arte(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}

def test_process_naturalistico():
    """Test del processamento delle attività naturalistiche con dati validi"""
    template_data = {
        "attivita_naturalistico": ["birdwatching", "escursioni"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Birdwatching", "Firenze", 50, "Osservazione uccelli")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_naturalistico(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Birdwatching"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 50
        assert result["costo_totale"] == 100  # 50 * 2 persone
        assert result["descrizione"] == "Osservazione uccelli"
        assert budget_viaggio[0] == 900  # 1000 - 100

def test_process_naturalistico_multiple_activities():
    """Test del processamento delle attività naturalistiche con multiple attività"""
    template_data = {
        "attivita_naturalistico": ["birdwatching", "escursioni"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Birdwatching", "Firenze", 50, "Osservazione uccelli"),
            ("Escursione", "Firenze", 30, "Passeggiata naturalistica")
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_naturalistico(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["costo_totale"] == 160  # (50 + 30) * 2 persone
        assert budget_viaggio[0] == 840  # 1000 - 160

def test_process_naturalistico_no_results():
    """Test del processamento delle attività naturalistiche senza risultati"""
    template_data = {
        "attivita_naturalistico": ["birdwatching", "escursioni"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_naturalistico(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato

def test_process_montagna():
    """Test del processamento delle attività in montagna con dati validi"""
    template_data = {
        "attivita_montagna": ["sci", "snowboard"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Sci", "Firenze", 70, "Discesa sugli sci")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_montagna(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Sci"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 70
        assert result["costo_totale"] == 140  # 70 * 2 persone
        assert result["descrizione"] == "Discesa sugli sci"
        assert budget_viaggio[0] == 860  # 1000 - 140

def test_process_montagna_multiple_activities():
    """Test del processamento delle attività in montagna con multiple attività"""
    template_data = {
        "attivita_montagna": ["sci", "snowboard"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Sci", "Firenze", 70, "Discesa sugli sci"),
            ("Snowboard", "Firenze", 60, "Discesa in snowboard")
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_montagna(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["costo_totale"] == 260  # (70 + 60) * 2 persone
        assert budget_viaggio[0] == 740  # 1000 - 260

def test_process_montagna_no_results():
    """Test del processamento delle attività in montagna senza risultati"""
    template_data = {
        "attivita_montagna": ["sci", "snowboard"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_montagna(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato

def test_process_gastronomia():
    """Test del processamento delle attività gastronomiche con dati validi"""
    template_data = {
        "degustazioni": ["vini", "formaggi"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Degustazione Vini", "Firenze", 60, "Assaggio di vini locali")
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_gastronomia(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Degustazione Vini"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 60
        assert result["costo_totale"] == 120  # 60 * 2 persone
        assert result["descrizione"] == "Assaggio di vini locali"
        assert budget_viaggio[0] == 880  # 1000 - 120

def test_process_gastronomia_multiple_activities():
    """Test del processamento delle attività gastronomiche con multiple attività"""
    template_data = {
        "degustazioni": ["vini", "formaggi"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Degustazione Vini", "Firenze", 60, "Assaggio di vini locali"),
            ("Degustazione Formaggi", "Firenze", 40, "Assaggio di formaggi locali")
        ]
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_gastronomia(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["costo_totale"] == 200  # (60 + 40) * 2 persone
        assert budget_viaggio[0] == 800  # 1000 - 200

def test_process_gastronomia_no_results():
    """Test del processamento delle attività gastronomiche senza risultati"""
    template_data = {
        "degustazioni": ["vini", "formaggi"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]

    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_gastronomia(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato

def test_process_citta_arte():
    """Test del processamento delle attività in città d'arte con dati validi"""
    template_data = {
        "attivita_citta_arte": ["museo", "galleria"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ("Museo Uffizi", "Firenze", 25, "Visita guidata")
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_citta_arte(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["nome"] == "Museo Uffizi"
        assert result["luogo"] == "Firenze"
        assert result["costo_base"] == 25
        assert result["costo_totale"] == 50  # 25 * 2 persone
        assert result["descrizione"] == "Visita guidata"

def test_process_citta_arte_multiple_activities():
    """Test del processamento delle attività in città d'arte con multiple attività"""
    template_data = {
        "attivita_citta_arte": ["museo", "galleria"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("Museo Uffizi", "Firenze", 25, "Visita guidata"),
            ("Galleria Accademia", "Firenze", 20, "Visita guidata")
        ]
        mock_db.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = process_citta_arte(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result["costo_totale"] == 90  # (25 + 20) * 2 persone

def test_process_citta_arte_no_results():
    """Test del processamento delle attività in città d'arte senza risultati"""
    template_data = {
        "attivita_citta_arte": ["attivita_non_esistente"],
        "luogo": "Firenze"
    }
    luogo = "Firenze"
    persone = 2
    budget_viaggio = [1000]
    
    with patch('backend.librerie.riepilogo.get_db_connection') as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = process_citta_arte(template_data, luogo, persone, budget_viaggio)
        assert isinstance(result, dict)
        assert result == {}
        assert budget_viaggio[0] == 1000  # Budget non modificato 