import { useState, useEffect, useRef, useContext } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
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

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function App() {
  const navigate = useNavigate();
  const { statoConversazione_context, setStatoConversazione_context } = useContext(StatoConversazioneContext);
  const [chat, setChat] = useState([])
  const [input, setInput] = useState('')
  const [currentTemplate, setCurrentTemplate] = useState('intro')
  const [statoConversazione, setStatoConversazione] = useState({})
  const [exit, setExit] = useState(false)
  const [loading, setLoading] = useState(false)
  const [debugData, setDebugData] = useState({})
  const chatEndRef = useRef(null)
  const [isTyping, setIsTyping] = useState(false)
  const [showGuidaChoice, setShowGuidaChoice] = useState(false)
  const [stepChoicePending, setStepChoicePending] = useState(false)
  const [chatHistory, setChatHistory] = useState([])

  // Solo useEffect per l'inizializzazione della chat
  useEffect(() => {
    setChat([
      { sender: 'bot', text: INTRO_PHRASE }
    ]);
    setCurrentTemplate('intro');
  }, []);

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
    setStatoConversazione_context(statoConversazione)
  }, [statoConversazione]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chat])

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
      
      const { guide_phrase, template_usato, nuovo_template, stato_conversazione, next_template, exit } = response.data
      
      console.log('=== ANALISI RISPOSTA ===')
      console.log('Valore exit ricevuto:', exit)
      console.log('Tipo di exit:', typeof exit)
      console.log('Stato completo della risposta:', response.data)
      
      setStatoConversazione(stato_conversazione)
      setStatoConversazione_context(stato_conversazione)
      
      if (nuovo_template && next_template) {
        setCurrentTemplate(next_template);
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
          await axios.post('http://localhost:8000/set_template', {
            template_type: next_template
          })
          setCurrentTemplate(next_template)
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
      // Qui implementeremo la logica per mostrare i risultati
      console.log("Vai al risultato")
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
      setChat(prev => [...prev, { role: 'assistant', text: response.data.guide_phrase }])
      setCurrentTemplate(response.data.template_usato)
      setStatoConversazione(response.data.stato_conversazione)
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
      
      setStatoConversazione(response.data.stato_conversazione)
      setStatoConversazione_context(response.data.stato_conversazione)
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

  return (
    <div className="min-h-screen bg-gray-100">
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
