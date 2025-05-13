import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from utils import construct_message, prepare_inputs, nuextract_generate
import json
from datetime import datetime, timedelta
import copy
import spacy

# Carica spaCy solo una volta
NLP_SPACY = spacy.load("xx_ent_wiki_sm")

def estrai_nome_cognome_spacy(nominativo):
    """
    Estrae nome e cognome da una stringa usando spaCy.
    """
    doc = NLP_SPACY(nominativo)
    persone = [ent.text for ent in doc.ents if ent.label_ == "PER"]
    if persone:
        parts = persone[0].split()
        if len(parts) >= 2:
            return parts[0], " ".join(parts[1:])
        elif len(parts) == 1:
            return parts[0], ""
    # fallback: tutto come nome, cognome vuoto
    return nominativo, ""

# =====================
# UTILITY GENERALI
# =====================
def extract_entities(text, template, model_path='./NuExtract-2-2B-experimental', current_data=None):
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
    msg = construct_message(text, template, current_data)
    input_messages = [msg]
    input_content = prepare_inputs(
        messages=input_messages,
        image_paths=[],
        tokenizer=tokenizer,
    )
    generation_config = {"do_sample": False, "num_beams": 1, "max_new_tokens": 2048}
    with torch.no_grad():
        result = nuextract_generate(
            model=model,
            tokenizer=tokenizer,
            prompts=input_content['prompts'],
            pixel_values_list=input_content['pixel_values_list'],
            num_patches_list=input_content['num_patches_list'],
            generation_config=generation_config
        )
    return result[0]

def extract_and_print(text, template, model_path='./NuExtract-2-2B-experimental'):
    """
    Estrae e stampa le entità dal testo.
    
    Args:
        text: Il testo da analizzare
        template: Il template JSON che definisce lo schema di output
        model_path: Il percorso al modello NuExtract
    """
    result = extract_entities(text, template, model_path)
    return result

def save_extraction_to_file(extraction, filename=None):
    """
    Salva l'estrazione in un file JSON.
    
    Args:
        extraction: La stringa JSON da salvare
        filename: Il nome del file (opzionale)
    """
    if filename is None:
        # Genera un nome basato sul timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extraction_{timestamp}.json"
    
    # Assicurati che sia un oggetto JSON valido
    try:
        json_data = json.loads(extraction)
    except json.JSONDecodeError:
        json_data = {"raw_output": extraction}
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

def is_bool_explicit(val):
    # Accetta solo risposte esplicite: True/False, 'true'/'false', 'sì'/'no', 'si'/'no'
    if isinstance(val, bool):
        return True
    if isinstance(val, str):
        v = val.strip().lower()
        return v in ['true', 'false', 'sì', 'si', 'no']
    return False

def is_no_extra(val):
    # Accetta risposte che indicano nessuna attività extra
    if isinstance(val, list) and len(val) == 0:
        return True
    if isinstance(val, str):
        v = val.strip().lower()
        return v in ['nessuna', 'no', 'nulla', 'niente', 'nessun']
    return False

# =====================
# TEMPLATE DINAMICO
# =====================
def build_dynamic_template(template_attivo, stato, template_keys, templates):
    """
    Costruisce un template dinamico per NuEstract:
    - Esclude richiesta_guida e lingua_guida finché non è il loro turno.
    - Se richiesta_guida è false, non include lingua_guida.
    """
    base_template = json.loads(templates[template_attivo])
    keys = template_keys[template_attivo]
    # Per i luoghi, gestisci dinamicamente
    if template_attivo == "luoghi":
        luogo_in_corso = stato.get("luogo_in_corso", {})
        # Se manca richiesta_guida, escludi sia richiesta_guida che lingua_guida
        if "richiesta_guida" not in luogo_in_corso or luogo_in_corso["richiesta_guida"] in [None, '', [], {}]:
            keys = [k for k in keys if k not in ["richiesta_guida", "lingua_guida"]]
        # Se richiesta_guida è false, escludi lingua_guida
        elif luogo_in_corso.get("richiesta_guida", None) is False:
            keys = [k for k in keys if k != "lingua_guida"]
        # Se richiesta_guida è true, includi anche lingua_guida
        # Ricostruisci il template solo con le chiavi attive
        template_dict = {k: base_template[k] for k in keys if k in base_template}
        return json.dumps(template_dict)
    # Per altri template, restituisci il template originale
    return templates[template_attivo]

