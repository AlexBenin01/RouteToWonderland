package com.routetowonderland.drools.service;

import com.routetowonderland.drools.model.RichiestaSconto;
import com.routetowonderland.drools.model.RispostaSconto;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ScontoService {

    private static final Logger logger = LoggerFactory.getLogger(ScontoService.class);

    @Autowired
    private KieContainer kieContainer;

    public RispostaSconto calcolaGradoSconto(RichiestaSconto richiesta) {
        logger.info("=== INIZIO CALCOLO GRADO SCONTO ===");
        logger.info("KieContainer caricato: {}", kieContainer != null ? "SI" : "NO");
        logger.info("Regole disponibili nel container: {}", kieContainer.getKieBaseNames());
        
        RispostaSconto risposta = new RispostaSconto();
        
        // Crea una nuova sessione per ogni richiesta
        logger.info("Creazione nuova KieSession...");
        KieSession kieSession = kieContainer.newKieSession();
        logger.info("KieSession creata con successo");
        
        try {
            // Inserisci i fatti nella sessione Drools
            logger.info("Inserimento fatti nella sessione Drools...");
            logger.info("Fatto 1 - RichiestaSconto: totale_speso={}, fatturato_annuale={}", 
                       richiesta.getTotale_speso(), richiesta.getFatturato_annuale());
            kieSession.insert(richiesta);
            
            logger.info("Fatto 2 - RispostaSconto: inizializzata");
            kieSession.insert(risposta);
            
            // Esegui le regole
            logger.info("Esecuzione regole Drools...");
            int rulesExecuted = kieSession.fireAllRules();
            logger.info("Regole eseguite: {}", rulesExecuted);
            
            logger.info("Risultato finale - Grado sconto: {}", risposta.getGrado_sconto());
            logger.info("=== FINE CALCOLO GRADO SCONTO ===");
            
            return risposta;
        } finally {
            // Assicurati che la sessione venga sempre chiusa
            logger.info("Chiusura KieSession...");
            kieSession.dispose();
            logger.info("KieSession chiusa");
        }
    }
} 