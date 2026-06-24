# PhotosynQ Studio v0.1

App locale Streamlit per organizzare e analizzare misure PhotosynQ/MultispeQ senza dipendere dal cloud.

## Installazione

```bash
pip install -r requirements.txt
```

## Avvio

```bash
streamlit run streamlit_app.py
```

## Cosa fa

- Importa JSON/CSV esportati da PhotosynQ
- Salva tutto in SQLite locale: `photosynq_studio.db`
- Aggiunge metadati: esperimento, trattamento, sample ID, pianta, replica, note
- Mostra tabella filtrabile
- Crea grafici per Phi2, LEF, NPQt, SPAD, PhiNPQ, PhiNO, qL, P700, ECS
- Esporta CSV/Excel
