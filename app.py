# app.py
# --------------------------------------------------------------
# Värvimise tabeli VAATAJA (lihtversioon)
# - Lae üles Excel/CSV
# - (Excel) vali sheet, vaikimisi päiserida = 3
# - Kuva ainult kuni veeruni "Pak+näidis" (kui selline veerg eksisteerib)
# - Kuva tabelit Exceli-laadselt (AgGrid kui saadaval) või tavalise tabelina
# - All: katelde planeerimise tabel numbrilises järjekorras (1102 → 1137)
# --------------------------------------------------------------

from __future__ import annotations
import io
import pandas as pd
import streamlit as st

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode  # type: ignore[misc]
    HAS_AGGRID = True
except Exception:
    HAS_AGGRID = False

st.set_page_config(page_title="Värvimise tabeli vaade", page_icon="📄", layout="wide")
st.title("📄 Värvimise tabeli vaade")
st.caption("Lae Excel/CSV ja vaata andmeid. (Filtrid/reeglid on ajutiselt maas.)")

# ------------------------------
# Abifunktsioonid
# ------------------------------

def _to_bytesio(uploaded) -> io.BytesIO:
    b = io.BytesIO(uploaded.getvalue())
    b.seek(0)
    return b

def _list_sheets(uploaded):
    b = _to_bytesio(uploaded)
    xl = pd.ExcelFile(b, engine="openpyxl")
    return xl.sheet_names

def read_with_header(uploaded, sheet: str, header_row_index: int) -> pd.DataFrame:
    b = _to_bytesio(uploaded)
    df = pd.read_excel(b, sheet_name=sheet, engine="openpyxl", header=header_row_index)
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ")
        .str.replace("\r", " ")
    )
    return df

def _trim_to_pak_naidis(df: pd.DataFrame) -> pd.DataFrame:
    if "Pak+näidis" in df.columns:
        col_idx = df.columns.get_loc("Pak+näidis") + 1
        df = df.iloc[:, :col_idx]
    df = df.dropna(how="all")
    return df

# ------------------------------
# Faili üleslaadimine + sheet/päis
# ------------------------------
with st.sidebar:
    st.header("1) Lae andmed")
    uploaded = st.file_uploader(
        "Laadi Excel (.xlsx/.xlsm) või CSV",
        type=["xlsx", "xlsm", "csv"],
        accept_multiple_files=False,
    )
    if HAS_AGGRID:
        st.caption("Grid: st-aggrid on aktiivne.")
    else:
        st.caption("(Valikuline) `pip install streamlit-aggrid` annab Exceli-laadse vaate.")

if uploaded is None:
    st.info("⬅️ Laadi vasakult fail.")
    st.stop()

# CSV
if uploaded.name.lower().endswith(".csv"):
    try:
        df = pd.read_csv(uploaded)
    except Exception:
        uploaded.seek(0)
        df = pd.read_csv(uploaded, sep=';', encoding='utf-8', engine='python')
    df.columns = df.columns.astype(str).str.strip()
    df = _trim_to_pak_naidis(df)
else:
    sheets = _list_sheets(uploaded)
    st.subheader("Sheet ja päis")
    sheet_name = st.selectbox("Vali sheet", options=sheets, index=0)
    header_row_index = st.number_input(
        "Päiserida (0 = esimene rida)", min_value=0, max_value=200, value=3, step=1,
        help="Vaikimisi 3, kuna sinu failides algavad veerunimed tavaliselt neljandast reast.",
    )
    df = read_with_header(uploaded, sheet_name, int(header_row_index))
    df = _trim_to_pak_naidis(df)

st.success(f"Fail laetud: **{uploaded.name}**. Read: {len(df)}")

# ------------------------------
# Tabeli kuvamine
# ------------------------------
if df.empty:
    st.warning("Tabel on tühi.")
else:
    if HAS_AGGRID:
        gob = GridOptionsBuilder.from_dataframe(df)
        gob.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)
        gob.configure_default_column(resizable=True, sortable=True, filter=True)
        gridOptions = gob.build()
        AgGrid(df, gridOptions=gridOptions, update_mode=GridUpdateMode.NO_UPDATE, fit_columns_on_grid_load=True, height=600)
    else:
        st.dataframe(df, use_container_width=True)

