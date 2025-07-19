import streamlit as st
import pandas as pd
import re
import dateparser
from io import BytesIO

st.set_page_config(page_title="Extractor de Celulares y Fechas", layout="wide")
st.title("📄 Extracción de Celulares y Fechas desde Excel")

uploaded_file = st.file_uploader("Sube tu archivo Excel (.xlsx):", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.success("Archivo cargado exitosamente ✅")
    st.write("Primeras filas del archivo:")
    st.dataframe(df.head())

    if len(df.columns) < 28:
        st.error("❌ El archivo debe tener al menos 28 columnas (hasta la columna AB).")
    else:
        columna_A = df.columns[0]
        columna_D = df.columns[3]
        columna_I = df.columns[8]
        columna_AB = df.columns[27]  # AB = índice 27

        # Extraer celulares
        regex_celular = r"(3\d{2}[ -.]?\d{3}[ -.]?\d{4})"
        df['celular_extraído'] = df[columna_AB].astype(str).apply(
            lambda texto: re.findall(regex_celular, texto)[0] if re.findall(regex_celular, texto) else None
        )

        # Extraer fecha solicitada
        etiquetas_validas = [
            'fecha asignada', 'fecha de visita', 'fecha visita', 'fecha programada',
            'programada para', 'agendada para', 'agenda', 'día de la visita'
        ]

        patrones_fecha = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}\s+de\s+[a-záéíóúñ]+(?:\s+\d{4})?',
            r'[a-záéíóúñ]+\s+\d{1,2}(?:,\s*\d{4})?',
            r'\b\d{1,2}\b\s+[a-záéíóúñ]+'
        ]

        def extraer_fecha_relevante(texto):
            texto = str(texto).lower()
            for etiqueta in etiquetas_validas:
                if etiqueta in texto:
                    seccion = texto.split(etiqueta, 1)[-1][:50]
                    for patron in patrones_fecha:
                        match = re.search(patron, seccion)
                        if match:
                            fecha = dateparser.parse(match.group(0), languages=['es'])
                            if fecha:
                                return fecha.date()
            return None

        df['fecha_solicitada'] = df[columna_AB].apply(extraer_fecha_relevante)

        # Mostrar resumen
        sin_fecha = df['fecha_solicitada'].isna().sum()
        con_fecha = df['fecha_solicitada'].notna().sum()

        st.info(f"Registros con fecha solicitada: {con_fecha}")
        st.warning(f"Registros SIN fecha solicitada: {sin_fecha}")

        # Mostrar y descargar archivo final
        df_exportar = df[[columna_A, columna_D, columna_I, columna_AB, 'celular_extraído', 'fecha_solicitada']].copy()
        df_exportar.columns = ['ID', 'Nombre', 'Ciudad', 'Observación', 'Celular', 'Fecha Solicitada']

        st.subheader("Vista previa del resultado:")
        st.dataframe(df_exportar.head(10))

        # Preparar para descarga
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_exportar.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Descargar archivo procesado",
            data=output,
            file_name="resumen_contactos_streamlit.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
