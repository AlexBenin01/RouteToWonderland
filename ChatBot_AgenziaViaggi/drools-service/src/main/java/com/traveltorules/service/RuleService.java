package com.traveltorules.service;

import com.traveltorules.model.TravelPreference;
import org.kie.api.KieServices;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.HashSet;
import java.util.Set;
import java.util.List;
import java.util.ArrayList;

@Service
public class RuleService {
    private static final Logger logger = LoggerFactory.getLogger(RuleService.class);
    private final KieContainer kieContainer;

    public RuleService() {
        KieServices kieServices = KieServices.Factory.get();
        this.kieContainer = kieServices.getKieClasspathContainer();
    }

    public List<String> evaluateTemplates(TravelPreference preference) {
        logger.info("Ricevuta richiesta di valutazione con i seguenti dati:");
        logger.info("Nazione: {}", preference.getNazioneDestinazione());
        logger.info("Regione/Città: {}", preference.getRegioneCittaDestinazione());
        logger.info("Numero Partecipanti: {}", preference.getNumeroPartecipanti());
        logger.info("Tipo Partecipanti: {}", preference.getTipoPartecipanti());
        logger.info("Data Partenza: {}", preference.getDepartureDate());
        logger.info("Durata Viaggio: {}", preference.getTripDuration());
        logger.info("Mood Vacanza: {}", preference.getMoodVacanza());
        logger.info("Budget: {}", preference.getBudgetViaggio());

        // Verifica che tutti i campi necessari siano presenti
        if (!isIntroTemplateComplete(preference)) {
            logger.error("Template incompleto. Campi mancanti:");
            if (preference.getNazioneDestinazione() == null) logger.error("- Nazione mancante");
            if (preference.getRegioneCittaDestinazione() == null) logger.error("- Regione/Città mancante");
            if (preference.getNumeroPartecipanti() <= 0) logger.error("- Numero partecipanti non valido");
            if (preference.getTipoPartecipanti() == null) logger.error("- Tipo partecipanti mancante");
            if (preference.getDepartureDate() == null) logger.error("- Data partenza mancante");
            if (preference.getTripDuration() <= 0) logger.error("- Durata viaggio non valida");
            if (preference.getMoodVacanza() == null || preference.getMoodVacanza().isEmpty()) logger.error("- Mood vacanza mancante");
            if (preference.getBudgetViaggio() <= 0) logger.error("- Budget non valido");
            
            throw new IllegalStateException("Il template 'intro' non è completo. Tutti i campi sono obbligatori.");
        }

        KieSession kieSession = kieContainer.newKieSession("ksession-rules");
        List<String> activeTemplates = new ArrayList<>();
        
        try {
            logger.info("Inizio valutazione regole Drools");
            kieSession.setGlobal("activeTemplates", activeTemplates);
            kieSession.insert(preference);
            kieSession.fireAllRules();
            logger.info("Valutazione regole completata. Templates attivi: {}", activeTemplates);
        } finally {
            kieSession.dispose();
        }
        
        return activeTemplates;
    }

    private boolean isIntroTemplateComplete(TravelPreference preference) {
        return preference.getNazioneDestinazione() != null &&
               preference.getRegioneCittaDestinazione() != null &&
               preference.getNumeroPartecipanti() > 0 &&
               preference.getTipoPartecipanti() != null &&
               preference.getDepartureDate() != null &&
               preference.getTripDuration() > 0 &&
               preference.getMoodVacanza() != null && !preference.getMoodVacanza().isEmpty() &&
               preference.getBudgetViaggio() > 0;
    }
} 