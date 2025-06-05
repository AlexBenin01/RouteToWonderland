import { useState, useEffect, useRef, useContext } from 'react'
import axios from 'axios'
import { useNavigate, useLocation } from 'react-router-dom'
import { StatoConversazioneContext } from './statoConversazioneContext'
import './App.css'

const TEMPLATES_LABELS = {
  intro: 'Dati di base',
  contatti: 'Contatti',
  alloggi: 'Alloggi',
  noleggi: 'Noleggi',
  naturalistico: 'Naturalistico',
  avventura: 'Avventura',
  montagna: 'Montagna',
  mare: 'Mare',
  gastronomia: 'Gastronomia',
  citta_arte: 'Città darte',
  benessere: 'Benessere'
}

// Manteniamo solo la frase di apertura per intro
const INTRO_PHRASE = "Che tipo di vacanza sogni? Un'avventura adrenalinica, una fuga rilassante, un viaggio tra sapori o un tuffo nella cultura locale? Raccontami il mood che cerchi!"

// Lista dei template obbligatori
const TEMPLATES_OBBLIGATORI = ['intro', 'contatti', 'trasporto'];

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Funzione per pulire tutti i dati
const clearAllData = () => {
  console.log('=== PULIZIA COMPLETA DEI DATI ===');
  sessionStorage.clear();
  console.log('Dati puliti:', Object.keys(sessionStorage));
};

