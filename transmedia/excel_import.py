import pandas as pd


def _norm_cols(cols):
    return [str(c).strip().upper() for c in cols]


def _clean(x):
    if isinstance(x, str):
        return x.strip()
    return x


def read_inventory_sheet(file_obj):
    """
    Reads uploaded excel and returns cleaned dataframe for sheet: 'media inventory table'
    Column header must include: TERMINALEQUIPMENT ID (can be blank).
    """
    df = pd.read_excel(file_obj, sheet_name="media inventory table", dtype=str)
    df.columns = _norm_cols(df.columns)

    # ✅ pandas new versions: use DataFrame.map instead of applymap
    df = df.map(_clean)

    col_map = {
        "SL NO": "sl_no",
        "SITE NAME": "site_name",
        "TRANSMISSION MEDIA (OF/DMW)": "transmission_media",
        "A END (SAY CPAN A1)": "a_end",
        "B END (TE B1 NODE)": "b_end",
        "TERMINAL EQUIPMENT(MAAN/DMW/CPAN)": "terminal_equipment_type",
        "MAKE": "make",
        "TERMINALEQUIPMENT ID": "terminalequipment_id",
        "CLUSTER": "cluster",
        "2G PORT": "port_2g",
        "3G PORT": "port_3g",
        "4G PORT": "port_4g",
    }

    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Ensure must-have columns exist
    for c in ["site_name", "terminal_equipment_type"]:
        if c not in df.columns:
            df[c] = ""

    if "terminalequipment_id" not in df.columns:
        df["terminalequipment_id"] = ""

    return df