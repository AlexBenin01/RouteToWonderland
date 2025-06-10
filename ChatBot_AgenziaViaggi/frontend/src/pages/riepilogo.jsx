import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import '../styles/Riepilogo.css';

// Funzione per pulire tutti i dati
const clearAllData = () => {
  console.log('=== PULIZIA COMPLETA DEI DATI ===');
  sessionStorage.clear();
  console.log('Dati puliti:', Object.keys(sessionStorage));
};

function Riepilogo() {
  const location = useLocation();
  const navigate = useNavigate();
  const [riepilogoData, setRiepilogoData] = useState(null);
  const [keepChatActive, setKeepChatActive] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState(() => {
    const savedTemplate = sessionStorage.getItem('currentTemplate');
    console.log('Template iniziale in Riepilogo:', savedTemplate || 'intro');
    return savedTemplate || 'intro';
  });
  const [chatHistory, setChatHistory] = useState(() => {
    // Recupera la chat dal sessionStorage all'inizializzazione
    const savedChat = sessionStorage.getItem('chatHistory');
    return savedChat ? JSON.parse(savedChat) : [];
  });

  // Salva i dati nel sessionStorage quando cambiano
  useEffect(() => {
    if (chatHistory.length > 0) {
      sessionStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }
    if (currentTemplate) {
      sessionStorage.setItem('currentTemplate', currentTemplate);
    }
  }, [chatHistory, currentTemplate]);

  // Funzione per aggiornare il template in modo sicuro
  const updateTemplate = (newTemplate) => {
    console.log('Aggiornamento template in Riepilogo:', newTemplate);
    setCurrentTemplate(newTemplate);
    sessionStorage.setItem('currentTemplate', newTemplate);
  };

  useEffect(() => {
    if (location.state?.riepilogoData) {
      setRiepilogoData(location.state.riepilogoData);
      setKeepChatActive(location.state.keepChatActive || false);
      if (location.state.chatHistory) {
        setChatHistory(location.state.chatHistory);
        sessionStorage.setItem('chatHistory', JSON.stringify(location.state.chatHistory));
      }
      if (location.state.currentTemplate) {
        console.log('Template ricevuto da location state in Riepilogo:', location.state.currentTemplate);
        updateTemplate(location.state.currentTemplate);
      }
    }
  }, [location]);

  // Monitora i cambiamenti del template
  useEffect(() => {
    console.log('Template corrente in Riepilogo:', currentTemplate);
    sessionStorage.setItem('currentTemplate', currentTemplate);
  }, [currentTemplate]);

  const handleBackToChat = () => {
    console.log('Tornando alla chat con template:', currentTemplate);
    // Recupera la chat più recente dal sessionStorage
    const currentChat = sessionStorage.getItem('chatHistory');
    const chatToPass = currentChat ? JSON.parse(currentChat) : chatHistory;
    
    console.log('Chat da passare:', chatToPass);
    
    navigate('/', { 
      state: { 
        chatHistory: chatToPass,
        keepChatActive: keepChatActive,
        currentTemplate: currentTemplate
      }
    });
  };

  // Modifico l'useEffect per la pulizia dei dati
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Rimuoviamo la pulizia automatica qui
      // I dati verranno mantenuti durante la navigazione
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [keepChatActive]);

  const handleCompletaOrdine = async () => {
    try {
      const response = await fetch('http://localhost:8000/completa_ordine', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          budget_usato: riepilogoData.riepilogo_costi.costo_totale_con_sconto,
          documento: riepilogoData.contatti.codice_fiscale_o_partita_iva,
        })
      });

      if (!response.ok) {
        throw new Error('Errore durante il completamento dell\'ordine');
      }

      const data = await response.json();
      // Pulisci tutti i dati della sessione
      clearAllData();
      // Reindirizza alla pagina di fine con lo stato orderCompleted
      navigate('/fine', { 
        replace: true,
        state: { 
          fromApp: true,
          orderCompleted: true 
        }
      });
    } catch (error) {
      console.error('Errore:', error);
      alert('Si è verificato un errore durante il completamento dell\'ordine');
    }
  };

  const renderValue = (value) => {
    if (typeof value === 'object' && value !== null) {
      return (
        <ul className="list-disc pl-4">
          {Object.entries(value).map(([key, val]) => (
            <li key={key}>
              <span className="font-semibold">{key}:</span> {renderValue(val)}
            </li>
          ))}
        </ul>
      );
    }
    return value?.toString() || '';
  };

  const renderIntroSection = (data) => {
    if (!data) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Informazioni Viaggio</h2>
        <div className="info-grid">
          <div className="info-item">
            <div className="info-label">Destinazione</div>
            <div className="location-info">
              <span className="info-value">{data.regione_citta_destinazione}</span>
              <span className="location-separator">-</span>
              <span className="info-value">{data.nazione_destinazione}</span>
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Data di Partenza</div>
            <div className="date-info">
              <span className="info-value">{data.departure_date}</span>
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Viaggiatori</div>
            <div className="info-value">{data.numero_partecipanti} {data.tipo_partecipanti}</div>
          </div>
          <div className="info-item">
            <div className="info-label">Durata Vacanza</div>
            <div className="info-value">{data.trip_duration} giorni</div>
          </div>
        </div>
      </div>
    );
  };

  const renderContattiSection = (data) => {
    if (!data) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Contatti</h2>
        <div className="contact-info">
          <div className="contact-row">
            <div className="info-item">
              <div className="info-label">Nominativo</div>
              <div className="info-value">{data.full_name}</div>
            </div>
            <div className="info-item">
              <div className="info-label">Documento</div>
              <div className="info-value">{data.codice_fiscale_o_partita_iva}</div>
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Contatti</div>
            <div className="contact-item">
              <span className="info-value">{data.numero_cellulare.replace(/-/g, ' ')}</span>
            </div>
            <div className="contact-item">
              <span className="info-value">{data.email}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderTrasportoSection = () => {
    if (!riepilogoData?.trasporto) return null;

    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Trasporto</h2>
        <div className="transport-info">
          <div className="transport-row">
            <div className="info-item">
              <div className="info-label">Tipo veicolo</div>
              <div className="info-value">{riepilogoData.trasporto.veicolo}</div>
            </div>
            <div className="info-item">
              <div className="info-label">Percorso</div>
              <div className="info-value">
                {riepilogoData.trasporto.luogo_partenza} ↔ {riepilogoData.trasporto.luogo_arrivo}
              </div>
            </div>
            <div className="info-item">
              <div className="info-label">Costo base per persona</div>
              <div className="info-value">{riepilogoData.trasporto.costo_base}€</div>
            </div>
          </div>
          <div className="transport-row">
            <div className="info-item">
              <div className="info-label">Costo totale</div>
              <div className="info-value">{riepilogoData.trasporto.costo_totale}€</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderRiepilogoCostiSection = (data) => {
    if (!data) return null;
    return (
      <div className="riepilogo-costi-container">
        <h2 className="costi-title">Riepilogo Costi</h2>
        <div className="costi-main-section">
          <div className="price-container">
            <div className="original-price">
              €{data.costo_totale.toLocaleString()}
            </div>
            <div className="discount-badge">
              {data.percentuale_sconto} di sconto
            </div>
            <div className="final-price">
              €{data.costo_totale_con_sconto.toLocaleString()}
            </div>
          </div>
          
          <div className="budget-container">
            <div className="budget-item">
              <div className="budget-label">Budget Iniziale</div>
              <div className="budget-value initial">
                €{data.budget_iniziale.toLocaleString()}
              </div>
            </div>
            <div className="budget-item">
              <div className="budget-label">Budget Rimanente</div>
              <div className={`budget-value ${data.budget_rimanente < 0 ? 'negative' : 'remaining'}`}>
                €{data.budget_rimanente.toLocaleString()}
              </div>
            </div>
          </div>

          <button
            onClick={handleCompletaOrdine}
            className="riepilogo-button bg-green-600 hover:bg-green-700 mt-12"
          >
            Completa Ordine
          </button>
        </div>
      </div>
    );
  };

  const renderAvventuraSection = (data) => {
    if (!data || !data.attivita) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Attività Avventura</h2>
        <div className="rental-grid">
          {data.attivita.map((attivita, index) => (
            <div key={index} className="rental-card">
              <div className="rental-name">{attivita.nome}</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Tipo</span>
                  <span className="rental-value">{attivita.tipo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Livello</span>
                  <span className="rental-value">{attivita.livello_difficolta}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Luogo</span>
                  <span className="rental-value">{attivita.luogo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Prezzo per persona</span>
                  <span className="rental-value">€{attivita.prezzo_persona}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo totale</span>
                  <span className="rental-value">€{attivita.costo_totale}</span>
                </div>
              </div>
            </div>
          ))}
          <div className="rental-card">
            <div className="rental-name">Riepilogo Attività</div>
            <div className="rental-summary">
              <div className="rental-summary-item">
                Numero attività: {data.attivita.length}
              </div>
              
              <div className="rental-summary-item">
                Costo totale: €{data.costo_totale}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderCittaArteSection = (data) => {
    if (!data || !data.attivita) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Città d'Arte</h2>
        <div className="rental-grid">
          {data.attivita.map((attivita, index) => (
            <div key={index} className="rental-card">
              <div className="rental-name">{attivita.nome}</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Tipo</span>
                  <span className="rental-value">{attivita.tipo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Luogo</span>
                  <span className="rental-value">{attivita.luogo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Prezzo per persona</span>
                  <span className="rental-value">€{attivita.prezzo_persona}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo totale</span>
                  <span className="rental-value">€{attivita.costo_totale}</span>
                </div>
              </div>
            </div>
          ))}
          {data.guida && (
            <div className="rental-card">
              <div className="rental-name">Guida Turistica</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Lingua</span>
                  <span className="rental-value">{data.guida.lingua}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo</span>
                  <span className="rental-value">€{data.guida.costo}</span>
                </div>
              </div>
            </div>
          )}
          <div className="rental-card">
            <div className="rental-name">Riepilogo Città d'Arte</div>
            <div className="rental-summary">
              <div className="rental-summary-item">
                Numero attività: {data.attivita.length}
              </div>
              <div className="rental-summary-item">
                Costo totale: €{data.costo_totale}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderNaturalisticoSection = (data) => {
    if (!data || !data.attivita) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Attività Naturalistiche</h2>
        <div className="rental-grid">
          {data.attivita.map((attivita, index) => (
            <div key={index} className="rental-card">
              <div className="rental-name">{attivita.nome}</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Tipo</span>
                  <span className="rental-value">{attivita.tipo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Luogo</span>
                  <span className="rental-value">{attivita.luogo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Prezzo per persona</span>
                  <span className="rental-value">€{attivita.prezzo_persona}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo totale</span>
                  <span className="rental-value">€{attivita.costo_totale}</span>
                </div>
              </div>
            </div>
          ))}
          {data.guida && (
            <div className="rental-card">
              <div className="rental-name">Guida Naturalistica</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Lingua</span>
                  <span className="rental-value">{data.guida.lingua}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo</span>
                  <span className="rental-value">€{data.guida.costo}</span>
                </div>
              </div>
            </div>
          )}
          <div className="rental-card">
            <div className="rental-name">Riepilogo Attività</div>
            <div className="rental-summary">
              <div className="rental-summary-item">
                Numero attività: {data.attivita.length}
              </div>
              <div className="rental-summary-item">
                Costo totale: €{data.costo_totale}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMareSection = (data) => {
    if (!data || !data.attivita) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Attività Mare</h2>
        <div className="rental-grid">
          {data.attivita.map((attivita, index) => (
            <div key={index} className="rental-card">
              <div className="rental-name">{attivita.nome_societa}</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Tipo</span>
                  <span className="rental-value">{attivita.tipo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Luogo</span>
                  <span className="rental-value">{attivita.luogo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Prezzo per persona</span>
                  <span className="rental-value">€{attivita.prezzo_persona}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo totale</span>
                  <span className="rental-value">€{attivita.costo_totale}</span>
                </div>
                {attivita.attrezzatura && (
                  <>
                    <div className="rental-detail">
                      <span className="rental-label">Attrezzatura</span>
                      <span className="rental-value">Inclusa</span>
                    </div>
                    <div className="rental-detail">
                      <span className="rental-label">Costo attrezzatura</span>
                      <span className="rental-value">€{attivita.attrezzatura.costo}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
          <div className="rental-card">
            <div className="rental-name">Riepilogo Attività</div>
            <div className="rental-summary">
              <div className="rental-summary-item">
                Numero attività: {data.attivita.length}
              </div>
              <div className="rental-summary-item">
                Costo totale: €{data.costo_totale}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMontagnaSection = (data) => {
    if (!data || !data.attivita) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Attività Montagna</h2>
        <div className="rental-grid">
          {data.attivita.map((attivita, index) => (
            <div key={index} className="rental-card">
              <div className="rental-name">{attivita.nome_societa}</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Tipo</span>
                  <span className="rental-value">{attivita.tipo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Luogo</span>
                  <span className="rental-value">{attivita.luogo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Prezzo per persona</span>
                  <span className="rental-value">€{attivita.prezzo_persona}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo totale</span>
                  <span className="rental-value">€{attivita.costo_totale}</span>
                </div>
                {attivita.attrezzatura && (
                  <>
                    <div className="rental-detail">
                      <span className="rental-label">Attrezzatura</span>
                      <span className="rental-value">Inclusa</span>
                    </div>
                    <div className="rental-detail">
                      <span className="rental-label">Costo attrezzatura</span>
                      <span className="rental-value">€{attivita.attrezzatura.costo}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}
          <div className="rental-card">
            <div className="rental-name">Riepilogo Attività</div>
            <div className="rental-summary">
              <div className="rental-summary-item">
                Numero attività: {data.attivita.length}
              </div>
              <div className="rental-summary-item">
                Costo totale: €{data.costo_totale}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderAlloggiSection = (data) => {
    if (!data) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Alloggio</h2>
        <div className="accommodation-card">
          <div className="accommodation-name">{data.nome}</div>
          <div className="accommodation-details">
            <div className="accommodation-detail">
              <div className="accommodation-label">Categoria</div>
              <div className="accommodation-value">{data.stelle} stelle</div>
            </div>
            <div className="accommodation-detail">
              <div className="accommodation-label">Tipo</div>
              <div className="accommodation-value">{data.tipo}</div>
            </div>
            <div className="accommodation-detail">
              <div className="accommodation-label">Luogo</div>
              <div className="accommodation-value">{data.luogo}</div>
            </div>
            <div className="accommodation-detail">
              <div className="accommodation-label">Durata</div>
              <div className="accommodation-value">{data.giorni} giorni</div>
            </div>
            <div className="accommodation-detail">
              <div className="accommodation-label">Ospiti</div>
              <div className="accommodation-value">{data.persone} persone</div>
            </div>
            <div className="accommodation-detail">
              <div className="accommodation-label">Costo per notte</div>
              <div className="accommodation-value">€{data.costo_per_notte}</div>
            </div>
          </div>
          <div className="accommodation-cost">
            <div className="accommodation-total">
              Costo Totale: €{data.costo_totale}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderNoleggiSection = (data) => {
    if (!data) return null;
    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Noleggi</h2>
        <div className="rental-grid">
          {data.veicoli.map((veicolo, index) => (
            <div key={index} className="rental-card">
              <div className="rental-name">{veicolo.marca} {veicolo.nome}</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Posti</span>
                  <span className="rental-value">{veicolo.n_posti}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Cambio</span>
                  <span className="rental-value">{veicolo.cambio}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo giornaliero</span>
                  <span className="rental-value">€{veicolo.costo_giornaliero}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo totale</span>
                  <span className="rental-value">€{veicolo.costo_totale}</span>
                </div>
              </div>
            </div>
          ))}
          <div className="rental-card">
            <div className="rental-name">Riepilogo Noleggi</div>
            <div className="rental-summary">
              <div className="rental-summary-item">
                Numero veicoli: {data.numero_veicoli}
              </div>
              <div className="rental-summary-item">
                Posti totali: {data.posti_coperti}
              </div>
              <div className="rental-summary-item">
                Costo totale: €{data.costo_totale}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderGastronomiaSection = (data) => {
    if (!data || !data.attivita) return null;

    return (
      <div className="riepilogo-content">
        <h2 className="section-title">Gastronomia</h2>
        <div className="rental-grid">
          {data.attivita.map((attivita, index) => (
            <div key={index} className={`rental-card ${attivita.tipo === 'corsi_cucina' ? 'corsi-cucina-card' : ''}`}>
              <div className="rental-name">{attivita.nome}</div>
              <div className="rental-details">
                <div className="rental-detail">
                  <span className="rental-label">Tipo</span>
                  <span className="rental-value">{attivita.tipo === 'corsi_cucina' ? 'Corsi di Cucina' : attivita.tipo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Luogo</span>
                  <span className="rental-value">{attivita.luogo}</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Prezzo per persona</span>
                  <span className="rental-value">{attivita.prezzo_persona}€</span>
                </div>
                <div className="rental-detail">
                  <span className="rental-label">Costo totale</span>
                  <span className="rental-value">{attivita.costo_totale}€</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="rental-card">
            <div className="rental-name">Riepilogo Gastronomia</div>
            <div className="rental-summary">
              <div className="rental-summary-item">
                Numero attività: {data.attivita.length}
              </div>
              <div className="rental-summary-item">
                Costo totale: €{data.costo_totale}
              </div>
            </div>
          </div>
      </div>
    );
  };

  if (!riepilogoData) {
    return (
      <div className="riepilogo-container">
        <div className="riepilogo-empty-state">
          <h1>Nessun dato disponibile</h1>
          <p>Torna alla chat per iniziare a pianificare il tuo viaggio</p>
        </div>
      </div>
    );
  }

  return (
    <div className="riepilogo-container">
      <div className="container mx-auto px-4">
        <div className="mb-12">
          <h1 className="riepilogo-title text-center">
            Riepilogo del Viaggio
          </h1>
        </div>
        
        <div className="mt-16">
          {renderRiepilogoCostiSection(riepilogoData.riepilogo_costi)}
          {renderIntroSection(riepilogoData.intro)}
          {renderContattiSection(riepilogoData.contatti)}
          {renderTrasportoSection()}
          {renderGastronomiaSection(riepilogoData.gastronomia)}
          {renderAvventuraSection(riepilogoData.avventura)}
          {renderCittaArteSection(riepilogoData.citta_arte)}
          {renderNaturalisticoSection(riepilogoData.naturalistico)}
          {renderMareSection(riepilogoData.mare)}
          {renderMontagnaSection(riepilogoData.montagna)}
          {renderAlloggiSection(riepilogoData.alloggi)}
          {renderNoleggiSection(riepilogoData.noleggi)}
          {renderRiepilogoCostiSection(riepilogoData.riepilogo_costi)}
        </div>

        <div className="mt-16 mb-8 text-center">
          <button
            onClick={handleBackToChat}
            className="riepilogo-button"
          >
            {keepChatActive ? 'Torna alla Chat' : 'Chiudi Riepilogo'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default Riepilogo; 