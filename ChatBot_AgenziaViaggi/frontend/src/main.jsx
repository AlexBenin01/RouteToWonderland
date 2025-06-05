import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App'
import Riepilogo from './pages/riepilogo'
import './index.css'
import { StatoConversazioneProvider } from './statoConversazioneContext'

// Funzione per forzare la pulizia del sessionStorage
const forceClearSessionStorage = () => {
  console.log('=== FORZATURA PULIZIA SESSIONSTORAGE ===');
  console.log('Stato prima della pulizia:', Object.keys(sessionStorage));
  
  // Forza la pulizia
  sessionStorage.clear();
  
  // Rimuovi specificamente tutte le chiavi che potrebbero essere presenti
  const keysToRemove = [
    'chatHistory',
    'currentTemplate',
    'riepilogoData',
    'statoConversazione',
    'debugData'
  ];
  
  keysToRemove.forEach(key => {
    sessionStorage.removeItem(key);
    console.log(`Rimossa chiave: ${key}`);
  });
  
  // Verifica che sia effettivamente vuoto
  console.log('Stato dopo la pulizia:', Object.keys(sessionStorage));
  console.log('=== FINE PULIZIA SESSIONSTORAGE ===');
};

// Esegui la pulizia forzata
forceClearSessionStorage();

function Main() {
  // Pulisci il sessionStorage anche al mount del componente
  React.useEffect(() => {
    console.log('Pulizia sessionStorage al mount...');
    forceClearSessionStorage();
  }, []);

  return (
    <StatoConversazioneProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/riepilogo" element={<Riepilogo />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </StatoConversazioneProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Main />
  </React.StrictMode>
)
