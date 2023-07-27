# Import the required libraries
import streamlit as st
from citation_engine import query_engine_vigente, query_engine_propuesta, get_final_response

#st.set_page_config(layout="wide")

# Set the title of the Streamlit application
st.title("Compara las Constituciones de Chile")
prompt = st.text_input("Ingresa un tema de tu interés, te contaremos que dice cada Constitución al respecto, luego te comentaremos sus similitudes y diferencias.", value='Las atribuciones del Banco Central')

if st.button("Consultar"):

    with st.spinner('Espera unos segundos, estamos procesando tu consulta...'):
        response_vigente = query_engine_vigente.query(prompt)
        response_propuesta = query_engine_propuesta.query(prompt)
        response_final = get_final_response(prompt, response_vigente, response_propuesta)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Constitución Actual")
            st.markdown(response_vigente)
            st.subheader("Fuentes")
            for node in response_vigente.source_nodes:
                [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
                st.markdown(f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n')

        with col2:
            st.subheader("Constitución Propuesta")
            st.markdown(response_propuesta)
            st.subheader("Fuentes")
            for node in response_propuesta.source_nodes:
                [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
                st.markdown(f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n')

        with col3:
            st.subheader("Comparación")
            st.markdown(response_final)