package com.routetowonderland.drools.controller;

import com.routetowonderland.drools.model.TravelPreference;
import com.routetowonderland.drools.service.RuleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/preferences")
public class PreferenceController {

    private final RuleService ruleService;

    @Autowired
    public PreferenceController(RuleService ruleService) {
        this.ruleService = ruleService;
    }

    @PostMapping("/evaluate")
    public List<String> evaluatePreferences(@RequestBody TravelPreference preference) {
        // Aggiorna i flag booleani basati sul mood
        preference.updateMoodFlags();
        // Valuta le preferenze usando il servizio delle regole
        return ruleService.evaluateTemplates(preference);
    }
} 