import { useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';

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
    navigate('/', { 
      state: { 
        chatHistory: chatHistory,
        keepChatActive: keepChatActive,
        currentTemplate: currentTemplate
      }
    });
  };

  // Modifico l'useEffect per la pulizia dei dati
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!keepChatActive) {
        clearAllData();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      if (!keepChatActive) {
        clearAllData();
      }
    };
  }, [keepChatActive]);

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

  if (!riepilogoData) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">Nessun dato disponibile</h1>
          <p className="text-gray-600">Non ci sono dati da visualizzare nel riepilogo.</p>
          <button
            onClick={handleBackToChat}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Torna alla Chat
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">
            Riepilogo del Viaggio
          </h1>
          <button
            onClick={handleBackToChat}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            {keepChatActive ? 'Torna alla Chat' : 'Chiudi Riepilogo'}
          </button>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Categoria
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dettagli
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(riepilogoData).map(([category, details]) => (
                  <tr key={category} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {category}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {renderValue(details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Riepilogo; 