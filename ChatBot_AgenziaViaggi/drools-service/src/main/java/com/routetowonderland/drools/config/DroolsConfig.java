package com.routetowonderland.drools.config;

import org.kie.api.KieServices;
import org.kie.api.builder.KieBuilder;
import org.kie.api.builder.KieFileSystem;
import org.kie.api.builder.KieModule;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.kie.internal.io.ResourceFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DroolsConfig {

    private static final Logger logger = LoggerFactory.getLogger(DroolsConfig.class);
    private final KieServices kieServices = KieServices.Factory.get();

    @Bean
    public KieContainer kieContainer() {
        logger.info("=== INIZIO CONFIGURAZIONE DROOLS ===");
        logger.info("Creazione KieFileSystem...");
        KieFileSystem kieFileSystem = kieServices.newKieFileSystem();
        
        logger.info("Caricamento file regole: com/routetowonderland/drools/rules/sconto.drl");
        kieFileSystem.write(ResourceFactory.newClassPathResource("com/routetowonderland/drools/rules/sconto.drl"));
        
        logger.info("Creazione KieBuilder...");
        KieBuilder kieBuilder = kieServices.newKieBuilder(kieFileSystem);
        
        logger.info("Compilazione regole Drools...");
        kieBuilder.buildAll();
        
        if (kieBuilder.getResults().hasMessages()) {
            logger.error("Errori durante la compilazione delle regole:");
            kieBuilder.getResults().getMessages().forEach(message -> 
                logger.error("Errore: {}", message.getText()));
        } else {
            logger.info("Compilazione regole completata con successo");
        }
        
        logger.info("Creazione KieModule...");
        KieModule kieModule = kieBuilder.getKieModule();
        
        logger.info("Creazione KieContainer...");
        KieContainer container = kieServices.newKieContainer(kieModule.getReleaseId());
        
        logger.info("KieContainer creato con successo");
        logger.info("Regole disponibili: {}", container.getKieBaseNames());
        logger.info("=== FINE CONFIGURAZIONE DROOLS ===");
        
        return container;
    }

    @Bean
    public KieSession kieSession() {
        logger.info("Creazione KieSession bean...");
        KieSession session = kieContainer().newKieSession();
        logger.info("KieSession bean creata");
        return session;
    }
} 