import { useContext, useState } from 'react';
import { StatoConversazioneContext } from './statoConversazioneContext';
import { Link } from 'react-router-dom';

// Funzione ricorsiva per visualizzare oggetti/array in modo leggibile
function renderValue(key, value, handleChange, path = [], editData = {}, maxPartecipanti = 0) {
  // Funzione helper per convertire una data nel fuso orario italiano
  const toItalianTimezone = (date) => {
    if (!date) return '';
    const d = new Date(date);
    // Aggiungi l'offset del fuso orario italiano (+1 o +2 a seconda dell'ora legale)
    const offset = d.getTimezoneOffset();
    d.setMinutes(d.getMinutes() - offset);
    return d.toISOString().slice(0, 16);
  };

  // Funzione helper per convertire una data dal fuso orario italiano
  const fromItalianTimezone = (dateString) => {
    if (!dateString) return '';
    const d = new Date(dateString);
    // Rimuovi l'offset del fuso orario italiano
    const offset = d.getTimezoneOffset();
    d.setMinutes(d.getMinutes() + offset);
    return d.toISOString().slice(0, 16);
  };

  // Funzione helper per aggiungere giorni a una data
  const addDays = (date, days) => {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result.toISOString().split('T')[0];
  };

  // Funzione helper per ottenere la data minima per data_partenza (domani)
  const getMinPartenza = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  // Funzione helper per ottenere la data minima per data_ritorno (data_partenza + 1 giorno)
  const getMinRitorno = () => {
    if (!editData.data_partenza) return getMinPartenza();
    return addDays(editData.data_partenza, 1);
  };

  // Funzione helper per ottenere i vincoli per orario_visita
  const getOrarioVisitaConstraints = () => {
    if (!editData.data_partenza || !editData.data_ritorno) {
      return { min: '', max: '' };
    }

    // Converti le date nel formato corretto per datetime-local (YYYY-MM-DDThh:mm)
    const minDate = new Date(editData.data_partenza);
    minDate.setHours(0, 0, 0, 0);
    const maxDate = new Date(editData.data_ritorno);
    maxDate.setHours(23, 59, 0, 0);

    // Applica il fuso orario italiano
    const min = toItalianTimezone(minDate);
    const max = toItalianTimezone(maxDate);

    return { min, max };
  };

  // Gestione speciale per numero_partecipanti
  if (key === 'numero_partecipanti') {
    const currentValue = value ? parseInt(value) : 0;
    
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <input
          type="number"
          value={value ?? ''}
          min="1"
          onChange={e => {
            const newValue = parseInt(e.target.value) || 0;
            handleChange(path, newValue);
          }}
          className="riepilogo-input"
          aria-label={key}
          style={{ width: '100px' }}
        />
        <span style={{ color: '#666', fontSize: '0.9em' }}>
          (min: 1)
        </span>
      </div>
    );
  }

  // Gestione speciale per budget_viaggio
  if (key === 'budget_viaggio') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <input
          type="number"
          value={value ?? ''}
          min="0"
          step="100"
          onChange={e => handleChange(path, parseInt(e.target.value) || 0)}
          className="riepilogo-input"
          aria-label={key}
          style={{ width: '150px' }}
        />
        <span style={{ color: '#666', fontSize: '0.9em' }}>
          €
        </span>
      </div>
    );
  }

  // Gestione speciale per budget_auto
  if (key === 'budget_auto') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <input
          type="number"
          value={value ?? ''}
          min="0"
          step="50"
          onChange={e => handleChange(path, parseInt(e.target.value) || 0)}
          className="riepilogo-input"
          aria-label={key}
          style={{ width: '150px' }}
        />
        <span style={{ color: '#666', fontSize: '0.9em' }}>
          €
        </span>
      </div>
    );
  }

  // Gestione speciale per richiesta_guida
  if (key === 'richiesta_guida') {
    return (
      <select
        className="riepilogo-input"
        aria-label="Richiesta guida"
        value={value === true || value === 'Sì' || value === 'si' ? 'Sì' : 'No'}
        onChange={e => handleChange(path, e.target.value === 'Sì' ? 'Sì' : 'No')}
      >
        <option value="Sì">Sì</option>
        <option value="No">No</option>
      </select>
    );
  }

  // Gestione speciale per partecipanti_visita
  if (key === 'partecipanti_visita') {
    console.log('Prima di partecipanti_visita - valore di maxPartecipanti:', maxPartecipanti);
    
    const currentValue = value ? parseInt(value) : 0;
    
    const result = (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <input
          type="number"
          value={value ?? ''}
          min="1"
          max={maxPartecipanti || 1}
          onChange={e => {
            const newValue = parseInt(e.target.value) || 0;
            if (newValue <= maxPartecipanti) {
              handleChange(path, newValue);
            }
          }}
          className="riepilogo-input"
          aria-label={key}
          style={{ width: '100px' }}
        />
        <span style={{ color: '#666', fontSize: '0.9em' }}>
          {maxPartecipanti > 0 ? `(max: ${maxPartecipanti})` : '(imposta prima il numero di partecipanti)'}
        </span>
      </div>
    );

    console.log('Dopo di partecipanti_visita - valore di maxPartecipanti:', maxPartecipanti);
    return result;
  }

  // Gestione speciale per data_partenza
  if (key === 'data_partenza') {
    const formattedDate = value ? new Date(value).toISOString().split('T')[0] : '';
    return (
      <input
        type="date"
        value={formattedDate}
        min={getMinPartenza()}
        onChange={e => handleChange(path, e.target.value)}
        className="riepilogo-input"
        aria-label={key}
      />
    );
  }

  // Gestione speciale per data_ritorno
  if (key === 'data_ritorno') {
    const formattedDate = value ? new Date(value).toISOString().split('T')[0] : '';
    return (
      <input
        type="date"
        value={formattedDate}
        min={getMinRitorno()}
        onChange={e => handleChange(path, e.target.value)}
        className="riepilogo-input"
        aria-label={key}
      />
    );
  }

  // Gestione speciale per orario_visita
  if (key === 'orario_visita') {
    const formattedDateTime = value ? toItalianTimezone(value) : '';
    const { min, max } = getOrarioVisitaConstraints();
    
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <input
          type="datetime-local"
          value={formattedDateTime}
          min={min}
          max={max}
          onChange={e => {
            const newValue = e.target.value;
            if (newValue >= min && newValue <= max) {
              handleChange(path, fromItalianTimezone(newValue));
            }
          }}
          className="riepilogo-input"
          aria-label={key}
        />
        {min && max && (
          <span style={{ color: '#666', fontSize: '0.9em' }}>
            Periodo consentito: dal {min.split('T')[0]} al {max.split('T')[0]}
          </span>
        )}
      </div>
    );
  }

  // Gestione speciale per altri campi data
  if (key.toLowerCase().includes('data') && typeof value === 'string') {
    const formattedDate = value ? new Date(value).toISOString().split('T')[0] : '';
    return (
      <input
        type="date"
        value={formattedDate}
        onChange={e => handleChange(path, e.target.value)}
        className="riepilogo-input"
        aria-label={key}
      />
    );
  }

  // Gestione speciale per lingua_guida
  if (key === 'lingua_guida') {
    const richiestaGuida = editData.richiesta_guida;
    const isDisabled = richiestaGuida === 'No' || richiestaGuida === false || richiestaGuida === 'no';
    return (
      <input
        type="text"
        value={value ?? ''}
        onChange={e => handleChange(path, e.target.value)}
        className="riepilogo-input"
        aria-label="Lingua guida"
        disabled={isDisabled}
        style={isDisabled ? { background: '#eee', color: '#aaa' } : {}}
      />
    );
  }
  if (typeof value === 'object' && value !== null) {
    if (Array.isArray(value)) {
      // Ordinamento per luoghi: se key è 'luoghi' e ogni item ha orario_visita
      let arrayToRender = value;
      if (key === 'luoghi' && value.length > 0 && value[0] && value[0].orario_visita !== undefined) {
        arrayToRender = [...value].sort((a, b) => {
          // Confronto orari come stringa (es: '09:00', '14:30')
          if (!a.orario_visita) return 1;
          if (!b.orario_visita) return -1;
          return a.orario_visita.localeCompare(b.orario_visita);
        });
      }
      return (
        <table className="riepilogo-table riepilogo-table-nested">
          <caption className="sr-only">Array {key}</caption>
          <tbody>
            {arrayToRender.map((item, idx) => (
              <tr key={idx}>
                <th scope="row" className="riepilogo-th-nested">{idx + 1}</th>
                <td>
                  {renderValue(`${key}[${idx}]`, item, handleChange, [...path, idx], editData, maxPartecipanti)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    } else {
      return (
        <table className="riepilogo-table riepilogo-table-nested">
          <caption className="sr-only">Oggetto {key}</caption>
          <tbody>
            {Object.entries(value).map(([k, v]) => (
              <tr key={k}>
                <th scope="row" className="riepilogo-th-nested">{k}</th>
                <td>
                  {renderValue(k, v, handleChange, [...path, k], value, maxPartecipanti)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
  } else {
    // Valore semplice: input modificabile
    return (
      <input
        type="text"
        value={value ?? ''}
        onChange={e => handleChange(path, e.target.value)}
        className="riepilogo-input"
        aria-label={key}
      />
    );
  }
}

export default function Riepilogo() {
  const { statoConversazione_context, setStatoConversazione_context } = useContext(StatoConversazioneContext);
  console.log('Riepilogo - statoConversazione_context ricevuto:', statoConversazione_context);
  console.log('Riepilogo - statoConversazione_context type:', typeof statoConversazione_context);
  console.log('Riepilogo - statoConversazione_context keys:', Object.keys(statoConversazione_context));
  
  const [editData, setEditData] = useState(statoConversazione_context || {});
  const initialMaxPartecipanti = statoConversazione_context?.intro?.numero_partecipanti ? parseInt(statoConversazione_context.intro.numero_partecipanti) : 0;
  const [maxPartecipanti, setMaxPartecipanti] = useState(initialMaxPartecipanti);

  // Funzione per validare e aggiornare orario_visita quando cambiano le date
  const validateAndUpdateOrarioVisita = (newData) => {
    const { data_partenza, data_ritorno, orario_visita } = newData;
    
    if (!data_partenza || !data_ritorno || !orario_visita) {
      return newData;
    }

    const minDate = new Date(data_partenza);
    minDate.setHours(0, 0, 0, 0);
    const maxDate = new Date(data_ritorno);
    maxDate.setHours(23, 59, 0, 0);
    const visitaDate = new Date(orario_visita);

    // Se l'orario_visita è fuori dal range, lo imposta al primo giorno disponibile
    if (visitaDate < minDate || visitaDate > maxDate) {
      return {
        ...newData,
        orario_visita: data_partenza + 'T09:00' // Imposta a 9:00 del giorno di partenza
      };
    }

    return newData;
  };

  // Gestione modifica campo ricorsiva
  const handleChange = (path, value) => {
    // Se stiamo modificando numero_partecipanti, aggiorniamo maxPartecipanti
    if (path[path.length - 1] === 'numero_partecipanti' && path[0] === 'intro') {
      const newMax = parseInt(value) || 0;
      setMaxPartecipanti(newMax);
    }

    setEditData(prev => {
      const newData = { ...prev };
      let obj = newData;
      for (let i = 0; i < path.length - 1; i++) {
        if (typeof obj[path[i]] === 'object' && obj[path[i]] !== null) {
          obj[path[i]] = Array.isArray(obj[path[i]]) ? [...obj[path[i]]] : { ...obj[path[i]] };
        }
        obj = obj[path[i]];
      }
      obj[path[path.length - 1]] = value;

      // Se stiamo modificando data_partenza o data_ritorno, validiamo orario_visita
      if (path[path.length - 1] === 'data_partenza' || path[path.length - 1] === 'data_ritorno') {
        return validateAndUpdateOrarioVisita(newData);
      }

      return newData;
    });
  };

  // Salva modifiche nello stato globale
  const handleSave = () => {
    console.log('Riepilogo - Salvo modifiche:', editData);
    setStatoConversazione_context(editData);
  };

  if (!statoConversazione_context || Object.keys(statoConversazione_context).length === 0) {
    console.log('Riepilogo - Nessun dato disponibile nel contesto');
    return <div>Nessun dato di conversazione disponibile.</div>;
  }

  return (
    <div style={{ maxWidth: 700, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h2 style={{ textAlign: 'center', marginBottom: 24 }}>Riepilogo Stato Conversazione</h2>
      <div style={{ overflowX: 'auto' }}>
        <table className="riepilogo-table" role="table" aria-label="Riepilogo stato conversazione">
          <caption className="sr-only">Riepilogo stato conversazione</caption>
          <thead>
            <tr>
              <th scope="col">Campo</th>
              <th scope="col">Valore</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(editData).map(([key, value]) => (
              <tr key={key}>
                <th scope="row">{key}</th>
                <td>{renderValue(key, value, handleChange, [key], editData, maxPartecipanti)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ marginTop: 24, display: 'flex', gap: 16, justifyContent: 'center' }}>
        <button onClick={handleSave} className="riepilogo-btn riepilogo-btn-save">
          Salva Modifiche
        </button>
        <Link to="/" className="riepilogo-btn riepilogo-btn-link">
          Torna alla chat
        </Link>
      </div>
      <style>{`
        .riepilogo-table {
          width: 100%;
          border-collapse: collapse;
          background: #fff;
          box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .riepilogo-table th, .riepilogo-table td {
          border: 1px solid #d0d7de;
          padding: 10px 14px;
          text-align: left;
          font-size: 1rem;
        }
        .riepilogo-table th {
          background: #f4f8fb;
          color: #1a3a5e;
        }
        .riepilogo-table-nested {
          margin-top: 4px;
          margin-bottom: 4px;
          background: #f9fafb;
        }
        .riepilogo-th-nested {
          background: #e3f0ff;
          color: #1a3a5e;
          font-weight: 500;
          min-width: 90px;
        }
        .riepilogo-input {
          width: 100%;
          padding: 6px 8px;
          border: 1.5px solid #b6dbff;
          border-radius: 6px;
          font-size: 1rem;
          background: #f8fbff;
          color: #222;
          transition: border 0.2s;
        }
        .riepilogo-input:focus {
          outline: 2px solid #1a3a5e;
          border-color: #1a3a5e;
          background: #e3f0ff;
        }
        .riepilogo-btn {
          padding: 10px 22px;
          border-radius: 8px;
          font-size: 1rem;
          border: none;
          cursor: pointer;
          transition: background 0.2s, color 0.2s;
        }
        .riepilogo-btn-save {
          background: #90ee90;
          color: #1a3a5e;
        }
        .riepilogo-btn-save:hover, .riepilogo-btn-save:focus {
          background: #6fdc6f;
        }
        .riepilogo-btn-link {
          background: #e3f0ff;
          color: #1a3a5e;
          text-decoration: none;
        }
        .riepilogo-btn-link:hover, .riepilogo-btn-link:focus {
          background: #b6dbff;
        }
        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0,0,0,0);
          border: 0;
        }
        @media (max-width: 600px) {
          .riepilogo-table th, .riepilogo-table td {
            font-size: 0.95rem;
            padding: 7px 6px;
          }
        }
      `}</style>
    </div>
  );
}
