import pandas as pd
import calendar
import argparse
import os

def style_html(data, jahr, monat, tage_im_monat):
    s = pd.DataFrame('', index=data.index, columns=data.columns)
    we = [f"{t:02d}" for t in range(1, tage_im_monat + 1) if calendar.weekday(jahr, monat, t) >= 5]
    
    for r in data.index:
        for c in data.columns:
            val = data.at[r, c]
            style = ""
            if c in we: 
                style += "background-color:#f2f2f2;"
            
            # r[1] ist der Name im MultiIndex (ID, Name)
            if r[1] == "LÜCKEN" and val != "":
                style += "background-color:#ffcccb;color:red;font-weight:bold;"
            elif val == "T": 
                style += "background-color:#90ee90;font-weight:bold;"
            elif val == "N": 
                style += "background-color:#add8e6;font-weight:bold;"
            
            s.at[r, c] = style
    return s

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Pfad zur Snapshot-CSV")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Fehler: Datei {args.file} nicht gefunden.")
        return

    # Daten laden
    snap = pd.read_csv(args.file)
    jahr = int(snap["Jahr"].iloc[0])
    monat = int(snap["Monat"].iloc[0])
    _, tage_im_monat = calendar.monthrange(jahr, monat)

    ma_snap = snap[snap["Name"] != "LÜCKEN"]
    luecken_snap = snap[snap["Name"] == "LÜCKEN"]
    
    rows = []
    unique_names = sorted(ma_snap["Name"].unique())
    
    # Mapping für IDs und Counter
    for name in unique_names:
        ma_id_full = ma_snap[ma_snap["Name"] == name]["ID"].iloc[0]
        kurz_id = str(ma_id_full).replace("MA_", "")
        anzahl = len(ma_snap[ma_snap["Name"] == name])
        rows.append((kurz_id, f"{name} ({anzahl})"))
    
    rows.append(("--", "LÜCKEN"))
    
    # MultiIndex ohne Namen erstellen (verhindert ID/Name im Header)
    index = pd.MultiIndex.from_tuples(rows, names=[None, None])
    columns = [f"{i:02d}" for i in range(1, tage_im_monat + 1)]
    df = pd.DataFrame("", index=index, columns=columns)

    # Daten füllen
    for _, row in ma_snap.iterrows():
        kurz_id = str(row["ID"]).replace("MA_", "")
        anzahl = len(ma_snap[ma_snap["Name"] == row["Name"]])
        df.at[(kurz_id, f"{row['Name']} ({anzahl})"), f"{row['Tag']:02d}"] = row["Dienst"]
        
    for _, row in luecken_snap.iterrows():
        df.at[("--", "LÜCKEN"), f"{row['Tag']:02d}"] = row["Dienst"]

    html_file = args.file.replace(".csv", ".html")
    monats_name = calendar.month_name[monat]
    
    styled_df = df.style.apply(style_html, axis=None, jahr=jahr, monat=monat, tage_im_monat=tage_im_monat)
    
    with open(html_file, "w", encoding="utf-8") as f:
        # CSS sorgt für saubere Ausrichtung der ersten beiden Spalten
        html_content = styled_df.to_html()
        f.write(f"<html><head><meta charset='utf-8'><style>")
        f.write("table{border-collapse:collapse;font-family:Arial;font-size:12px;}")
        f.write("td,th{border:1px solid #000;padding:4px;text-align:center;min-width:25px;}")
        f.write("th.row_heading{text-align:left; font-weight:normal; background-color:#ffffff;}")
        f.write("th.level0{width:30px; text-align:center;}") # Die ID Spalte
        f.write("th.level1{width:150px;}") # Die Namen Spalte
        f.write("</style></head><body>")
        f.write(f"<h2>Dienstplan {monats_name} {jahr}</h2>{html_content}</body></html>")

    print(f"HTML erfolgreich erstellt: {html_file}")

if __name__ == "__main__":
    main()