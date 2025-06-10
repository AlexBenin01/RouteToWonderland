import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import App from './App'
import Riepilogo from './pages/riepilogo'
import Fine from './pages/fine'
import './index.css'
import { StatoConversazioneProvider } from './statoConversazioneContext'

// Componente ProtectedRoute per proteggere le route
const ProtectedRoute = ({ children, requireOrderCompletion = false }) => {
  const location = useLocation();
  
  // Verifica se l'utente arriva dalla navigazione corretta
  if (!location.state?.fromApp) {
    // Se non arriva dalla navigazione corretta, reindirizza alla home
    return <Navigate to="/" replace />;
  }

  // Se la rotta richiede il completamento dell'ordine
  if (requireOrderCompletion && !location.state?.orderCompleted) {
    // Se l'ordine non è stato completato, reindirizza alla home
    return <Navigate to="/" replace />;
  }
  
  return children;
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <StatoConversazioneProvider>
        <Routes>
          <Route path="/" element={<App />} />
          <Route 
            path="/riepilogo" 
            element={
              <ProtectedRoute>
                <Riepilogo />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/fine" 
            element={
              <ProtectedRoute requireOrderCompletion={true}>
                <Fine />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </StatoConversazioneProvider>
    </BrowserRouter>
  </React.StrictMode>
)
