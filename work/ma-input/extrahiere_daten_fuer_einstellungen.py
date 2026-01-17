import os
from pypdf import PdfReader
from collections import Counter

def extrahiere_mit_statistik(ordner=".", ziel_datei="extraktion_ergebnis.txt"):
    ergebnisse = {"ABW": [], "TAG": [], "NACHT": []}
    ma_counter = 0
    alle_tage = []

    dateien = [f for f in os.listdir(ordner) if f.endswith("-Dienste.pdf")]
    
    for datei in dateien:
        try:
            reader = PdfReader(os.path.join(ordner, datei))
            fields = reader.get_fields()
            if not fields: continue
            
            ma_counter += 1
            for f_name, f_data in fields.items():
                wert = str(f_data.get('/V', '')).strip()
                if not wert or f_name == "MONAT": continue
                
                # Daten sammeln und Statistik-Liste füttern
                if f_name.startswith("WUNSCH_TAG_"):
                    ergebnisse["TAG"].append(f"{f_name}: {wert}")
                elif f_name.startswith("WUNSCH_NACHT_"):
                    ergebnisse["NACHT"].append(f"{f_name}: {wert}")
                elif f_name.startswith("ABW_"):
                    ergebnisse["ABW"].append(f"{f_name}: {wert}")
                    # Tage für die "Engpass-Analyse" sammeln
                    tage = [t.strip() for t in wert.split(",") if t.strip().isdigit()]
                    alle_tage.extend(tage)
        except Exception as e:
            print(f"Fehler bei {datei}: {e}")

    # Statistik berechnen
    haeufige_tage = Counter(alle_tage).most_common(3)

    # In Datei schreiben
    with open(ziel_datei, "w", encoding="utf-8") as f:
        f.write(f"# DIENSTPLAN-AUSWERTUNG\n# Verarbeitete Personen: {ma_counter}\n\n")
        for key, label in [("ABW", "Abwesenheiten"), ("NACHT", "Wunsch-Nacht"), ("TAG", "Wunsch-Tag")]:
            f.write(f"# {label}\n" + "\n".join(sorted(ergebnisse[key])) + "\n\n")

    # Demo-Ausgabe für den Dienstplaner
    print("-" * 40)
    print(f"ERGEBNIS FÜR DEN DIENSTPLANER:")
    print(f"-> {ma_counter} PDFs erfolgreich eingelesen.")
    if haeufige_tage:
        print(f"-> ACHTUNG: Am häufigsten fehlen Leute an Tag: {', '.join([f'der {t[0]}. ({t[1]}x)' for t in haeufige_tage])}")
    print(f"-> Datei '{ziel_datei}' wurde erstellt.")
    print("-" * 40)

extrahiere_mit_statistik()