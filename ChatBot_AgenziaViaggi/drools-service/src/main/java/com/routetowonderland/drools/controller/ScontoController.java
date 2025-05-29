package com.routetowonderland.drools.controller;

import com.routetowonderland.drools.model.RichiestaSconto;
import com.routetowonderland.drools.model.RispostaSconto;
import com.routetowonderland.drools.service.ScontoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class ScontoController {

    @Autowired
    private ScontoService scontoService;

    @PostMapping("/calcola-sconto")
    public ResponseEntity<RispostaSconto> calcolaSconto(@RequestBody RichiestaSconto richiesta) {
        RispostaSconto risposta = scontoService.calcolaGradoSconto(richiesta);
        return ResponseEntity.ok(risposta);
    }
} 