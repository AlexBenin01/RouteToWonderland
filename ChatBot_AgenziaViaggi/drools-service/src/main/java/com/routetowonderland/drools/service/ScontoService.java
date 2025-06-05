package com.routetowonderland.drools.service;

import com.routetowonderland.drools.model.RichiestaSconto;
import com.routetowonderland.drools.model.RispostaSconto;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ScontoService {

    @Autowired
    private KieContainer kieContainer;

    public RispostaSconto calcolaGradoSconto(RichiestaSconto richiesta) {
        RispostaSconto risposta = new RispostaSconto();
        
        // Crea una nuova sessione per ogni richiesta
        KieSession kieSession = kieContainer.newKieSession();
        
        try {
            // Inserisci i fatti nella sessione Drools
            kieSession.insert(richiesta);
            kieSession.insert(risposta);
            
            // Esegui le regole
            kieSession.fireAllRules();
            
            return risposta;
        } finally {
            // Assicurati che la sessione venga sempre chiusa
            kieSession.dispose();
        }
    }
} 