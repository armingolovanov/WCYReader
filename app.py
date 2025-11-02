# app.py
# --------------------------------------------------------------
# Värvimise tabeli VAATAJA (lihtversioon)
# - Lae üles Excel/CSV
# - (Excel) vali sheet, vaikimisi päiserida = 3
# - Kuva ainult kuni veeruni "Pak+näidis" (kui selline veerg eksisteerib)
# - Kuva tabelit Exceli-laadselt (AgGrid kui saadaval) või tavalise tabelina
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

# Abiplokk: piirame veerud kuni "Pak+näidis" ja eemaldame tühjad read

def _trim_to_pak_naidis(df: pd.DataFrame) -> pd.DataFrame:
    if "Pak+näidis" in df.columns:
        col_idx = df.columns.get_loc("Pak+näidis") + 1
        df = df.iloc[:, :col_idx]
    # Eemalda täiesti tühjad read (kui päise järel on tühi saba)
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
    # Excel
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
