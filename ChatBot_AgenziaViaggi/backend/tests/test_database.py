import pytest
from unittest.mock import patch, MagicMock
from backend.librerie.database import get_db_connection, release_connection, init_connection_pool

@pytest.fixture
def mock_pool():
    """Fixture per creare un mock del connection pool"""
    mock = MagicMock()
    mock.getconn = MagicMock()
    mock.putconn = MagicMock()
    return mock

def test_get_db_connection(mock_pool):
    """Test per la connessione al database con parametri di default"""
    with patch('backend.librerie.database.connection_pool', mock_pool):
        conn = get_db_connection()
        mock_pool.getconn.assert_called_once()
        assert conn == mock_pool.getconn.return_value

def test_release_connection(mock_pool):
    """Test per il rilascio della connessione"""
    mock_conn = MagicMock()
    with patch('backend.librerie.database.connection_pool', mock_pool):
        release_connection(mock_conn)
        mock_pool.putconn.assert_called_once_with(mock_conn)

def test_release_connection_no_pool():
    """Test per il rilascio della connessione quando il pool non esiste"""
    mock_conn = MagicMock()
    with patch('backend.librerie.database.connection_pool', None):
        # Non dovrebbe sollevare eccezioni
        release_connection(mock_conn) 