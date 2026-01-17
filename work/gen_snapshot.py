import pandas as pd
import calendar
import os
import argparse
from datetime import datetime

# --- FUNKTIONEN ---
def lade_einstellungen(dateiname):
    einst = {"abwesenheiten": {}, "wünsche_n": {}, "wünsche_t": {}, "limits": {}, "namen": {}, "jahr": 2026, "monat": 1}
    temp_daten = []
    try:
        if not os.path.exists(dateiname): return einst
        with open(dateiname, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            for line in lines:
                key, val = [x.strip() for x in line.split(":", 1)]
                if key.startswith("MA_"): einst["namen"][key] = val
                elif key == "JAHR": einst["jahr"] = int(val)
                elif key == "MONAT": einst["monat"] = int(val)
                else: temp_daten.append((key, val))
            for key, val in temp_daten:
                ma_id = next((pid for pid in einst["namen"].keys() if pid in key), None)
                if not ma_id: continue
                name = einst["namen"][ma_id]
                if key.startswith("LIMIT_"): einst["limits"][name] = int(val)
                elif key.startswith("WUNSCH_TAG_"): einst["wünsche_t"][name] = [int(x) for x in val.split(",")]
                elif key.startswith("WUNSCH_NACHT_"): einst["wünsche_n"][name] = [int(x) for x in val.split(",")]
                elif key.startswith("ABW_"): einst["abwesenheiten"][name] = [int(x) for x in val.split(",")]
    except Exception as e: print(f"Fehler beim Laden der Einstellungen: {e}")
    return einst

def wer_kann(tag, ist_nacht, wer_gesperrt, config, counter, check_morgen_abwesend=False, anker_ma=None):
    mitarbeiter_namen = sorted(list(config["namen"].values()))
    
    # --- 1. ANKER-PRÜFUNG (Stabilität zuerst) ---
    if anker_ma and anker_ma in mitarbeiter_namen:
        # Check: Ist der Anker-Mitarbeiter heute verfügbar?
        ist_verfuegbar = (
            tag not in config["abwesenheiten"].get(anker_ma, []) and
            counter[anker_ma] < config["limits"].get(anker_ma, 31) and
            anker_ma not in wer_gesperrt
        )
        if ist_nacht and check_morgen_abwesend and (tag + 1) in config["abwesenheiten"].get(anker_ma, []):
            ist_verfuegbar = False
        
        if ist_verfuegbar:
            return anker_ma # Anker wird übernommen, kein Domino-Effekt

    # --- 2. POSITIV-WUNSCH (Wenn kein Anker oder Anker krank) ---
    wun_aktuell = config["wünsche_n"] if ist_nacht else config["wünsche_t"]
    for m in mitarbeiter_namen:
        if tag in wun_aktuell.get(m, []) and tag not in config["abwesenheiten"].get(m, []):
            if ist_nacht and check_morgen_abwesend and (tag + 1) in config["abwesenheiten"].get(m, []): continue
            if m not in wer_gesperrt and counter[m] < config["limits"].get(m, 31): return m
    
    # --- 3. REGULÄRE SUCHE ---
    wun_andere = config["wünsche_t"] if ist_nacht else config["wünsche_n"]
    kand = [m for m in mitarbeiter_namen 
            if tag not in config["abwesenheiten"].get(m, [])
            if counter[m] < config["limits"].get(m, 31) 
            if m not in wer_gesperrt
            if m not in wun_andere.get(m, [])]

    if ist_nacht and check_morgen_abwesend:
        kand = [m for m in kand if (tag + 1) not in config["abwesenheiten"].get(m, [])]

    if not kand: # Notfall-Backup
        kand = [m for m in mitarbeiter_namen if tag not in config["abwesenheiten"].get(m, []) 
                if counter[m] < config["limits"].get(m, 31) if m not in wer_gesperrt]

    if not kand: return None
    kand.sort(key=lambda x: counter[x])
    return kand[0]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--anker", help="Pfad zum alten Snapshot (Anker-Plan)", default=None)
    args = parser.parse_args()

    config = lade_einstellungen("einstellungen.txt")
    JAHR, MONAT = config["jahr"], config["monat"]
    name_to_id = {v: k for k, v in config["namen"].items()}
    mitarbeiter_namen = sorted(list(config["namen"].values()))
    _, tage_im_monat = calendar.monthrange(JAHR, MONAT)

    # Anker-Daten laden
    anker_dict = {}
    if args.anker and os.path.exists(args.anker):
        print(f"Lade Anker-Plan: {args.anker}")
        df_anker = pd.read_csv(args.anker)
        for _, row in df_anker.iterrows():
            if row["Name"] != "LÜCKEN":
                anker_dict[(int(row["Tag"]), row["Dienst"])] = row["Name"]

    df = pd.DataFrame("", index=mitarbeiter_namen, columns=[f"{i:02d}" for i in range(1, tage_im_monat + 1)])
    counter = {m: 0 for m in mitarbeiter_namen}
    luecken = {}
    wer_hatte_nacht_gestern = ""

    for t in range(1, tage_im_monat + 1):
        ts = f"{t:02d}"
        wd = calendar.weekday(JAHR, MONAT, t)
        
        # Tagdienst
        if wd <= 4:
            a_ma = anker_dict.get((t, "T"))
            bes = wer_kann(t, False, [wer_hatte_nacht_gestern], config, counter, anker_ma=a_ma)
            if bes: df.at[bes, ts], counter[bes] = "T", counter[bes] + 1
            else: luecken[t] = luecken.get(t, "") + "T"

        # Nachtdienst
        wer_hat_heute_tag = [m for m in mitarbeiter_namen if df.at[m, ts] == "T"]
        a_ma_n = anker_dict.get((t, "N"))
        bes_n = wer_kann(t, True, wer_hat_heute_tag, config, counter, True, anker_ma=a_ma_n)
        
        if bes_n:
            df.at[bes_n, ts], counter[bes_n] = "N", counter[bes_n] + 1
            wer_hatte_nacht_gestern = bes_n
        else:
            wer_hatte_nacht_gestern = ""
            luecken[t] = luecken.get(t, "") + "N"

    # Export
    snapshot_data = [[JAHR, MONAT, name_to_id[m], m, t, df.at[m, f"{t:02d}"]] 
                     for m in mitarbeiter_namen for t in range(1, tage_im_monat + 1) if df.at[m, f"{t:02d}"]]
    for t, status in luecken.items(): snapshot_data.append([JAHR, MONAT, "---", "LÜCKEN", t, status])
    
    zeitstempel = datetime.now().strftime("%d%m_%H%M")
    out_file = f"snapshot_{zeitstempel}.csv"
    pd.DataFrame(snapshot_data, columns=["Jahr", "Monat", "ID", "Name", "Tag", "Dienst"]).to_csv(out_file, index=False)
    print(f"Neuer Snapshot erstellt: {out_file}")

if __name__ == "__main__":
    main()