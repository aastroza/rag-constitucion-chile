# Import the required libraries
import streamlit as st
from citation_engine import create_index, create_query_engine, get_final_response
from stream_handler import StreamHandler
import re

st.set_page_config(layout="wide")
padding_left = 5
percentage_width_main = 80
st.markdown(
        f"""<style>
        .appview-container .main .block-container {{
        max-width: {percentage_width_main}%;
        padding-left: {padding_left}rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

@st.cache_resource
def get_index_vigente(model_name):
    return create_index(documents_path = "data/documents/", persist_dir = "./citation", model_name=model_name)

@st.cache_resource
def get_index_propuesta(model_name):
    return create_index(documents_path = "data/documents_propuesta", persist_dir = "./citation_propuesta", model_name=model_name)

query_engine_vigente_gpt3 = create_query_engine(get_index_vigente(model_name='gpt-3.5-turbo'))
query_engine_propuesta_gpt3 = create_query_engine(get_index_propuesta(model_name='gpt-3.5-turbo'))

query_engine_vigente_gpt4 = create_query_engine(get_index_vigente(model_name='gpt-4'))
query_engine_propuesta_gpt4 = create_query_engine(get_index_propuesta(model_name='gpt-4'))


def stream_llamaindex_response(container, response):
    result = ""
    for text in response.response_gen:
        result += text
        container.markdown(result)
    return result


# Set the title of the Streamlit application
st.title("Compara las Constituciones de Chile")

option = st.selectbox(
    'Selecciona el modelo de lenguaje que quieres usar',
    ('gpt-4', 'gpt-3.5-turbo'))

prompt = st.text_input("Ingresa un tema de tu interés, te contaremos que dice cada Constitución al respecto, luego te comentaremos sus similitudes y diferencias.", value='Las atribuciones del Banco Central')

if st.button("Consultar"):

    col1, col2 = st.columns(2)
    
    #with st.spinner('Espera unos segundos, estamos procesando tu consulta...'):

    if option == 'gpt-4':
        response_vigente = query_engine_vigente_gpt4.query(prompt)
    else:
        response_vigente = query_engine_vigente_gpt3.query(prompt)
    with col1:
        st.subheader("Constitución Actual")
        response_vigente_final = stream_llamaindex_response(st.empty(), response_vigente)
        sources_vigente_idx = set(re.findall(r'[\d]', response_vigente_final))
        if len(sources_vigente_idx) > 0:
            st.subheader("Fuentes")
            for idx in sources_vigente_idx:
                node = response_vigente.source_nodes[int(idx)-1]
                [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
                st.markdown(f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n')

    if option == 'gpt-4':
        response_propuesta = query_engine_propuesta_gpt4.query(prompt)
    else:
        response_propuesta = query_engine_propuesta_gpt3.query(prompt)
    with col2:
        st.subheader("Constitución Propuesta")
        response_propuesta_final = stream_llamaindex_response(st.empty(), response_propuesta)
        sources_propuesta_idx = set(re.findall(r'[\d]', response_propuesta_final))
        if len(sources_propuesta_idx) > 0:
            st.subheader("Fuentes")
            for idx in sources_propuesta_idx:
                node = response_propuesta.source_nodes[int(idx)-1]
                [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
                st.markdown(f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n')

    if len(sources_vigente_idx) + len(sources_propuesta_idx) > 0:
        st.subheader("Comparación")
        st_callback = StreamHandler(st.empty(), display_method='markdown')

        if option == 'gpt-4':
            response_final = get_final_response(prompt, response_vigente_final,
                                            response_propuesta_final, st_callback, model_name='gpt-4')
        else:
            response_final = get_final_response(prompt, response_vigente_final,
                                            response_propuesta_final, st_callback, model_name='gpt-3.5-turbo')