# =====================
# GESTIONE DATE
# =====================
def fix_future_date(date_str, today=None):
    """Porta la data nel futuro se è nel passato, incrementando l'anno."""
    if not date_str:
        return date_str
    if today is None:
        today = datetime.now()
    # Prova vari formati
    formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"]
    for fmt in formats:
        try:
            d = datetime.strptime(date_str, fmt)
            # Incrementa l'anno finché la data non è nel futuro
            while d < today:
                try:
                    d = d.replace(year=d.year + 1)
                except ValueError:
                    # Gestisce il caso del 29 febbraio in anni non bisestili
                    d = d.replace(month=3, day=1, year=d.year + 1)
            output = d.strftime(fmt)
            return output
        except Exception as e:
            continue
    return date_str

def is_between(date_str, start_str, end_str):
    """Controlla se la DATA (non l'orario) di date_str è tra start_str e end_str (tutti in formato ISO)."""
    try:
        # Estrai solo la parte di data
        if 'T' in date_str:
            d = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
        else:
            d = datetime.strptime(date_str, "%Y-%m-%d")
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")
        result = start.date() <= d.date() <= end.date()
        return result
    except Exception as e:
        return False

# =====================
# SUPPORTO CONVERSAZIONE
# =====================
def completa_luogo(stato, luogo_in_corso, template_attivo):
    stato.setdefault("luoghi", []).append(copy.deepcopy(luogo_in_corso))
    stato["luogo_in_corso"] = {}
    stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
    return {
        "estrazione": {},
        "template_usato": template_attivo,
        "stato_conversazione": stato,
        "stato_conversazione_json": stato_conversazione_json_new,
        "luogo_completato": True,
        "guide_phrase": "✅ Luogo aggiunto! Vuoi aggiungere un altro luogo?"
}

