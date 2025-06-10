import { createContext, useState, useEffect } from 'react'

export const StatoConversazioneContext = createContext({
  statoConversazione_context: {},
  setStatoConversazione_context: () => {}
})

export const StatoConversazioneProvider = ({ children }) => {
  const [statoConversazione_context, setStatoConversazione_context] = useState(() => {
    // Resetta lo stato all'avvio dell'applicazione
    console.log('StatoConversazioneProvider - Reset stato iniziale');
    return {};
  });

  // Resetta lo stato quando il sessionStorage viene pulito
  useEffect(() => {
    const handleStorageChange = () => {
      if (!sessionStorage.getItem('chatHistory')) {
        console.log('StatoConversazioneProvider - Reset stato per pulizia sessionStorage');
        setStatoConversazione_context({});
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  console.log('StatoConversazioneProvider - Stato attuale:', statoConversazione_context);

  return (
    <StatoConversazioneContext.Provider value={{
      statoConversazione_context,
      setStatoConversazione_context
    }}>
      {children}
    </StatoConversazioneContext.Provider>
  );
}; 