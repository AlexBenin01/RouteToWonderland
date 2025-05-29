package com.routetowonderland.drools.service;

import com.routetowonderland.drools.model.RichiestaSconto;
import com.routetowonderland.drools.model.RispostaSconto;
import org.kie.api.runtime.KieSession;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class ScontoService {

    @Autowired
    private KieSession kieSession;

    public RispostaSconto calcolaGradoSconto(RichiestaSconto richiesta) {
        RispostaSconto risposta = new RispostaSconto();
        
        // Inserisci i fatti nella sessione Drools
        kieSession.insert(richiesta);
        kieSession.insert(risposta);
        
        // Esegui le regole
        kieSession.fireAllRules();
        
        // Pulisci la sessione
        kieSession.dispose();
        
        return risposta;
    }
} 