# =====================
# FUNZIONE PRINCIPALE
# =====================
def process_extraction(
    text,
    template_attivo,
    stato_conversazione_json,
    templates,
    template_keys,
    guide_phrases,
    model_path='./NuExtract-2-2B-experimental',
    campo=None
):
    # --- LOG INIZIALE ---
    print("=== INIZIO PROCESS_EXTRACTION ===")
    print(f"text: {text}")
    print(f"template_attivo: {template_attivo}")
    print(f"campo: {campo}")
    print(f"stato_conversazione_json: {stato_conversazione_json}")
    print("===============================")

    stato = json.loads(stato_conversazione_json)

    # --- CONTROLLO ESPLICITO PER ATTIVITA_EXTRA ---
    if template_attivo == "luoghi" and (campo == "attivita_extra" or "attività extra" in text.lower() or "attivita extra" in text.lower()):
        print("=== GESTIONE ATTIVITA_EXTRA ===")
        luogo_in_corso = stato.get("luogo_in_corso", {})
        print(f"luogo_in_corso prima: {luogo_in_corso}")
        if is_no_extra(text):
            luogo_in_corso["attivita_extra"] = ""
        else:
            # Rimuovi il prefisso "attività extra: " se presente
            text = text.strip()
            if text.lower().startswith("attività extra: "):
                text = text[16:]
            elif text.lower().startswith("attivita extra: "):
                text = text[15:]
            # Imposta direttamente il testo come attivita_extra
            luogo_in_corso["attivita_extra"] = text
        print(f"luogo_in_corso dopo: {luogo_in_corso}")
        stato["luogo_in_corso"] = luogo_in_corso
        stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
        
        # --- CONTROLLO COMPLETAMENTO LUOGO ---
        luogo_completato = all(
            (
                (k == "lingua_guida" and luogo_in_corso.get("richiesta_guida", None) is False)
                or (k == "attivita_extra" and isinstance(luogo_in_corso.get("attivita_extra", None), str))
                or (k in luogo_in_corso and (luogo_in_corso[k] not in [None, '', {}, []] if k != "attivita_extra" else k in luogo_in_corso))
            )
            for k in template_keys["luoghi"]
        )
        print(f"luogo_completato: {luogo_completato}")
        
        if luogo_completato:
            print("=== LUOGO COMPLETATO ===")
            return completa_luogo(stato, luogo_in_corso, template_attivo)
            
        # Trova la prossima guida_phrase (NON attivita_extra!)
        guide_phrase = None
        for k in template_keys["luoghi"]:
            if k not in luogo_in_corso:
                if k != "attivita_extra":
                    guide_phrase = guide_phrases["luoghi"][k]
                    break
        print(f"guide_phrase: {guide_phrase}")
        print("=========================")
        return {
            'estrazione': {},
            'template_usato': template_attivo,
            'stato_conversazione': stato,
            'stato_conversazione_json': stato_conversazione_json_new,
            'luogo_completato': luogo_completato,
            'guide_phrase': guide_phrase
        }

    # --- GESTIONE NOTE AGGIUNTIVE ---
    if template_attivo == "contatti" and (campo == "note_aggiuntive" or "note aggiuntive: " in text.lower()):
        print("=== GESTIONE NOTE AGGIUNTIVE ===")
        stato_template = stato.get("contatti", {})
        print(f"stato_template prima: {stato_template}")
        if is_no_extra(text):
            stato_template["note_aggiuntive"] = ""
            # Rimuovi il campo nominativo_completo se presente
            if "nominativo_completo" in stato_template:
                del stato_template["nominativo_completo"]
        else:
              # Rimuovi il prefisso "note aggiuntive: " se presente
            text = text.strip()
            if text.lower().startswith("note aggiuntive: "):
                text = text[17:]
            elif text.lower().startswith("note aggiuntive: "):
                text = text[16:]
            # Imposta direttamente il testo come note_aggiuntive
            stato_template["note_aggiuntive"] = text
        print(f"stato_template dopo: {stato_template}")
        stato["contatti"] = stato_template
        stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
        
        # Trova la prossima guida_phrase
        guide_phrase = None
        for k in template_keys["contatti"]:
            if k == "nominativo_completo":
                continue
            if k not in stato_template or stato_template[k] in [None, '', [], {}]:
                guide_phrase = guide_phrases["contatti"][k]
                break
        
        # --- CONTROLLO COMPLETAMENTO TEMPLATE CONTATTI ---
        template_keys_no_nominativo = [k for k in template_keys["contatti"] if k != "nominativo_completo"]
        if all(is_field_filled_contatti(k, stato_template) for k in template_keys_no_nominativo):
            guide_phrase = None  # Nessuna guida_phrase = template completo
            
        return {
            "estrazione": {},
            "template_usato": template_attivo,
            "stato_conversazione": stato,
            "stato_conversazione_json": stato_conversazione_json_new,
            "guide_phrase": guide_phrase
        }

    # --- GESTIONE SALTA STEP PRIMA DI TUTTO: NO AI! ---
    if text == 'salta_step_alloggi' and template_attivo == 'alloggi':
        print("=== SALTA STEP ALLOGGI ===")
        stato['alloggi'] = {
            'nome_struttura': '',
            'indirizzo_struttura': ''
        }
        stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
        return {
            'estrazione': {},
            'template_usato': template_attivo,
            'stato_conversazione': stato,
            'stato_conversazione_json': stato_conversazione_json_new,
            'guide_phrase': "Hai scelto di saltare lo step Alloggi.",
            'nuovo_template': True,
            'next_template': 'noleggi'
        }
    if text == 'salta_step_noleggi' and template_attivo == 'noleggi':
        stato['noleggi'] = {
            'richiesta_auto': '',
            'posti_auto': '',
            'tipo_auto': '',
            'budget_auto': ''
        }
        stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
        return {
            'estrazione': {},
            'template_usato': template_attivo,
            'stato_conversazione': stato,
            'stato_conversazione_json': stato_conversazione_json_new,
            'guide_phrase': "Hai scelto di saltare lo step Noleggi.",
            'nuovo_template': True,
            'next_template': 'contatti'
        }

    # --- GESTIONE TEMPLATE CONTATTI CON NOMINATIVO COMPLETO E SPACY ---
    if template_attivo == "contatti":
        stato_template = stato.get("contatti", {})
        # Step 1: se manca nominativo_completo, estrai solo quello
        if "nominativo_completo" not in stato_template or not stato_template["nominativo_completo"]:
            # Estrai solo nominativo_completo con NuEstract
            temp_template = json.dumps({"nominativo_completo": json.loads(templates["contatti"])["nominativo_completo"]})
            result = extract_entities(text, temp_template, model_path)
            result_dict = json.loads(result)
            nominativo = result_dict.get("nominativo_completo", "")
            stato_template["nominativo_completo"] = nominativo
            # Applica spaCy
            nome, cognome = estrai_nome_cognome_spacy(nominativo)
            if nome:
                stato_template["nome"] = nome
            if cognome:
                stato_template["cognome"] = cognome
            stato["contatti"] = stato_template
            stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
            # Se manca nome o cognome, chiedi solo il campo mancante
            if not nome:
                guide_phrase = guide_phrases["contatti"]["nome"]
            elif not cognome:
                guide_phrase = guide_phrases["contatti"]["cognome"]
            else:
                # Passa al prossimo campo (numero_cellulare)
                for k in template_keys["contatti"]:
                    if k == "nominativo_completo":
                        continue
                    if k not in stato_template or stato_template[k] in [None, '', [], {}]:
                        guide_phrase = guide_phrases["contatti"][k]
                        break
            return {
                "estrazione": {},
                "template_usato": template_attivo,
                "stato_conversazione": stato,
                "stato_conversazione_json": stato_conversazione_json_new,
                "guide_phrase": guide_phrase
            }
        # Step 2: se manca nome o cognome, passa la risposta a spaCy
        if (campo == "nome" or campo == "cognome") and text.strip():
            nome = stato_template.get("nome", "")
            cognome = stato_template.get("cognome", "")
            # Applica spaCy alla risposta
            n, c = estrai_nome_cognome_spacy(text)
            if campo == "nome" and n:
                stato_template["nome"] = n
            if campo == "cognome" and c:
                stato_template["cognome"] = c
            stato["contatti"] = stato_template
            stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
            # Se manca ancora uno dei due, chiedi
            if not stato_template.get("nome"):
                guide_phrase = guide_phrases["contatti"]["nome"]
            elif not stato_template.get("cognome"):
                guide_phrase = guide_phrases["contatti"]["cognome"]
            else:
                # Passa al prossimo campo (numero_cellulare)
                for k in template_keys["contatti"]:
                    if k == "nominativo_completo":
                        continue
                    if k not in stato_template or stato_template[k] in [None, '', [], {}]:
                        guide_phrase = guide_phrases["contatti"][k]
                        break
            return {
                "estrazione": {},
                "template_usato": template_attivo,
                "stato_conversazione": stato,
                "stato_conversazione_json": stato_conversazione_json_new,
                "guide_phrase": guide_phrase
            }
        # Step 3: se nome e cognome sono presenti, continua con NuEstract per gli altri campi
        # Crea un template senza nominativo_completo e note_aggiuntive
        final_template_dict = json.loads(templates["contatti"])
        final_template_dict.pop("nominativo_completo", None)
        temp_template = json.dumps(final_template_dict)
        
        # --- NON passare current_data, lavora solo con text e template ---
        result = extract_entities(text, temp_template, model_path)
        result_dict = json.loads(result)
        # Aggiorna solo i campi non ancora valorizzati
        for k in template_keys["contatti"]:
            if k == "nominativo_completo":
                continue
            # NON sovrascrivere nome/cognome se già valorizzati
            if k in stato_template and stato_template[k] not in [None, '', [], {}]:
                continue
            if k in result_dict and result_dict[k] not in [None, '', [], {}]:
                stato_template[k] = result_dict[k]
        stato["contatti"] = stato_template
        # Trova la prima chiave mancante e la frase guida da mostrare
        guide_phrase = None
        for k in template_keys["contatti"]:
            if k == "nominativo_completo":
                continue
            if k not in stato_template or stato_template[k] in [None, '', [], {}]:
                guide_phrase = guide_phrases["contatti"][k]
                break
        stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
        return {
            "estrazione": result_dict,
            "template_usato": template_attivo,
            "stato_conversazione": stato,
            "stato_conversazione_json": stato_conversazione_json_new,
            "guide_phrase": guide_phrase
        }

    # --- GESTIONE DIRETTA Sì/No su campo specifico se richiesto dal frontend ---
    if campo and template_attivo == "luoghi":
        luogo_in_corso = stato.get("luogo_in_corso", {})
        obbligatori = template_keys["luoghi"]
        if campo == "richiesta_guida" and is_bool_explicit(text):
            # Aggiorna SOLO richiesta_guida, mantenendo gli altri campi già presenti
            luogo_in_corso["richiesta_guida"] = text.strip().lower() in ["true", "sì", "si"] or text.strip().lower() == "1"
            # Se la scelta è No, imposta anche lingua_guida =""
            if luogo_in_corso["richiesta_guida"] is False:
                luogo_in_corso["lingua_guida"] = ""
            stato["luogo_in_corso"] = luogo_in_corso  # mantiene tutti i campi già presenti

            # --- CONTROLLO COMPLETAMENTO LUOGO ---
            luogo_completato = all(
                (
                    (k == "lingua_guida" and luogo_in_corso.get("richiesta_guida", None) is False)
                    or (k == "attivita_extra" and isinstance(luogo_in_corso.get("attivita_extra", None), list))
                    or (k in luogo_in_corso and (luogo_in_corso[k] not in [None, '', {}, []] if k != "attivita_extra" else k in luogo_in_corso))
                )
                for k in obbligatori
            )
            if luogo_completato:
                return completa_luogo(stato, luogo_in_corso, template_attivo)

            stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
            guide_phrase = None
            # Se la risposta è Sì, la prossima guida_phrase è sempre lingua_guida
            if luogo_in_corso["richiesta_guida"] is True:
                guide_phrase = guide_phrases["luoghi"]["lingua_guida"]
            else:
                for k in obbligatori:
                    if k == "lingua_guida" and luogo_in_corso.get("richiesta_guida", None) is False:
                        continue
                    if k == "attivita_extra" and isinstance(luogo_in_corso.get("attivita_extra", None), list):
                        continue
                    if k not in luogo_in_corso or luogo_in_corso[k] in [None, '', [], {}]:
                        guide_phrase = guide_phrases["luoghi"][k]
                        break
            if guide_phrase:
                return {
                    "estrazione": {},
                    "template_usato": template_attivo,
                    "stato_conversazione": stato,
                    "stato_conversazione_json": stato_conversazione_json_new,
                    "luogo_completato": False,
                    "guide_phrase": guide_phrase
                }
    # Se il campo attivita_extra è già compilato (anche se vuoto), NON riproporre la domanda
    if template_attivo == "luoghi":
        luogo_in_corso = stato.get("luogo_in_corso", {})
        if "attivita_extra" in luogo_in_corso and luogo_in_corso["attivita_extra"] not in [None, '', {}]:
            # Salta la domanda su attivita_extra
            pass
    # GESTIONE DIRETTA Sì/No per altri template (se necessario, estendibile)
    # Costruisci template dinamico
    template = build_dynamic_template(template_attivo, stato, template_keys, templates)
    # Estrai le informazioni dal testo usando NuEstract
    result = extract_entities(text, template, model_path)
    result_dict = json.loads(result)
    # Se siamo nei luoghi e richiesta_guida è false, aggiungi lingua_guida vuoto
    if template_attivo == "luoghi":
        luogo_in_corso = stato.get("luogo_in_corso", {})
        richiesta_guida_val = luogo_in_corso.get("richiesta_guida", None)
        # Se richiesta_guida è stato appena impostato a false, oppure già false, forza lingua_guida vuoto
        if ("richiesta_guida" in luogo_in_corso and luogo_in_corso["richiesta_guida"] is False) or ("richiesta_guida" in result_dict and result_dict["richiesta_guida"] is False):
            result_dict["lingua_guida"] = ""
    # --- CORREZIONE DATE ---
    today = datetime.now()
    if 'data_partenza' in result_dict:
        result_dict['data_partenza'] = fix_future_date(result_dict['data_partenza'], today)
    if 'data_ritorno' in result_dict:
        data_partenza_ref = result_dict.get('data_partenza') or stato.get('intro', {}).get('data_partenza')
        if data_partenza_ref:
            result_dict['data_ritorno'] = fix_future_date(result_dict['data_ritorno'], datetime.strptime(data_partenza_ref.split('T')[0], "%Y-%m-%d"))
        else:
            # Se manca la data di partenza, rimuovi data_ritorno dal risultato
            result_dict.pop('data_ritorno', None)
    if 'orario_visita' in result_dict:
        data_partenza = result_dict.get('data_partenza') or stato.get('intro', {}).get('data_partenza')
        data_ritorno = result_dict.get('data_ritorno') or stato.get('intro', {}).get('data_ritorno')
        if data_partenza:
            # Usa la data di partenza come riferimento invece della data di oggi
            orario_visita = fix_future_date(result_dict['orario_visita'], datetime.strptime(data_partenza.split('T')[0], "%Y-%m-%d"))
            if data_ritorno:
                if not is_between(orario_visita, data_partenza, data_ritorno):
                    result_dict.pop('orario_visita', None)
                else:
                    result_dict['orario_visita'] = orario_visita
            else:
                result_dict['orario_visita'] = orario_visita
        else:
            # Se non c'è data di partenza, rimuovi orario_visita
            result_dict.pop('orario_visita', None)
    luogo_completato = False  # Flag per sapere se un luogo è stato completato
    guide_phrase = None       # Frase guida da mostrare all'utente

    # --- GESTIONE TEMPLATE SINGOLI ---
    if template_attivo != "luoghi":
        stato_template = stato.get(template_attivo, {})
        updated = False
        # Aggiorna solo i campi non ancora valorizzati
        for k in template_keys[template_attivo]:
            if k in stato_template and stato_template[k] not in [None, '', [], {}]:
                continue  # non sovrascrivere il campo già valorizzato
            if k in result_dict and result_dict[k] not in [None, '', [], {}]:
                stato_template[k] = result_dict[k]
                updated = True
        if updated:
            stato[template_attivo] = stato_template
        # Trova la prima chiave mancante e la frase guida da mostrare
        for k in template_keys[template_attivo]:
            if k not in stato_template or stato_template[k] in [None, '', [], {}]:
                guide_phrase = guide_phrases[template_attivo][k]
                break
    # --- GESTIONE TEMPLATE LUOGHI (campo per campo, input parziali) ---
    else:
        luogo_in_corso = stato.get("luogo_in_corso", {})
        updated = False
        obbligatori = template_keys["luoghi"]
        primo_mancante = None
        for k in obbligatori:
            if k == "lingua_guida" and luogo_in_corso.get("richiesta_guida", None) is False:
                continue
            if k not in luogo_in_corso or luogo_in_corso[k] in [None, '', [], {}]:
                primo_mancante = k
                break
        # Aggiorna solo i campi non ancora valorizzati del luogo in corso
        for k in obbligatori:
            if k in luogo_in_corso and luogo_in_corso[k] not in [None, '', [], {}]:
                continue
            if k in result_dict and result_dict[k] not in [None, '', [], {}]:
                # Per attivita_extra, accetta anche risposte "nessuna", "no", ecc.
                if k == "attivita_extra":
                    val = result_dict[k]
                    if is_no_extra(val):
                        luogo_in_corso[k] = ""
                        updated = True
                    else:
                        luogo_in_corso[k] = val
                        updated = True
                else:
                    luogo_in_corso[k] = result_dict[k]
                    updated = True
        # Se manca attivita_extra e il campo mancante è proprio quello, controlla direttamente il testo utente
        for k in obbligatori:
            if k == "lingua_guida" and luogo_in_corso.get("richiesta_guida", None) is False:
                continue
            # PATCH: attivita_extra è completato anche se è lista vuota
            if k == "attivita_extra":
                if k not in luogo_in_corso or luogo_in_corso[k] is None:
                    guide_phrase = guide_phrases["luoghi"][k]
                    break
                if isinstance(luogo_in_corso[k], list):
                    continue  # lista (anche vuota) = campo compilato
                if luogo_in_corso[k] in ['', {}, []]:
                    guide_phrase = guide_phrases["luoghi"][k]
                    break
            elif k not in luogo_in_corso or luogo_in_corso[k] in [None, '', [], {}]:
                guide_phrase = guide_phrases["luoghi"][k]
                break
        # Se il luogo in corso è completo (tutti i campi obbligatori, attivita_extra può essere lista vuota, lingua_guida ignorata se richiesta_guida è false)
        if all(
            (
                (k == "lingua_guida" and luogo_in_corso.get("richiesta_guida", None) is False)
                or (k == "attivita_extra" and isinstance(luogo_in_corso.get("attivita_extra", None), list))
                or (k in luogo_in_corso and (luogo_in_corso[k] not in [None, '', {}, []] if k != "attivita_extra" else k in luogo_in_corso))
            )
            for k in obbligatori
        ):
            return completa_luogo(stato, luogo_in_corso, template_attivo)
        else:
            stato["luogo_in_corso"] = luogo_in_corso

        # --- CONTROLLO COERENZA PARTECIPANTI ---
        numero_partecipanti = stato.get("intro", {}).get("numero_partecipanti")
        partecipanti_visita = luogo_in_corso.get("partecipanti_visita")
        try:
            n_partecipanti = int(numero_partecipanti) if numero_partecipanti is not None else None
            p_visita = int(partecipanti_visita) if partecipanti_visita is not None else None
        except Exception:
            n_partecipanti = numero_partecipanti
            p_visita = partecipanti_visita
        if (
            n_partecipanti is not None and p_visita is not None
            and isinstance(n_partecipanti, int) and isinstance(p_visita, int)
            and p_visita > n_partecipanti
        ):
            # Rimuovo il campo errato prima di restituire l'errore
            if "partecipanti_visita" in luogo_in_corso:
                del luogo_in_corso["partecipanti_visita"]
            stato["luogo_in_corso"] = luogo_in_corso
            return {
                "estrazione": {},
                "template_usato": template_attivo,
                "stato_conversazione": stato,
                "stato_conversazione_json": json.dumps(stato, ensure_ascii=False, indent=2),
                "luogo_completato": False,
                "guide_phrase": "Il numero di partecipanti alla visita non può essere maggiore del numero totale di partecipanti al viaggio. Riprova."
            }

    stato_conversazione_json_new = json.dumps(stato, ensure_ascii=False, indent=2)
    return {
        "estrazione": result_dict,
        "template_usato": template_attivo,
        "stato_conversazione": stato,
        "stato_conversazione_json": stato_conversazione_json_new,
        "luogo_completato": luogo_completato,
        "guide_phrase": guide_phrase
    }

# Funzione di supporto per il controllo dei campi compilati in contatti
def is_field_filled_contatti(k, stato_template):
    # note_aggiuntive è un campo opzionale, quindi lo consideriamo sempre compilato
    if k == "note_aggiuntive":
        return True
    return k in stato_template and stato_template[k] not in [None, '', [], {}]
