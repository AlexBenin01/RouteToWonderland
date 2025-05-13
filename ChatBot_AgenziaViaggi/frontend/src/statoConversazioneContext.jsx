import { createContext, useState } from 'react'

export const StatoConversazioneContext = createContext({
  statoConversazione_context: {},
  setStatoConversazione_context: () => {}
})

export const StatoConversazioneProvider = ({ children }) => {
  const [statoConversazione_context, setStatoConversazione_context] = useState({});

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