@st.cache_data
def _excel_bytes(_df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        _df.to_excel(writer, index=False, sheet_name="Andmed")
    buf.seek(0)
    return buf.read()

st.download_button(
    label="⬇️ Lae nähtav tabel Excelina",
    data=_excel_bytes(df),
    file_name="tabel_export.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.caption("Kuvatakse kuni veeruni 'Pak+näidis' (kui olemas) ja tühjad read eemaldatakse.")

# ------------------------------
# Katelde planeerimine — fikseeritud mahutuvused (näidised)
# ------------------------------
st.header("5) Katelde mahutuvused — fikseeritud")

BOILERS = [
    1102, 1105, 1110, 1111, 1113, 1114, 1115, 1116, 1117, 1118,
    1119, 1120, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128,
    1129, 1131, 1132, 1137
]

# Pildi põhjal sisestatud vahemikud (kg). Muuda julgelt vastavalt tegelikule tabelile.
BOILER_CAPACITY = {
    1102: (175, 300),
    1105: (3.5, 10),
    1110: (98, 150),
    1111: (50, 70),
    1113: (340, 800),
    1114: (6, 29),
    1115: (6, 15),
    1116: (3, 7),
    1117: (6, 14),
    1118: (650, 1050),
    1119: (650, 1050),
    1120: (700, 1250),
    1121: (700, 1250),
    1122: (350, 600),
    1123: (30, 66),
    1124: (60, 140),
    1125: (175, 300),
    1126: (1300, 2100),
    1127: (66, 110),
    1128: (150, 220),
    1129: (350, 600),
    1131: (98, 150),
    1132: (50, 75),
    1137: (7, 35),
}

cap_df = (
    pd.DataFrame([
        {"Katla nr": b, "Mahutuvus min": BOILER_CAPACITY[b][0], "Mahutuvus max": BOILER_CAPACITY[b][1]}
        for b in sorted(BOILERS)
    ])
)

st.dataframe(cap_df, use_container_width=True, hide_index=True)

st.caption("Vahemikud võetud sinu jagatud pildilt; kontrolli üle ja muuda koodis BOILER_CAPACITY sõnastikus, kui mõni number vajab täpsustamist (nt koma vs punkt).")

# ------------------------------
# Tellimused katla järgi (klikitav menüü)
# ------------------------------
st.subheader("6) Tellimused katla järgi")

# Abi: leia veerud "Värvim. tellim. nr" ja "Kg" automaatselt
import re

def _norm(s: str) -> str:
    s = s.lower()
    s = s.replace("ä", "a").replace("ö", "o").replace("õ", "o").replace("ü", "u")
    return re.sub(r"[^a-z0-9]+", "", s)

ORDER_COL = None
KG_COL = None
for c in df.columns:
    sc = _norm(str(c))
    if ORDER_COL is None and ("varvim" in sc and "tellim" in sc):
        ORDER_COL = c
    if KG_COL is None and (sc == "kg" or sc.endswith("kg")):
        KG_COL = c

if ORDER_COL is None or KG_COL is None:
    st.warning("Ei leidnud veerge ‘Värvim. tellim. nr’ või ‘Kg’. Palun kontrolli päiserida/veerunimesid.")
else:
    st.caption(f"Kasutatakse veerge: **{ORDER_COL}** (tellimus) ja **{KG_COL}** (kg).")

    # Nupud kateldele (6 tükki reas)
    if "selected_boiler" not in st.session_state:
        st.session_state.selected_boiler = None

    rows = 6
    for i in range(0, len(BOILERS), rows):
        cols = st.columns(rows)
        for j, b in enumerate(BOILERS[i:i+rows]):
            if cols[j].button(str(b), key=f"boilbtn_{b}"):
                st.session_state.selected_boiler = b

    sel = st.session_state.selected_boiler
    if sel is None:
        st.info("Vali ülevalt katel, et näha sinna sobivaid tellimusi.")
    else:
        bmin, bmax = BOILER_CAPACITY[sel]
        # Filtreeri sobivad tellimused vahemiku järgi
        work = df.copy()
        work["_kg"] = pd.to_numeric(work[KG_COL], errors="coerce")
        work = work.dropna(subset=["_kg"]) 
        eligible = work[ (work["_kg"] >= bmin) & (work["_kg"] <= bmax) ]
        # Võta välja ainult tellimuse nr ja kg
        out = eligible[[ORDER_COL, "_kg"]].rename(columns={ORDER_COL: "Värvim. tellim. nr", "_kg": "Kg"})
        out["Värvim. tellim. nr"] = out["Värvim. tellim. nr"].astype(str)

        st.markdown(f"**Katel {sel}** — vahemik {bmin}–{bmax} kg")
        st.write(f"Leitud tellimusi: **{len(out)}**, kogusumma: **{int(out['Kg'].sum()) if len(out)>0 else 0} kg**")
        if out.empty:
            st.info("Selles vahemikus ühtegi tellimust ei leitud.")
        else:
            st.dataframe(out.sort_values(by=["Kg"], ascending=False), use_container_width=False, hide_index=True)
