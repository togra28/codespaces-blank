from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
import re

def bereinige_dateiname(name):
    ersatz = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'Euro'}
    for zeichen, neu in ersatz.items():
        name = name.replace(zeichen, neu)
    return re.sub(r'[^a-zA-Z0-9._-]', '_', name)

def generiere_mitarbeiter_pdfs(einstellungs_datei, testmodus=False):
    mitarbeiter_mapping = {} 
    gefundene_ids = []        
    jahr = "2026"
    monat_input = "1" 

    # Mapping von Zahl auf Name für die Vorauswahl
    monate_namen = {
        "1": "Januar", "2": "Februar", "3": "März", "4": "April",
        "5": "Mai", "6": "Juni", "7": "Juli", "8": "August",
        "9": "September", "10": "Oktober", "11": "November", "12": "Dezember"
    }

    if not os.path.exists(einstellungs_datei):
        print(f"Fehler: {einstellungs_datei} nicht gefunden.")
        return

    with open(einstellungs_datei, "r", encoding="utf-8") as f:
        for zeile in f:
            zeile = zeile.strip()
            if not zeile or zeile.startswith("#"): continue
            if zeile.startswith("JAHR:"): jahr = zeile.split(":")[1].strip()
            if zeile.startswith("MONAT:"): monat_input = zeile.split(":")[1].strip()
            if zeile.startswith("MA_") and ":" in zeile:
                parts = zeile.split(":")
                mitarbeiter_mapping[parts[0].strip()] = parts[1].strip()
            if zeile.startswith("LIMIT_MA_"):
                m_id = zeile.replace("LIMIT_", "").split(":")[0].strip()
                gefundene_ids.append(m_id)

    # Die Auswahl-Optionen nutzen jetzt Text als Wert
    auswahl_optionen = list(monate_namen.values())
    
    # Ermittle den Namen für die Vorauswahl (falls Zahl in TXT steht)
    vorauswahl_monat = monate_namen.get(monat_input, monat_input)

    for m_id in sorted(set(gefundene_ids)):
        klarname = mitarbeiter_mapping.get(m_id, m_id)
        sicherer_name = bereinige_dateiname(f"{klarname}-Dienste.pdf")
        
        c = canvas.Canvas(sicherer_name, pagesize=A4)
        form = c.acroForm
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 800, "Persönlicher Dienstplan-Input")
        c.setFont("Helvetica", 12)
        c.drawString(100, 770, f"Mitarbeiter: {klarname} | Jahr: {jahr}")
        
        y = 720
        c.setFont("Helvetica-Bold", 11)
        c.drawString(100, y, "Monat:")
        
        # Dropdown mit Klarnamen
        form.choice(
            name="MONAT",
            value=vorauswahl_monat, 
            options=auswahl_optionen,
            x=100, y=y-25,
            width=150, height=20,
            fieldFlags='combo'
        )
        
        y -= 65
        rest_felder = [
            ("Abwesenheiten (Tage):", f"ABW_{m_id}", "1, 2, 3"),
            ("Wunsch-Tagdienste (Tage):", f"WUNSCH_TAG_{m_id}", "10, 15"),
            ("Wunsch-Nachtdienste (Tage):", f"WUNSCH_NACHT_{m_id}", "20")
        ]
        
        for label, feldname, testwert in rest_felder:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(100, y, label)
            inhalt = testwert if testmodus else ""
            form.textfield(name=feldname, value=inhalt, x=100, y=y-25, width=350, height=20, borderStyle='underlined')
            y -= 65 

        c.save()
        print(f"Erstellt: {sicherer_name}")

# --- START ---
generiere_mitarbeiter_pdfs("einstellungen.txt", testmodus=True)