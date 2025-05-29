"""
Libreria per la gestione dei template
Gestisce il caricamento, l'accesso e la sequenza dei template
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateManager:
    def __init__(self):
        self.templates: Dict[str, Dict[str, Any]] = {}
        self.active_template: Optional[str] = None
        self.template_sequence: List[str] = []
        
    def load_templates(self):
        """Carica tutti i template disponibili"""
        template_files = {
            "intro": "intro.json",
            "contatti": "contatti.json",
            "trasporto": "trasporto.json",
            "alloggi": "alloggi.json",
            "noleggi": "noleggi.json",
            "naturalistico": "naturalistico.json",
            "avventura": "avventura.json",
            "montagna": "montagna.json",
            "mare": "mare.json",
            "gastronomia": "gastronomia.json",
            "citta_arte": "citta_arte.json",
            "benessere": "benessere.json",
            "famiglia": "famiglia.json",
            "exit": "exit.json"
        }
        
        for template_name, file_name in template_files.items():
            try:
                with open(f"template/{file_name}", 'r', encoding='utf-8') as f:
                    self.templates[template_name] = json.load(f)
                logger.info(f"Template {template_name} caricato con successo")
            except FileNotFoundError:
                logger.warning(f"Template {template_name} non trovato")
                
    def set_active_template(self, template_name: str) -> bool:
        """
        Imposta il template attivo
        
        Args:
            template_name: Nome del template da impostare come attivo
            
        Returns:
            bool: True se il template è stato impostato con successo, False altrimenti
        """
        if template_name in self.templates:
            self.active_template = template_name
            return True
        logger.warning(f"Template {template_name} non trovato")
        return False
        
    def get_active_template(self) -> Optional[Dict[str, Any]]:
        """
        Restituisce il template attivo
        
        Returns:
            Optional[Dict[str, Any]]: Il template attivo o None se non è impostato
        """
        return self.templates.get(self.active_template)
        
    def get_template_sequence(self) -> List[str]:
        """
        Restituisce la sequenza dei template
        
        Returns:
            List[str]: Lista dei template nella sequenza
        """
        return self.template_sequence
        
    def update_template_sequence(self, new_sequence: List[str]):
        """
        Aggiorna la sequenza dei template
        
        Args:
            new_sequence: Nuova sequenza di template
        """
        self.template_sequence = new_sequence
        logger.info(f"Sequenza template aggiornata: {new_sequence}")
        
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene un template specifico
        
        Args:
            template_name: Nome del template da ottenere
            
        Returns:
            Optional[Dict[str, Any]]: Il template richiesto o None se non esiste
        """
        return self.templates.get(template_name)
        
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Restituisce tutti i template
        
        Returns:
            Dict[str, Dict[str, Any]]: Dizionario con tutti i template
        """
        return self.templates.copy() 
    
    def get_exit_template(self) -> Optional[Dict[str, Any]]:
        """
        Ottiene il template di uscita
        
        Returns:
            Optional[Dict[str, Any]]: Il template di uscita o None se non esiste
        """
        return self.templates.get("exit")