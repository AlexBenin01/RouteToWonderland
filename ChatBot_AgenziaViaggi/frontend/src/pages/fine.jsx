import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import '../styles/Fine.css';

function Fine() {
  const navigate = useNavigate();

  useEffect(() => {
    // Pulisci tutta la sessionStorage quando il componente viene montato
    sessionStorage.clear();
  }, []);

  const handleTornaHome = () => {
    navigate('/', { replace: true });
  };

  return (
    <div className="fine-container">
      <div className="fine-content">
        <h1 className="fine-title">Grazie per aver scelto RouteToWonderland!</h1>
        <p className="fine-message">
          Il tuo ordine è stato completato con successo. Riceverai presto una email con tutti i dettagli del tuo viaggio.
        </p>
        <p className="fine-message">
          Speriamo che il tuo viaggio sia indimenticabile!
        </p>
        <button
          onClick={handleTornaHome}
          className="fine-button"
        >
          Torna alla Home
        </button>
      </div>
    </div>
  );
}

export default Fine; 