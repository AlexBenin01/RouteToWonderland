package com.routetowonderland.drools.model;

import lombok.Data;
import java.util.List;

@Data
public class TravelPreference {
    // Campi base aggiornati per corrispondere a TravelPreferenceRequest
    private String nazioneDestinazione;
    private String regioneCittaDestinazione;
    private int numeroPartecipanti;
    private String tipoPartecipanti; // adulti, anziani, famiglia
    private String departureDate;
    private int tripDuration;
    private List<String> moodVacanza; // Lista di mood: avventura, cultura, benessere, mare, montagna, citta_arte, famiglia, naturalistico, gastronomia
    private int budgetViaggio;
    
    // Campi derivati per facilitare le regole
    private boolean mare;
    private boolean montagna;
    private boolean cittaArte;
    private boolean gastronomia;
    private boolean benessere;
    private boolean avventura;
    private boolean naturalistico;
    private boolean famiglia;
    private boolean cultura;
    
    // Preferenze aggiuntive
    private String periodo;
    private int budget;
    private int numeroPersone;
    private boolean conBambini;
    
    // Metodo per aggiornare i campi booleani basati sul mood
    public void updateMoodFlags() {
        if (moodVacanza != null) {
            mare = moodVacanza.contains("mare");
            montagna = moodVacanza.contains("montagna");
            cittaArte = moodVacanza.contains("citta_arte");
            gastronomia = moodVacanza.contains("gastronomia");
            benessere = moodVacanza.contains("benessere");
            avventura = moodVacanza.contains("avventura");
            naturalistico = moodVacanza.contains("naturalistico");
            famiglia = moodVacanza.contains("famiglia");
            cultura = moodVacanza.contains("cultura");
        }
    }
} 