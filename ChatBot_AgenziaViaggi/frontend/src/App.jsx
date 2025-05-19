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
const INTRO_PHRASE = "Ciao! Sono il tuo assistente di viaggio. Raccontami dove vorresti andare, con chi e quando: sono qui per aiutarti a organizzare tutto al meglio!"

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
  const [loading, setLoading] = useState(false)
  const [luogoCompletato, setLuogoCompletato] = useState(false)
  const [debugData, setDebugData] = useState({})
  const chatEndRef = useRef(null)
  const [isTyping, setIsTyping] = useState(false)
  const [showGuidaChoice, setShowGuidaChoice] = useState(false)
  const [showSaltaAttivita, setShowSaltaAttivita] = useState(false)
  const [showSaltaNoteAggiuntive, setShowSaltaNoteAggiuntive] = useState(false)
  const [stepChoicePending, setStepChoicePending] = useState(false)

  // Solo useEffect per l'inizializzazione della chat
  useEffect(() => {
    setChat([
      { sender: 'bot', text: INTRO_PHRASE }
    ]);
    setCurrentTemplate('intro');
  }, []);

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
      
      const { guide_phrase, template_usato, nuovo_template, stato_conversazione, next_template } = response.data
      
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
    } catch (err) {
      await addBotMessage({ sender: 'bot', text: err.response?.data?.detail || 'Errore nella richiesta' })
    }
    
    setInput('')
    setLoading(false)
  }

  return (
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
          disabled={loading}
        />
        <button 
          type="submit" 
          disabled={loading || !input.trim()}
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
  )
}

export default App
