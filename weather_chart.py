import pandas as pd
import streamlit as st

def show_temperature_chart(forecast):

    df = pd.DataFrame(forecast)

    df["date"] = pd.to_datetime(df["date"])

    df = df.rename(columns={
        "temperature_max": "Maximum temperature (°C)",
        "temperature_min": "Minimum temperature (°C)"
    })

    st.line_chart(
        df,
        x="date",
        y=[
            "Maximum temperature (°C)",
            "Minimum temperature (°C)"
        ],
        x_label="Date",
        y_label="Temperature (°C)"
    )
