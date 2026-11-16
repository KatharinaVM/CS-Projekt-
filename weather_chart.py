import pandas as pd
import streamlit as st


def show_temperature_chart(forecast):

    # Wetterdaten in DataFrame umwandeln
    df = pd.DataFrame(forecast)

    # Datum in Datumsformat umwandeln
    df["date"] = pd.to_datetime(df["date"])

    # Spalten umbenennen
    df = df.rename(columns={
        "temperature_max": "Maximaltemperatur (°C)",
        "temperature_min": "Minimaltemperatur (°C)"
    })

    # Diagramm anzeigen
    st.line_chart(
        df,
        x="date",
        y=[
            "Maximaltemperatur (°C)",
            "Minimaltemperatur (°C)"
        ],
        x_label="Datum",
        y_label="Temperatur (°C)"
    )
    