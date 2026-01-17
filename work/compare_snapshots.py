import pandas as pd
import argparse
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Zwei Snapshots vergleichen")
    parser.add_argument("alt", help="Pfad zur alten Snapshot-CSV")
    parser.add_argument("neu", help="Pfad zur neuen Snapshot-CSV")
    args = parser.parse_args()

    if not os.path.exists(args.alt) or not os.path.exists(args.neu):
        print("Fehler: Eine oder beide Dateien wurden nicht gefunden.")
        return

    # Daten laden und Index setzen
    df_alt = pd.read_csv(args.alt).set_index(["Name", "Tag"])
    df_neu = pd.read_csv(args.neu).set_index(["Name", "Tag"])

    # Metadaten prüfen (optionaler Hinweis)
    m_alt = f"{df_alt.iloc[0]['Monat']}/{df_alt.iloc[0]['Jahr']}"
    m_neu = f"{df_neu.iloc[0]['Monat']}/{df_neu.iloc[0]['Jahr']}"
    if m_alt != m_neu:
        print(f"HINWEIS: Du vergleichst verschiedene Zeiträume ({m_alt} vs. {m_neu})!")

    # Alle Mitarbeiter/Tag Kombinationen beider Dateien finden
    alle_kombis = df_alt.index.union(df_neu.index)
    änderungen = []

    for name, tag in alle_kombis:
        d_alt = df_alt.loc[(name, tag), "Dienst"] if (name, tag) in df_alt.index else ""
        d_neu = df_neu.loc[(name, tag), "Dienst"] if (name, tag) in df_neu.index else ""

        if d_alt != d_neu:
            status = "GEÄNDERT"
            if d_alt == "": status = "NEU"
            elif d_neu == "": status = "ENTFERNT"
            
            änderungen.append({
                "Mitarbeiter": name,
                "Tag": tag,
                "Status": status,
                "Alt": d_alt,
                "Neu": d_neu
            })

    if änderungen:
        diff_df = pd.DataFrame(änderungen)
        zeitstempel = datetime.now().strftime("%d%m_%H%M")
        output_file = f"kandidaten_aenderung_{zeitstempel}.csv"
        diff_df.to_csv(output_file, index=False, sep=";")
        print(f"Vergleich abgeschlossen. {len(änderungen)} Änderungen gefunden.")
        print(f"Datei erstellt: {output_file}")
        print("\nVorschau der Änderungen:")
        print(diff_df.head(10))
    else:
        print("Keine Unterschiede zwischen den Snapshots gefunden.")

if __name__ == "__main__":
    main()