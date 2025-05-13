import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import Riepilogo from './riepilogo'
import './index.css'
import { StatoConversazioneProvider } from './statoConversazioneContext'

function Main() {
  return (
    <StatoConversazioneProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/riepilogo" element={<Riepilogo />} />
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
