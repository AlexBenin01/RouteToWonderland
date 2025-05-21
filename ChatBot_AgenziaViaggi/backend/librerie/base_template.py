"""
Libreria base per tutti i template
Contiene le funzionalità comuni a tutti i template
"""

from typing import Dict, Any, Tuple, List
from .template_manager import TemplateManager

class BaseTemplate:
    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
    
    def set_template(self, template_name: str) -> bool:
        """Cambia il template attivo"""
        return self.template_manager.set_active_template(template_name)
    
    def get_template_data(self) -> Dict[str, Any]:
        """Ottiene i dati del template attivo"""
        return self.template_manager.get_active_template()
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Valida i dati in input secondo il template
        
        Args:
            data: Dizionario contenente i dati da validare
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (validità dei dati, messaggio di errore, dati corretti)
        """
        corrected_data = data.copy()
        template_data = self.get_template_data()
        
        try:
            # Validazione base che può essere estesa dalle classi figlie
            return True, "Dati validi", corrected_data
            
        except Exception as e:
            return False, f"Errore durante la validazione: {str(e)}", corrected_data
    
    
    def verifica_template(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str]]:
        """
        Verifica e aggiorna tutti i campi del template
        
        Args:
            data: Dizionario contenente i dati da verificare
            
        Returns:
            Tuple[Dict[str, Any], List[str], List[str]]: (template aggiornato, warnings, errors)
        """
        warnings = []
        errors = []
        updated_data = data.copy()
        
        try:
            
            # 2. Verifica la validità dei dati
            is_valid, msg, updated_data = self.validate_data(updated_data)
            if not is_valid:
                errors.append(msg)
            
            return updated_data, warnings, errors
            
        except Exception as e:
            errors.append(f"Errore durante la verifica del template: {str(e)}")
            return updated_data, warnings, errors 