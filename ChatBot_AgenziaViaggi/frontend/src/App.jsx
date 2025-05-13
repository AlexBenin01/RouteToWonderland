import { useState, useEffect, useRef, useContext } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { StatoConversazioneContext } from './statoConversazioneContext'
import './App.css'

const TEMPLATES_SEQUENCE = ['intro', 'luoghi', 'alloggi', 'noleggi', 'contatti']
const TEMPLATES_LABELS = {
  intro: 'Dati di base',
  luoghi: 'Luoghi',
  alloggi: 'Alloggi',
  noleggi: 'Noleggi',
  contatti: 'Contatti',
}
const OPENING_PHRASES = {
  intro: "Ciao! Sono il tuo assistente di viaggio. Raccontami dove vorresti andare, con chi e quando: sono qui per aiutarti a organizzare tutto al meglio!",
  luoghi: "Parliamo ora delle tappe del tuo viaggio! Hai già in mente qualche luogo o attività che non vuoi perderti?",
  alloggi: "Pensiamo all'alloggio: preferisci un hotel, un appartamento o hai già una struttura in mente?",
  noleggi: "Per gli spostamenti, ti serve un'auto a noleggio? Dimmi pure le tue preferenze!",
  contatti: "Infine, mi lasci il suo nominativo e poi i suoi dati di contatti così posso inviarti la proposta e restare in contatto per ogni esigenza?"
};

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

  useEffect(() => {
    setChat([
      { sender: 'bot', text: OPENING_PHRASES.intro }
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

  useEffect(() => {
    if (currentTemplate === 'alloggi' || currentTemplate === 'noleggi') {
      setStepChoicePending(true);
    } else {
      setStepChoicePending(false);
    }
  }, [currentTemplate]);

  // Utility per aggiungere messaggio bot con effetto typing
  const addBotMessage = async (msg) => {
    setIsTyping(true)
    await new Promise(res => setTimeout(res, 700))
    setChat(prev => [...prev, msg])
    setIsTyping(false)
    // Bottoni Sì/No per richiesta_guida
    if (msg.sender === 'bot' && msg.text && msg.text.toLowerCase().includes('guida turistica')) {
      setShowGuidaChoice(true);
    } else {
      setShowGuidaChoice(false);
    }
    // Tasto "Salta Campo" per attivita_extra
    if (msg.sender === 'bot' && msg.text && msg.text.toLowerCase().includes('attivit') && msg.text.toLowerCase().includes('extra')) {
      setShowSaltaAttivita(true);
    } else {
      setShowSaltaAttivita(false);
    }
    // Tasto "Salta Note Aggiuntive" per note_aggiuntive
    if (msg.sender === 'bot' && msg.text && msg.text.toLowerCase().includes('dettaglio') && msg.text.toLowerCase().includes('extra')) {
      setShowSaltaNoteAggiuntive(true);
    } else {
      setShowSaltaNoteAggiuntive(false);
    }
  }

  // Gestione invio testo utente
  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading || showGuidaChoice || stepChoicePending) return
    let userInput = showSaltaAttivita ? `attività extra: ${input}` : 
                    showSaltaNoteAggiuntive ? `note aggiuntive: ${input}` : 
                    input;
    setChat(prev => [...prev, { sender: 'utente', text: userInput }])
    setLoading(true)
    setLuogoCompletato(false)
    try {
      const response = await axios.post('http://localhost:8000/extract_simple', {
        text: userInput
      })
      const { guide_phrase, template_usato, nuovo_template, stato_conversazione, luogo_completato, next_template } = response.data
      setStatoConversazione(stato_conversazione)
      setStatoConversazione_context(stato_conversazione)
      if (nuovo_template && next_template) {
        setCurrentTemplate(next_template);
        await addBotMessage({ sender: 'bot', text: OPENING_PHRASES[next_template] });
        setInput('');
        setLoading(false);
        return;
      }
      
      if (template_usato === 'luoghi' && luogo_completato) {
        setLuogoCompletato(true)
        await addBotMessage({ sender: 'bot',text: guide_phrase || '✅ Luogo aggiunto! Vuoi aggiungere un altro luogo?', isHtml: false, luogoChoice: true })
      }else if(guide_phrase) {
        await addBotMessage({ sender: 'bot', text: guide_phrase })
      }
        
      if ((!guide_phrase || guide_phrase.trim() === '') && template_usato !== 'luoghi') {
        const idx = TEMPLATES_SEQUENCE.indexOf(template_usato)
        const nextTemplate = TEMPLATES_SEQUENCE[idx + 1]
        if (nextTemplate) {
          await axios.post('http://localhost:8000/set_template', {
            template_type: nextTemplate
          })
          setCurrentTemplate(nextTemplate)
          await addBotMessage({ sender: 'bot', text: OPENING_PHRASES[nextTemplate] })
        } else {
          await addBotMessage({ sender: 'bot', text: '🎉 Tutte le informazioni sono state raccolte! Grazie per aver usato il nostro servizio.' })
          // Naviga al riepilogo dopo 1 secondo
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

  // Gestione scelta Sì/No per richiesta_guida
  const handleGuidaChoice = async (val) => {
    setShowGuidaChoice(false);
    setChat(prev => [...prev, { sender: 'bot', text: val ? 'Sì' : 'No' }]);
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/extract_simple', {
        text: val ? 'sì' : 'no',
        campo: 'richiesta_guida',
        ...(val === false ? { lingua_guida: "" } : {})
      });
      const { guide_phrase, template_usato, nuovo_template, stato_conversazione, luogo_completato } = response.data;
      setStatoConversazione(stato_conversazione);
      setStatoConversazione_context(stato_conversazione);
      if (template_usato === 'luoghi' && luogo_completato) {
        setLuogoCompletato(true);
        await addBotMessage({ sender: 'bot',text: guide_phrase || '✅ Luogo aggiunto! Vuoi aggiungere un altro luogo?', isHtml: false, luogoChoice: true });
      }else if(guide_phrase){
        await addBotMessage({ sender: 'bot', text: guide_phrase });
      }
      if ((!guide_phrase || guide_phrase.trim() === '') && template_usato !== 'luoghi') {
        const idx = TEMPLATES_SEQUENCE.indexOf(template_usato);
        const nextTemplate = TEMPLATES_SEQUENCE[idx + 1];
        if (nextTemplate) {
          await axios.post('http://localhost:8000/set_template', {
            template_type: nextTemplate
          });
          setCurrentTemplate(nextTemplate);
          await addBotMessage({ sender: 'bot', text: OPENING_PHRASES[nextTemplate] });
        } else {
          await addBotMessage({ sender: 'bot', text: '🎉 Tutte le informazioni sono state raccolte! Grazie per aver usato il nostro servizio.' });
          // Naviga al riepilogo dopo 1 secondo
          setTimeout(() => {
            navigate('/riepilogo');
          }, 1000);
        }
      }
    } catch (err) {
      await addBotMessage({ sender: 'bot', text: err.response?.data?.detail || 'Errore nella richiesta' });
    }
    setLoading(false);
  }

  // Gestione scelta Salta Campo per attivita_extra
  const handleSaltaAttivita = async () => {
    setShowSaltaAttivita(false);
    setChat(prev => [...prev, { sender: 'bot', text: 'Salta Campo' }]);
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/extract_simple', {
        text: 'nessuna',
        campo: 'attivita_extra'
      });
      const { guide_phrase, template_usato, nuovo_template, stato_conversazione, luogo_completato } = response.data;
      setStatoConversazione(stato_conversazione);
      setStatoConversazione_context(stato_conversazione);
      if (template_usato === 'luoghi' && luogo_completato) {
        setLuogoCompletato(true);
        await addBotMessage({ sender: 'bot', text: guide_phrase || '✅ Luogo aggiunto! Vuoi aggiungere un altro luogo?', isHtml: false, luogoChoice: true });
      }else if(guide_phrase){
        await addBotMessage({ sender: 'bot', text: guide_phrase });
      }
      if ((!guide_phrase || guide_phrase.trim() === '') && template_usato !== 'luoghi') {
        const idx = TEMPLATES_SEQUENCE.indexOf(template_usato);
        const nextTemplate = TEMPLATES_SEQUENCE[idx + 1];
        if (nextTemplate) {
          await axios.post('http://localhost:8000/set_template', {
            template_type: nextTemplate
          });
          setCurrentTemplate(nextTemplate);
          await addBotMessage({ sender: 'bot', text: OPENING_PHRASES[nextTemplate] });
        } else {
          await addBotMessage({ sender: 'bot', text: '🎉 Tutte le informazioni sono state raccolte! Grazie per aver usato il nostro servizio.' });
        }
      }
    } catch (err) {
      await addBotMessage({ sender: 'bot', text: err.response?.data?.detail || 'Errore nella richiesta' });
    }
    setLoading(false);
  }

  // Gestione scelta Sì/No per aggiungere un altro luogo
  const handleLuogoChoice = async (addAnother) => {
    setLuogoCompletato(false)
    if (addAnother) {
      // Mostra la frase guida per il nuovo luogo (il backend gestisce lo stato)
      await addBotMessage({ sender: 'bot', text: OPENING_PHRASES.luoghi })
    } else {
      // Passa al prossimo template
      const idx = TEMPLATES_SEQUENCE.indexOf(currentTemplate)
      const nextTemplate = TEMPLATES_SEQUENCE[idx + 1]
      if (nextTemplate) {
        try {
          await axios.post('http://localhost:8000/set_template', {
            template_type: nextTemplate
          })
          setCurrentTemplate(nextTemplate)
          await addBotMessage({ sender: 'bot', text: OPENING_PHRASES[nextTemplate] })
        } catch (err) {
          await addBotMessage({ sender: 'bot', text: 'Errore nel cambio template' })
        }
      } else {
        await addBotMessage({ sender: 'bot', text: '🎉 Tutte le informazioni sono state raccolte! Grazie per aver usato il nostro servizio.' })
        // Naviga al riepilogo dopo 1 secondo
        setTimeout(() => {
          navigate('/riepilogo');
        }, 1000);
      }
    }
  }

  const handleSaltaAlloggi = async () => {
    setStepChoicePending(false);
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/extract_simple', {
        text: 'salta_step_alloggi'
      });
      setStatoConversazione(response.data.stato_conversazione);
      setStatoConversazione_context(response.data.stato_conversazione);
      if (response.data.guide_phrase) {
        await addBotMessage({ sender: 'bot', text: response.data.guide_phrase });
      }
      if (response.data.nuovo_template && response.data.next_template) {
        await axios.post('http://localhost:8000/set_template', {
          template_type: response.data.next_template
        });
        setCurrentTemplate(response.data.next_template);
        await addBotMessage({ sender: 'bot', text: OPENING_PHRASES[response.data.next_template] });
      }
    } catch (err) {
      await addBotMessage({ sender: 'bot', text: err.response?.data?.detail || 'Errore nella richiesta' });
    }
    setLoading(false);
  };

  const handleConfermaAlloggi = () => {
    setStepChoicePending(false);
    // Ora l'utente può compilare i dati alloggi normalmente
  };

  const handleSaltaNoleggi = async () => {
    setStepChoicePending(false);
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/extract_simple', {
        text: 'salta_step_noleggi'
      });
      setStatoConversazione(response.data.stato_conversazione);
      setStatoConversazione_context(response.data.stato_conversazione);
      if (response.data.guide_phrase) {
        await addBotMessage({ sender: 'bot', text: response.data.guide_phrase });
      }
      if (response.data.nuovo_template && response.data.next_template) {
        await axios.post('http://localhost:8000/set_template', {
          template_type: response.data.next_template
        });
        setCurrentTemplate(response.data.next_template);
        await addBotMessage({ sender: 'bot', text: OPENING_PHRASES[response.data.next_template] });
      }
    } catch (err) {
      await addBotMessage({ sender: 'bot', text: err.response?.data?.detail || 'Errore nella richiesta' });
    }
    setLoading(false);
  };

  const handleConfermaNoleggi = () => {
    setStepChoicePending(false);
    // Ora l'utente può compilare i dati noleggi normalmente
  };

  // Gestione scelta Salta Campo per note_aggiuntive
  const handleSaltaNoteAggiuntive = async () => {
    setShowSaltaNoteAggiuntive(false);
    setChat(prev => [...prev, { sender: 'bot', text: 'Salta Campo' }]);
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/extract_simple', {
        text: 'nessuna',
        campo: 'note_aggiuntive'
      });
      setStatoConversazione(response.data.stato_conversazione);
      setStatoConversazione_context(response.data.stato_conversazione);
      if (response.data.guide_phrase) {
        await addBotMessage({ sender: 'bot', text: response.data.guide_phrase });
      } else {
        // Logica di chiusura conversazione come in handleSend
        const idx = TEMPLATES_SEQUENCE.indexOf(response.data.template_usato);
        const nextTemplate = TEMPLATES_SEQUENCE[idx + 1];
        if (!nextTemplate) {
          await addBotMessage({ sender: 'bot', text: '🎉 Tutte le informazioni sono state raccolte! Grazie per aver usato il nostro servizio.' });
          // Naviga al riepilogo dopo 1 secondo
          setTimeout(() => {
            navigate('/riepilogo');
          }, 1000);
        }
      }
    } catch (err) {
      await addBotMessage({ sender: 'bot', text: err.response?.data?.detail || 'Errore nella richiesta' });
    }
    setLoading(false);
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
            {/* Pulsanti Sì/No per aggiungere un altro luogo */}
            {msg.luogoChoice && luogoCompletato && (
              <div style={{ marginTop: 8 }}>
                <button onClick={() => handleLuogoChoice(true)} style={{ marginRight: 8 }}>Sì</button>
                <button onClick={() => handleLuogoChoice(false)}>No</button>
              </div>
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
          disabled={loading || luogoCompletato || showGuidaChoice || stepChoicePending}
        />
        <button 
          type="submit" 
          disabled={loading || !input.trim() || luogoCompletato || showGuidaChoice || stepChoicePending}
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
        {/* Tasto Salta Campo per attivita_extra */}
        {showSaltaAttivita && (
          <button type="button" onClick={handleSaltaAttivita} style={{ marginLeft: 8, background: '#f7c873', color: '#222', borderRadius: 8, padding: '8px 12px', border: 'none' }}>
            Salta Campo
          </button>
        )}
        {/* Tasto Salta Campo per note_aggiuntive */}
        {showSaltaNoteAggiuntive && (
          <button type="button" onClick={handleSaltaNoteAggiuntive} style={{ marginLeft: 8, background: '#f7c873', color: '#222', borderRadius: 8, padding: '8px 12px', border: 'none' }}>
            Salta Campo
          </button>
        )}
        {/* Bottoni Conferma/Salta Step per Alloggi */}
        {stepChoicePending && currentTemplate === 'alloggi' && (
          <>
            <button type="button" onClick={handleSaltaAlloggi} style={{ marginLeft: 8, background: '#f7c873', color: '#222', borderRadius: 8, padding: '8px 12px', border: 'none' }}>
              Salta Step
            </button>
            <button type="button" onClick={handleConfermaAlloggi} style={{ marginLeft: 8, background: '#90ee90', color: '#222', borderRadius: 8, padding: '8px 12px', border: 'none' }}>
              Conferma
            </button>
          </>
        )}
        {/* Bottoni Conferma/Salta Step per Noleggi */}
        {stepChoicePending && currentTemplate === 'noleggi' && (
          <>
            <button type="button" onClick={handleSaltaNoleggi} style={{ marginLeft: 8, background: '#f7c873', color: '#222', borderRadius: 8, padding: '8px 12px', border: 'none' }}>
              Salta Step
            </button>
            <button type="button" onClick={handleConfermaNoleggi} style={{ marginLeft: 8, background: '#90ee90', color: '#222', borderRadius: 8, padding: '8px 12px', border: 'none' }}>
              Conferma
            </button>
          </>
        )}
      </form>
      {/* Bottoni Sì/No per richiesta_guida */}
      {showGuidaChoice && (
        <div style={{ margin: '16px 0', textAlign: 'center' }}>
          <button onClick={() => handleGuidaChoice(true)} style={{ marginRight: 12 }}>Sì</button>
          <button onClick={() => handleGuidaChoice(false)}>No</button>
        </div>
      )}
      {/* DEBUG BOX */}
      <div style={{marginTop: 32, background: '#f4f4f4', borderRadius: 8, padding: 16}}>
        <b>DEBUG - Stato conversazione:</b>
        <pre style={{fontSize: 12, color: '#333'}}>{JSON.stringify(debugData, null, 2)}</pre>
      </div>
    </div>
  )
}

export default App