function App() {
  const navigate = useNavigate();
  const { statoConversazione_context, setStatoConversazione_context } = useContext(StatoConversazioneContext);
  const [chat, setChat] = useState(() => {
    const savedChat = sessionStorage.getItem('chatHistory');
    return savedChat ? JSON.parse(savedChat) : [];
  });
  const [input, setInput] = useState('')
  const [currentTemplate, setCurrentTemplate] = useState(() => {
    const savedTemplate = sessionStorage.getItem('currentTemplate');
    console.log('Template iniziale in App:', savedTemplate || 'intro');
    return savedTemplate || 'intro';
  });
  const [statoConversazione, setStatoConversazione] = useState(() => {
    const savedStato = sessionStorage.getItem('statoConversazione');
    return savedStato ? JSON.parse(savedStato) : {};
  });
  const [exit, setExit] = useState(false)
  const [loading, setLoading] = useState(false)
  const [debugData, setDebugData] = useState(() => {
    const savedDebug = sessionStorage.getItem('debugData');
    return savedDebug ? JSON.parse(savedDebug) : {};
  });
  const chatEndRef = useRef(null)
  const [isTyping, setIsTyping] = useState(false)
  const [showGuidaChoice, setShowGuidaChoice] = useState(false)
  const [stepChoicePending, setStepChoicePending] = useState(false)
  const [chatHistory, setChatHistory] = useState([])
  const location = useLocation();
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });
  const [keepChatActive, setKeepChatActive] = useState(false);

  // Salva la chat solo se c'è almeno un messaggio
  useEffect(() => {
    if (chat.length > 0) {
      sessionStorage.setItem('chatHistory', JSON.stringify(chat));
    }
  }, [chat]);

  // Funzione per aggiornare il template in modo sicuro
  const updateTemplate = (newTemplate) => {
    console.log('Aggiornamento template in App:', newTemplate);
    setCurrentTemplate(newTemplate);
    sessionStorage.setItem('currentTemplate', newTemplate);
  };

  // Salva il template corrente nel sessionStorage
  useEffect(() => {
    console.log('Template corrente in App:', currentTemplate);
    sessionStorage.setItem('currentTemplate', currentTemplate);
  }, [currentTemplate]);

  // Funzione per aggiornare lo stato della conversazione in modo sicuro
  const updateStatoConversazione = (newStato) => {
    console.log('Aggiornamento stato conversazione:', newStato);
    setStatoConversazione(newStato);
    sessionStorage.setItem('statoConversazione', JSON.stringify(newStato));
  };

  // Funzione per aggiornare il debug data in modo sicuro
  const updateDebugData = (newDebug) => {
    console.log('Aggiornamento debug data:', newDebug);
    setDebugData(newDebug);
    sessionStorage.setItem('debugData', JSON.stringify(newDebug));
  };

  // Solo useEffect per l'inizializzazione della chat
  useEffect(() => {
    if (location.state?.chatHistory) {
      setChat(location.state.chatHistory);
      setKeepChatActive(location.state.keepChatActive || false);
      setExit(location.state.keepChatActive ? false : true);
      // Mantieni il template corrente quando si torna dalla pagina riepilogo
      if (location.state.currentTemplate) {
        console.log('Template ricevuto da location state:', location.state.currentTemplate);
        updateTemplate(location.state.currentTemplate);
      }
    } else if (!sessionStorage.getItem('chatHistory')) {
      setChat([
        { sender: 'bot', text: INTRO_PHRASE }
      ]);
      updateTemplate('intro');
    }
  }, [location]);

  // Pulisci il sessionStorage quando si chiude la pagina
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!keepChatActive) {
        sessionStorage.removeItem('chatHistory');
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [keepChatActive]);

  useEffect(() => {
    if (exit) {
      setChatHistory([...chat]);
      setChat([{ sender: 'bot', text: chat[chat.length - 1]?.text || '' }]);
    } else if (chatHistory.length > 0) {
      setChat([...chatHistory]);
      setChatHistory([]);
    }
  }, [exit]);

  useEffect(() => {
    setDebugData(statoConversazione);
    setStatoConversazione_context(statoConversazione);
    updateDebugData(statoConversazione);
  }, [statoConversazione]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chat])

  useEffect(() => {
    console.log('=== MONITORAGGIO STATO CONVERSAZIONE ===');
    console.log('statoConversazione:', statoConversazione);
    console.log('statoConversazione_context:', statoConversazione_context);
    console.log('debugData:', debugData);
  }, [statoConversazione, statoConversazione_context, debugData]);

  // Funzione per mostrare la notifica
  const showNotification = (message, type = 'info') => {
    setNotification({ show: true, message, type });
    setTimeout(() => {
      setNotification({ show: false, message: '', type: '' });
    }, 3000);
  };

  // Gestione della combinazione Ctrl+R
  useEffect(() => {
    const handleKeyDown = async (e) => {
      if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        
        if (!TEMPLATES_OBBLIGATORI.includes(currentTemplate)) {
          try {
            setLoading(true);
            const response = await fetch('http://localhost:8000/get_summary', {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
              },
            });
            
            if (!response.ok) {
              throw new Error('Errore nella risposta del server');
            }
            
            const { data, show_summary } = await response.json();
            console.log("Risultati ricevuti:", { data, show_summary });
            
            if (show_summary) {
              navigate('/riepilogo', { 
                state: { 
                  riepilogoData: data,
                  keepChatActive: true,
                  chatHistory: chat,
                  currentTemplate: currentTemplate // Passa il template corrente
                } 
              });
            }
          } catch (error) {
            console.error('Errore durante il recupero dei risultati:', error);
            showNotification('Errore nel recupero del riepilogo', 'error');
          } finally {
            setLoading(false);
          }
        } else {
          showNotification(
            'ATTENZIONE!\n' +
            'Il riepilogo non è disponibile\n' +
            'durante i template obbligatori', 
            'error'
          );
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [currentTemplate, chat, navigate]);

  const addBotMessage = async (msg) => {
    setIsTyping(true)
    await new Promise(res => setTimeout(res, 700))
    setChat(prev => [...prev, msg])
    setIsTyping(false)
  }

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading || showGuidaChoice || stepChoicePending) return
    
    setChat(prev => [...prev, { sender: 'utente', text: input }])
    setLoading(true)
    
    try {
      const response = await axios.post('http://localhost:8000/extract_simple', {
        text: input
      })
      
      // Controllo per show_summary
      if (response.data?.show_summary === true && response.data?.data) {
        setExit(true);
        navigate('/riepilogo', { 
          state: { 
            riepilogoData: response.data.data,
            keepChatActive: false,
            chatHistory: chat
          } 
        });
        setLoading(false);
        return;
      }
      
      const { guide_phrase, template_usato, nuovo_template, stato_conversazione, next_template, exit } = response.data
      
      console.log('=== ANALISI RISPOSTA ===')
      console.log('Template usato:', template_usato)
      console.log('Next template:', next_template)
      console.log('Stato completo della risposta:', response.data)
      
      // Aggiorna sempre il template con quello usato nella risposta
      if (template_usato) {
        updateTemplate(template_usato);
      }
      
      updateStatoConversazione(stato_conversazione);
      setStatoConversazione_context(stato_conversazione);
      
      if (nuovo_template && next_template) {
        updateTemplate(next_template);
        await addBotMessage({ sender: 'bot', text: guide_phrase });
        setInput('');
        setLoading(false);
        return;
      }
      
      if (guide_phrase) {
        await addBotMessage({ sender: 'bot', text: guide_phrase })
      }
        
      if (!guide_phrase || guide_phrase.trim() === '') {
        if (next_template) {
          updateTemplate(next_template);
        } else {
          await addBotMessage({ sender: 'bot', text: '🎉 Tutte le informazioni sono state raccolte! Grazie per aver usato il nostro servizio.' })
          setTimeout(() => {
            navigate('/riepilogo');
          }, 1000);
        }
      }

      // Gestione dei pulsanti di uscita
      if (exit) {
        console.log('=== GESTIONE EXIT ===')
        console.log('Stato exit prima dell\'aggiornamento:', exit)
        setExit(true)
        console.log('Stato exit dopo setExit(true):', true)
        console.log('Stato completo al momento dell\'exit:', {
          currentTemplate,
          statoConversazione,
          exit: true
        })
        setLoading(false)
        return
      }
    } catch (err) {
      await addBotMessage({ sender: 'bot', text: err.response?.data?.detail || 'Errore nella richiesta' })
    }
    
    setInput('')
    setLoading(false)
  }

  const handleResult = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/get_summary', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Errore nella risposta del server');
      }
      
      const { data, show_summary } = await response.json();
      console.log("Risultati ricevuti:", { data, show_summary });
      
      if (show_summary) {
        navigate('/riepilogo', { 
          state: { 
            riepilogoData: data,
            keepChatActive: true,
            chatHistory: chat,
            currentTemplate: currentTemplate // Passa il template corrente
          } 
        });
      } else {
        console.log('Nessun riepilogo da mostrare');
      }
      
      setLoading(false)
      setExit(false)
    } catch (error) {
      console.error('Errore durante il recupero dei risultati:', error)
      setLoading(false)
    }
  }

  const handleSkipTemplate = async () => {
    try {
      setLoading(true)
      const response = await axios.post('http://localhost:8000/skip_template')
      
      if (response.data?.show_summary === true && response.data?.data) {
        setExit(true);
        navigate('/riepilogo', { 
          state: { 
            riepilogoData: response.data.data,
            keepChatActive: false,
            chatHistory: chat
          } 
        });
        setLoading(false);
        return;
      }
      
      setChat(prev => [...prev, { role: 'assistant', text: response.data.guide_phrase }])
      updateTemplate(response.data.template_usato);
      updateStatoConversazione(response.data.stato_conversazione);
      setStatoConversazione_context(response.data.stato_conversazione);
      setExit(false)
      setLoading(false)
    } catch (error) {
      console.error('Errore durante il salto del template:', error)
      setLoading(false)
    }
  }

  const handleContinue = async () => {
    try {
      console.log('=== INIZIO HANDLE_CONTINUE ===')
      console.log('Stato attuale:', {
        currentTemplate,
        statoConversazione,
        exit
      })
      
      setLoading(true)
      console.log('Chiamata a get_continue...')
      const response = await axios.get('http://localhost:8000/get_continue')
      console.log('Risposta ricevuta:', response.data)
      
      setChat(prev => [...prev, { sender: 'bot', text: response.data.guide_phrase }])
      console.log('Chat aggiornata con nuova domanda')
      
      updateStatoConversazione(response.data.stato_conversazione);
      updateTemplate(response.data.template_usato);
      setStatoConversazione_context(response.data.stato_conversazione);
      console.log('Stato conversazione aggiornato')
      
      setExit(false)
      setLoading(false)
      console.log('=== FINE HANDLE_CONTINUE ===')
    } catch (error) {
      console.error('=== ERRORE IN HANDLE_CONTINUE ===')
      console.error('Dettagli errore:', error)
      console.error('Stato al momento dell\'errore:', {
        currentTemplate,
        statoConversazione,
        exit
      })
      setLoading(false)
    }
  }

  // Aggiungi un useEffect per monitorare i cambiamenti di exit
  useEffect(() => {
    console.log('=== MONITORAGGIO EXIT ===')
    console.log('Nuovo valore di exit:', exit)
    console.log('Tipo di exit:', typeof exit)
    console.log('Stato completo al cambio di exit:', {
      currentTemplate,
      statoConversazione,
      exit
    })
  }, [exit])

  // Aggiungo l'event listener per la chiusura
  useEffect(() => {
    const handleBeforeUnload = () => {
      clearAllData();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      clearAllData(); // Pulisce anche quando il componente viene smontato
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Notifica */}
      {notification.show && (
        <div className={`fixed top-20 left-1/2 transform -translate-x-1/2 p-8 rounded-lg shadow-2xl z-[9999] transition-all duration-300 ${
          notification.type === 'error' ? 'bg-red-600 border-4 border-red-800' : 
          notification.type === 'warning' ? 'bg-yellow-500 border-4 border-yellow-700' : 
          'bg-blue-500 border-4 border-blue-700'
        } text-white text-center whitespace-pre-line backdrop-blur-sm bg-opacity-100`}
        style={{
          position: 'fixed',
          top: '5rem',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 9999,
          pointerEvents: 'none',
          animation: 'float 2s ease-in-out infinite',
          minWidth: '400px',
          fontSize: '1.25rem',
          fontWeight: 'bold',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 0 0 4px rgba(220, 38, 38, 0.5)'
        }}>
          {notification.message}
        </div>
      )}

      <style>
        {`
          @keyframes float {
            0% {
              transform: translateX(-50%);
            }
            50% {
              transform: translateX(-50%) translateY(-5px);
            }
            100% {
              transform: translateX(-50%);
            }
          }
        `}
      </style>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="mb-4">
              <h1 className="text-2xl font-bold text-center text-gray-800">
                Route to Wonderland
              </h1>
            </div>

            <div style={{ maxWidth: 600, margin: '2rem auto', fontFamily: 'sans-serif' }}>
              <h1>Chatbot Agenzia Viaggi</h1>
              <div className="chat-container" style={{
                border: '1px solid #ccc', borderRadius: 8, padding: 16, minHeight: 300, marginBottom: 16, background: '#f9f9f9',
                maxHeight: 400, overflowY: 'auto', display: 'flex', flexDirection: 'column'
              }}>
                {chat.map((msg, idx) => (
                  <div
                    key={idx}
                    style={{
                      textAlign: msg.sender === 'utente' ? 'right' : 'left',
                      margin: '8px 0'
                    }}
                  >
                    {msg.isHtml ? (
                      <span
                        style={{
                          display: 'inline-block',
                          background: msg.sender === 'utente' ? '#d1e7dd' : '#e2e3e5',
                          color: '#222',
                          borderRadius: 16,
                          padding: '8px 16px',
                          maxWidth: '80%',
                          wordBreak: 'break-word'
                        }}
                        dangerouslySetInnerHTML={{ __html: msg.text }}
                      />
                    ) : (
                      <span
                        style={{
                          display: 'inline-block',
                          background: msg.sender === 'utente' ? '#d1e7dd' : '#e2e3e5',
                          color: '#222',
                          borderRadius: 16,
                          padding: '8px 16px',
                          maxWidth: '80%',
                          wordBreak: 'break-word'
                        }}
                      >
                        {msg.text}
                      </span>
                    )}
                  </div>
                ))}
                {exit && (
                  <div className="flex flex-wrap gap-2 justify-center mt-4">
                    <button
                      onClick={handleResult}
                      disabled={loading}
                      className="px-4 py-2 bg-white text-blue-500 border border-blue-300 rounded-lg hover:bg-blue-50 transition-colors disabled:opacity-50 text-sm shadow-sm"
                    >
                      {loading ? 'Caricamento...' : 'Vai al Risultato'}
                    </button>
                    <button
                      onClick={handleSkipTemplate}
                      disabled={loading}
                      className="px-4 py-2 bg-white text-red-500 border border-red-300 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50 text-sm shadow-sm"
                    >
                      {loading ? 'Caricamento...' : 'Salta Argomento'}
                    </button>
                    <button
                      onClick={handleContinue}
                      disabled={loading}
                      className="px-4 py-2 bg-white text-green-500 border border-green-300 rounded-lg hover:bg-green-50 transition-colors disabled:opacity-50 text-sm shadow-sm"
                    >
                      Continua Conversazione
                    </button>
                  </div>
                )}
                <div ref={chatEndRef} />
                {loading && <div style={{ color: '#888' }}>Sto pensando...</div>}
                {isTyping && <div style={{ color: '#888', margin: '8px 0' }}> sto scrivendo...</div>}
              </div>

              <form onSubmit={handleSend} style={{ display: 'flex', gap: 8 }}>
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="Scrivi qui la tua richiesta..."
                  style={{ flex: 1, borderRadius: 8, padding: 8 }}
                  disabled={loading || exit}
                />
                <button 
                  type="submit" 
                  disabled={loading || !input.trim() || exit}
                  style={{ 
                    background: '#4a90e2', 
                    color: '#fff', 
                    borderRadius: 8, 
                    padding: '8px 12px', 
                    border: 'none',
                    cursor: 'pointer'
                  }}
                >
                  Invia
                </button>
              </form>

              {/* DEBUG BOX */}
              <div style={{marginTop: 32, background: '#f4f4f4', borderRadius: 8, padding: 16}}>
                <b>DEBUG - Stato conversazione:</b>
                <pre style={{fontSize: 12, color: '#333'}}>{JSON.stringify(debugData, null, 2)}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
