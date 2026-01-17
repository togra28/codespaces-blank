import pandas as pd
import calendar
import argparse
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Einzelsnapshots für Mitarbeiter erstellen")
    # Das erste Argument ist die Datei, die als Plan ausgegeben werden soll
    parser.add_argument("datei", help="Der Snapshot, der gedruckt werden soll (CSV)")
    # Das zweite Argument ist optional der Anker für den Vergleich
    parser.add_argument("anker", nargs="?", help="Optional: Der alte Snapshot zum Vergleich (Anker)", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.datei):
        print(f"Fehler: Datei {args.datei} nicht gefunden.")
        return

    # Daten laden
    df_neu = pd.read_csv(args.datei)
    jahr = int(df_neu["Jahr"].iloc[0])
    monat = int(df_neu["Monat"].iloc[0])
    mitarbeiter_liste = sorted(df_neu[df_neu["Name"] != "LÜCKEN"]["Name"].unique())
    _, tage_im_monat = calendar.monthrange(jahr, monat)
    monats_name = calendar.month_name[monat]
    wt_namen = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    # Vergleichsdaten laden falls Anker angegeben
    df_alt = None
    if args.anker and os.path.exists(args.anker):
        df_alt = pd.read_csv(args.anker).set_index(["Name", "Tag"])
        print(f"Vergleichsmodus aktiv: Änderungen gegenüber {args.anker} werden markiert.")
    else:
        print("Normalmodus: Erstelle Pläne ohne Markierungen.")

    # Ordner für die Ergebnisse erstellen
    zeitstempel = datetime.now().strftime("%d%m_%H%M")
    folder = f"mitarbeiter_plaene_{zeitstempel}"
    os.makedirs(folder, exist_ok=True)

    # Für jeden Mitarbeiter einen Plan erstellen
    for m in mitarbeiter_liste:
        m_data = df_neu[df_neu["Name"] == m].set_index("Tag")
        zeilen = []
        
        # Wir gehen alle Tage durch, um auch ENTFERNTE Dienste zu finden
        for t in range(1, tage_im_monat + 1):
            d_neu = m_data.loc[t, "Dienst"] if t in m_data.index else ""
            
            status_html = ""
            inline_style = ""
            
            # Logik für Vergleich/Markierung
            if df_alt is not None:
                idx = (m, t)
                d_alt = df_alt.loc[idx, "Dienst"] if idx in df_alt.index else ""
                
                if d_neu != d_alt:
                    if d_alt == "" and d_neu != "":
                        status_html = " <b style='color:green;'>(NEU)</b>"
                        inline_style = "background-color:#e6fffa;" # Grün
                    elif d_neu != "" and d_alt != "":
                        status_html = f" <b style='color:orange;'>(GEÄNDERT, war {d_alt})</b>"
                        inline_style = "background-color:#fffce0;" # Gelb
                    elif d_neu == "" and d_alt != "":
                        # Dienst wurde im neuen Plan entfernt
                        zeilen.append(
                            f"<tr style='background-color:#ffe6e6;'>"
                            f"<td>{t:02d}.{monat:02d}.</td>"
                            f"<td><del>{'Tagdienst' if d_alt=='T' else 'Nachtdienst'}</del> <b style='color:red;'>(ENTFERNT)</b></td>"
                            f"</tr>"
                        )
                        continue

            # Dienstzeile hinzufügen, wenn im neuen Plan vorhanden
            if d_neu != "":
                wd = wt_namen[calendar.weekday(jahr, monat, t)]
                dienst_text = "Tagdienst" if d_neu == "T" else "Nachtdienst"
                zeilen.append(
                    f"<tr style='{inline_style}'>"
                    f"<td>{wd}, {t:02d}.{monat:02d}.</td>"
                    f"<td>{dienst_text}{status_html}</td>"
                    f"</tr>"
                )

        # HTML Datei schreiben
        file_path = os.path.join(folder, f"Plan_{m}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("<html><head><meta charset='utf-8'></head><body style='font-family:Arial;'>")
            f.write(f"<h3>Persönlicher Dienstplan: {m}</h3>")
            f.write(f"<h4>Monat: {monats_name} {jahr}</h4>")
            
            if df_alt is not None:
                f.write("<p style='font-size:0.9em;'><i>Hinweis: Farbige Markierungen zeigen Änderungen zum letzten Stand.</i></p>")
            
            f.write("<table border='1' style='border-collapse:collapse; width:500px;'>")
            f.write("<tr style='background:#eee;'><th>Datum</th><th>Dienstleistung</th></tr>")
            f.write("".join(zeilen) if zeilen else "<tr><td colspan='2'>Keine Dienste eingeteilt</td></tr>")
            f.write("</table>")
            
            # Legende nur bei Vergleich anzeigen
            if df_alt is not None:
                f.write("<p style='font-size:0.8em; margin-top:15px;'><b>Legende:</b> "
                        "<span style='background-color:#e6fffa; padding:2px;'>Grün = Einspringer/Neu</span> | "
                        "<span style='background-color:#fffce0; padding:2px;'>Gelb = Schichttausch</span> | "
                        "<span style='background-color:#ffe6e6; padding:2px;'>Rot = Dienst entfällt</span></p>")
            
            f.write(f"<p><small>Generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M')}</small></p>")
            f.write("</body></html>")

    print(f"Fertig! Einzelpläne wurden im Ordner '{folder}' gespeichert.")

if __name__ == "__main__":
    main()