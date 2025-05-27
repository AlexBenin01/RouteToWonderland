"""
Libreria per la gestione del template master e il caricamento dei dati nei template specifici
"""

from typing import Dict, Any, Optional, Tuple
import logging
from .utils import extract_entities
import json
import os

logger = logging.getLogger(__name__)

class MasterTemplateManager:
    def __init__(self):
        try:
            
            
            # Percorso del file template master
            template_path = os.path.join(os.path.dirname(__file__), '..', 'template', 'master_template.json')
            logger.info(f"Caricamento template master da: {template_path}")
            
            # Carica il template master dal file JSON
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template_master = json.load(f)
                logger.info("Template master caricato con successo")
                
            # Inizializza tutti i valori a None
            for key in self.template_master.keys():
                self.template_master[key] = None
                
            logger.info("Template master inizializzato con valori None")
            
        except Exception as e:
            logger.error(f"Errore durante il caricamento del template master: {str(e)}")
            self.template_master = {}
    
    def load_master_template(self, template_master: Dict[str, Any]):
        """
        Carica il template master
        
        Args:
            template_master: Dizionario contenente il template master
        """
        self.template_master = template_master
        logger.info("Template master caricato")
    
    def process_extraction(self, text: str) -> Tuple[Dict[str, Any], bool]:
        """
        Elabora il testo e aggiorna il template master con le nuove informazioni.
        Aggiorna anche i campi già valorizzati se il nuovo valore è valido.
        
        Args:
            text: Il testo da cui estrarre le informazioni
            
        Returns:
            Tuple[Dict[str, Any], bool]: Il template master aggiornato e un flag che indica se sono state trovate nuove informazioni
        """
        try:
            
            #os.system('cls' if os.name == 'nt' else 'clear')
            
            logger.info(f"Testo ricevuto: {text}")
            logger.info(f"Template master attuale: {self.template_master}")
            
            self.model_path = './NuExtract-2-2B-experimental'  # Percorso del modello NuExtract
            logger.info(f"Percorso modello: {self.model_path}")
            
            # Crea un template vuoto con la stessa struttura del template master
            empty_template = {key: None for key in self.template_master.keys()}
            logger.info(f"Template vuoto creato: {empty_template}")
            
            # Converti il template vuoto in JSON
            template_json = json.dumps(empty_template, ensure_ascii=False)
            logger.info(f"Template JSON: {template_json}")
            
            # Ottieni i dati estratti
            logger.info("Chiamata a extract_entities...")
            result = extract_entities(
                text=text,
                template=template_json,
                model_path=self.model_path
            )
            
            logger.info(f"Tipo di risultato: {type(result)}")
            logger.info(f"Risultato estratto: {result}")
            
            # Converti la risposta in JSON
            try:
                logger.info("Tentativo di parsing JSON...")
                extracted_data = json.loads(result)
                logger.info(f"Tipo di dati estratti: {type(extracted_data)}")
                logger.info(f"Dati estratti: {extracted_data}")
            except json.JSONDecodeError as e:
                logger.error(f"Errore nel parsing della risposta JSON: {str(e)}")
                logger.error(f"Risposta non valida: {result}")
                return self.template_master, False
            
            # Aggiorna il template master con i nuovi dati
            template_updated = False
            logger.info("Inizio aggiornamento template master...")
            for key, value in extracted_data.items():
                logger.info(f"Processando campo: {key} = {value}")
                # Aggiorna il campo se il nuovo valore è valido (non None e non "null")
                if value is not None and value != "null":
                    self.template_master[key] = value
                    template_updated = True
                    logger.info(f"Campo {key} aggiornato con valore: {value}")
                else:
                    logger.info(f"Campo {key} ignorato: valore non valido")
            
            logger.info(f"Template master finale: {self.template_master}")
            logger.info(f"Template master aggiornato: {template_updated}")
            return self.template_master, template_updated
            
        except Exception as e:
            logger.error(f"Errore durante l'aggiornamento del template master: {str(e)}")
            logger.error(f"Stack trace:", exc_info=True)
            return self.template_master, False
    
    def process_template(self, template_attivo: str, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa il template attivo e aggiorna i dati dal template master
        
        Args:
            template_attivo: Nome del template attivo
            template_aggiornato: Dizionario contenente il template da aggiornare
            
        Returns:
            Dict[str, Any]: Template aggiornato con i dati dal master
        """
        logger.info(f"Processo template: {template_attivo}")
        
        # Mappa delle funzioni di processamento per ogni template
        template_processors = {
            "intro": self._process_intro_template,
            "contatti": self._process_contatti_template,
            "trasporto": self._process_trasporto_template,
            "alloggi": self._process_alloggi_template,
            "noleggi": self._process_noleggi_template,
            "naturalistico": self._process_naturalistico_template,
            "avventura": self._process_avventura_template,
            "montagna": self._process_montagna_template,
            "mare": self._process_mare_template,
            "gastronomia": self._process_gastronomia_template,
            "citta_arte": self._process_citta_arte_template,
            "benessere": self._process_benessere_template,
            "famiglia": self._process_famiglia_template
        }
        
        # Ottieni la funzione di processamento appropriata
        processor = template_processors.get(template_attivo)
        if processor:
            return processor(template_aggiornato)
        else:
            logger.warning(f"Nessun processore trovato per il template: {template_attivo}")
            return template_aggiornato
    
    def _process_intro_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template intro"""
        logger.info("Processo template intro")
        
        # Se ci sono bambini, imposta tipo_partecipanti a "famiglia"
        if 'bambini' in self.template_master and int(self.template_master['bambini']) > 0:
            template_aggiornato['tipo_partecipanti'] = "famiglia"
            logger.info("Impostato tipo_partecipanti a 'famiglia' per presenza di bambini")
            
            # Aggiungi "famiglia" a mood_vacanza se non è già presente
            if 'mood_vacanza' not in template_aggiornato:
                template_aggiornato['mood_vacanza'] = []
            elif template_aggiornato['mood_vacanza'] is None:
                template_aggiornato['mood_vacanza'] = []
                
            if isinstance(template_aggiornato['mood_vacanza'], list) and "famiglia" not in template_aggiornato['mood_vacanza']:
                template_aggiornato['mood_vacanza'].append("famiglia")
                logger.info("Aggiunto 'famiglia' a mood_vacanza")
        
        # Calcola il numero totale di partecipanti
        numero_totale = 0
        if 'anziani' in self.template_master and self.template_master['anziani'] is not None:
            numero_totale += int(self.template_master['anziani'])
        if 'adulti' in self.template_master and self.template_master['adulti'] is not None:
            numero_totale += int(self.template_master['adulti'])
        if 'bambini' in self.template_master and self.template_master['bambini'] is not None:
            numero_totale += int(self.template_master['bambini'])
        if 'genitori' in self.template_master and self.template_master['genitori'] is not None:
            numero_totale += int(self.template_master['genitori'])
            
        if numero_totale > 0:
            template_aggiornato['numero_partecipanti'] = numero_totale
            logger.info(f"Calcolato numero totale partecipanti: {numero_totale}")
        
        return template_aggiornato
    
    def _process_contatti_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template contatti"""
        logger.info("Processo template contatti")
        # Copia i dati rilevanti dal template master
        if 'full_name' in self.template_master:
            template_aggiornato['full_name'] = self.template_master['full_name']
        if 'codice_fiscale_o_partita_iva' in self.template_master:
            template_aggiornato['codice_fiscale_o_partita_iva'] = self.template_master['codice_fiscale_o_partita_iva']
        if 'numero_cellulare' in self.template_master:
            template_aggiornato['numero_cellulare'] = self.template_master['numero_cellulare']
        if 'email' in self.template_master:
            template_aggiornato['email'] = self.template_master['email']
        return template_aggiornato
    
    def _process_trasporto_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template trasporto"""
        logger.info("Processo template trasporto")
        # Copia i dati rilevanti dal template master
        if 'tipo_veicolo' in self.template_master:
            template_aggiornato['tipo_veicolo'] = self.template_master['tipo_veicolo']
        if 'luogo_partenza' in self.template_master:
            template_aggiornato['luogo_partenza'] = self.template_master['luogo_partenza']
        return template_aggiornato
    
    def _process_alloggi_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template alloggi"""
        logger.info("Processo template alloggi")
        # Copia i dati rilevanti dal template master
        if 'tipo_alloggio' in self.template_master:
            template_aggiornato['tipo_alloggio'] = self.template_master['tipo_alloggio']
        return template_aggiornato
    
    def _process_noleggi_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template noleggi"""
        logger.info("Processo template noleggi")
        # Copia i dati rilevanti dal template master
        if 'posti_auto' in self.template_master:
            template_aggiornato['posti_auto'] = self.template_master['posti_auto']
        if 'tipo_cambio' in self.template_master:
            template_aggiornato['tipo_cambio'] = self.template_master['tipo_cambio']
        return template_aggiornato
    
    def _process_naturalistico_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template naturalistico"""
        logger.info("Processo template naturalistico")
        # Copia i dati rilevanti dal template master
        if 'attivita_naturalistico' in self.template_master:
            template_aggiornato['attivita'] = self.template_master['attivita_naturalistico']
        return template_aggiornato
    
    def _process_avventura_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template avventura"""
        logger.info("Processo template avventura")
        # Copia i dati rilevanti dal template master
        if 'attivita_avventura' in self.template_master:
            template_aggiornato['attivita'] = self.template_master['attivita_avventura']
        return template_aggiornato
    
    def _process_montagna_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template montagna"""
        logger.info("Processo template montagna")
        # Copia i dati rilevanti dal template master
        if 'attivita_montagna' in self.template_master:
            template_aggiornato['attivita'] = self.template_master['attivita_montagna']
        return template_aggiornato
    
    def _process_mare_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template mare"""
        logger.info("Processo template mare")
        # Copia i dati rilevanti dal template master
        if 'attivita_mare' in self.template_master:
            template_aggiornato['attivita'] = self.template_master['attivita_mare']
        return template_aggiornato
    
    def _process_gastronomia_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template gastronomia"""
        logger.info("Processo template gastronomia")
        # Copia i dati rilevanti dal template master
        if 'degustazioni' in self.template_master:
            template_aggiornato['degustazioni'] = self.template_master['degustazioni']
        return template_aggiornato
    
    def _process_citta_arte_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template città e arte"""
        logger.info("Processo template città e arte")
        # Copia i dati rilevanti dal template master
        if 'attivita_citta_arte' in self.template_master:
            template_aggiornato['attivita'] = self.template_master['attivita_citta_arte']
        return template_aggiornato
    
    def _process_benessere_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template benessere"""
        logger.info("Processo template benessere")
        # Copia i dati rilevanti dal template master
        if 'trattamenti' in self.template_master:
            template_aggiornato['trattamenti'] = self.template_master['trattamenti']
        return template_aggiornato
    
    def _process_famiglia_template(self, template_aggiornato: Dict[str, Any]) -> Dict[str, Any]:
        """Processa il template famiglia"""
        logger.info("Processo template famiglia")
        # Copia i dati rilevanti dal template master
        if 'adulti' in self.template_master:
            template_aggiornato['adulti'] = self.template_master['adulti']
        if 'bambini' in self.template_master:
            template_aggiornato['bambini'] = self.template_master['bambini']
        return template_aggiornato
