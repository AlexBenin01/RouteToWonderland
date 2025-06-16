package com.routetowonderland.drools.controller;

import com.routetowonderland.drools.model.RichiestaSconto;
import com.routetowonderland.drools.model.RispostaSconto;
import com.routetowonderland.drools.service.ScontoService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class ScontoController {

    private static final Logger logger = LoggerFactory.getLogger(ScontoController.class);

    @Autowired
    private ScontoService scontoService;

    @PostMapping("/calcola-sconto")
    public ResponseEntity<RispostaSconto> calcolaSconto(@RequestBody RichiestaSconto richiesta) {
        logger.info("=== RICEVUTA CHIAMATA HTTP ===");
        logger.info("Endpoint: /api/calcola-sconto");
        logger.info("Totale speso: {}", richiesta.getTotale_speso());
        logger.info("Fatturato annuale: {}", richiesta.getFatturato_annuale());
        
        RispostaSconto risposta = scontoService.calcolaGradoSconto(richiesta);
        
        logger.info("Grado sconto calcolato: {}", risposta.getGrado_sconto());
        logger.info("=== FINE CHIAMATA HTTP ===");
        
        return ResponseEntity.ok(risposta);
    }
} 