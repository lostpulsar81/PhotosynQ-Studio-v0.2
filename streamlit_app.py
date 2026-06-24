
import io
import pandas as pd
import plotly.express as px
import streamlit as st

from database import connect, fetch_measurements, insert_measurements, delete_all
from importer import parse_uploaded_file

st.set_page_config(page_title="PhotosynQ Studio", layout="wide")
st.title("PhotosynQ Studio v0.1")
st.caption("Archivio locale, import, grafici ed export per misure PhotosynQ/MultispeQ.")

conn = connect()

with st.sidebar:
    st.header("Nuovo import")
    experiment = st.text_input("Esperimento", value="Maize HA experiment")
    treatment = st.text_input("Trattamento", value="")
    sample_id = st.text_input("Sample ID", value="")
    plant_id = st.text_input("Plant / pot ID", value="")
    replicate = st.text_input("Replica", value="")
    notes = st.text_area("Note", value="", height=90)

    metadata = {
        "experiment": experiment,
        "treatment": treatment,
        "sample_id": sample_id,
        "plant_id": plant_id,
        "replicate": replicate,
        "notes": notes,
    }

    uploaded_files = st.file_uploader(
        "Importa file PhotosynQ JSON/CSV",
        type=["json", "csv", "txt"],
        accept_multiple_files=True,
    )

    if st.button("Importa nel database", type="primary", use_container_width=True):
        if not uploaded_files:
            st.warning("Carica almeno un file.")
        else:
            total = 0
            errors = []
            for uploaded_file in uploaded_files:
                try:
                    rows = parse_uploaded_file(uploaded_file, metadata)
                    total += insert_measurements(conn, rows)
                except Exception as e:
                    errors.append(f"{uploaded_file.name}: {e}")
            if total:
                st.success(f"Importate {total} misure.")
            if errors:
                st.error("Alcuni file non sono stati importati:\\n" + "\\n".join(errors))

    st.divider()
    with st.expander("Zona pericolosa"):
        if st.button("Cancella tutto il database", use_container_width=True):
            delete_all(conn)
            st.warning("Database cancellato.")

rows = fetch_measurements(conn)
df = pd.DataFrame([dict(r) for r in rows])

if df.empty:
    st.info("Nessuna misura importata. Carica un file JSON/CSV dalla barra laterale.")
    st.stop()

numeric_cols = [
    "phi2", "phinpq", "phino", "npqt", "ql", "lef", "spad", "ecst",
    "vhplus", "ghplus", "pmf", "p700", "ps1_active_centers",
    "ps1_open_centers", "ps1_oxidized_centers", "ps1_over_reduced_centers",
    "par", "leaf_temperature", "ambient_temperature", "humidity", "pressure",
    "thickness", "angle"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

st.subheader("Database locale")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Misure", len(df))
m2.metric("Esperimenti", df["experiment"].nunique(dropna=True))
m3.metric("Trattamenti", df["treatment"].nunique(dropna=True))
m4.metric("File sorgente", df["source_file"].nunique(dropna=True))

with st.expander("Filtri", expanded=True):
    c1, c2, c3 = st.columns(3)
    experiments = sorted([x for x in df["experiment"].dropna().unique()])
    treatments = sorted([x for x in df["treatment"].dropna().unique()])
    files = sorted([x for x in df["source_file"].dropna().unique()])
    selected_experiments = c1.multiselect("Esperimenti", experiments, default=experiments)
    selected_treatments = c2.multiselect("Trattamenti", treatments, default=treatments)
    selected_files = c3.multiselect("File sorgente", files, default=files)

filtered = df.copy()
if selected_experiments:
    filtered = filtered[filtered["experiment"].isin(selected_experiments)]
if selected_treatments:
    filtered = filtered[filtered["treatment"].isin(selected_treatments)]
if selected_files:
    filtered = filtered[filtered["source_file"].isin(selected_files)]

st.write(f"Misure visualizzate: **{len(filtered)}**")

preferred_cols = [
    "id", "timestamp", "experiment", "treatment", "sample_id", "plant_id", "replicate",
    "phi2", "lef", "npqt", "phinpq", "phino", "ql", "spad", "par",
    "leaf_temperature", "ambient_temperature", "humidity", "thickness", "notes", "source_file"
]
visible_cols = [c for c in preferred_cols if c in filtered.columns]
st.dataframe(filtered[visible_cols], use_container_width=True, height=320)

st.subheader("Grafici rapidi")
available_params = [c for c in numeric_cols if c in filtered.columns and filtered[c].notna().any()]
default_params = [p for p in ["phi2", "lef", "npqt", "spad"] if p in available_params]

if not available_params:
    st.warning("Non ho trovato parametri numerici riconosciuti. Controlla il raw JSON nel debug.")
else:
    selected_params = st.multiselect("Parametri", available_params, default=default_params or available_params[:1])
    group_by = st.selectbox("Raggruppa per", ["treatment", "experiment", "plant_id", "replicate", "source_file"], index=0)
    plot_type = st.radio("Tipo grafico", ["Box plot", "Barre media ± SD", "Scatter"], horizontal=True)

    for param in selected_params:
        plot_df = filtered.dropna(subset=[param]).copy()
        if plot_df.empty:
            continue
        st.markdown(f"#### {param}")
        if plot_type == "Box plot":
            fig = px.box(plot_df, x=group_by, y=param, points="all", color=group_by)
        elif plot_type == "Barre media ± SD":
            summary = plot_df.groupby(group_by, dropna=False)[param].agg(["mean", "std", "count"]).reset_index()
            fig = px.bar(summary, x=group_by, y="mean", error_y="std", text="count")
            fig.update_layout(yaxis_title=param, xaxis_title=group_by)
        else:
            x_axis = "timestamp" if "timestamp" in plot_df.columns else "id"
            fig = px.scatter(plot_df, x=x_axis, y=param, color=group_by, hover_data=visible_cols)
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Export")
export_cols = [c for c in filtered.columns if c != "raw_json"]
export_df = filtered[export_cols].copy()
csv_bytes = export_df.to_csv(index=False).encode("utf-8")

excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    export_df.to_excel(writer, index=False, sheet_name="measurements")
excel_bytes = excel_buffer.getvalue()

d1, d2 = st.columns(2)
d1.download_button("Scarica CSV filtrato", csv_bytes, "photosynq_studio_export.csv", "text/csv", use_container_width=True)
d2.download_button("Scarica Excel filtrato", excel_bytes, "photosynq_studio_export.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

with st.expander("Debug: raw JSON dell'ultima misura visualizzata"):
    if not filtered.empty:
        st.code(str(filtered.iloc[0].get("raw_json", "")), language="json")
