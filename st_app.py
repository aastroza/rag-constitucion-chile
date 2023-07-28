# Import the required libraries
import streamlit as st
from citation_engine import create_index, create_query_engine, get_final_response
from stream_handler import StreamHandler


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
def get_index_vigente():
    return create_index(documents_path = "data/documents/", persist_dir = "./citation")

@st.cache_resource
def get_index_propuesta():
    return create_index(documents_path = "data/documents_propuesta", persist_dir = "./citation_propuesta")

query_engine_vigente = create_query_engine(get_index_vigente())

query_engine_propuesta = create_query_engine(get_index_propuesta())


def stream_llamaindex_response(container, response):
    result = ""
    for text in response.response_gen:
        result += text
        container.markdown(result)
    return result


# Set the title of the Streamlit application
st.title("Compara las Constituciones de Chile")
prompt = st.text_input("Ingresa un tema de tu interés, te contaremos que dice cada Constitución al respecto, luego te comentaremos sus similitudes y diferencias.", value='Las atribuciones del Banco Central')

if st.button("Consultar"):

    col1, col2 = st.columns(2)
    
    #with st.spinner('Espera unos segundos, estamos procesando tu consulta...'):
    response_vigente = query_engine_vigente.query(prompt)
    with col1:
        st.subheader("Constitución Actual")
        response_vigente_final = stream_llamaindex_response(st.empty(), response_vigente)
        st.subheader("Fuentes")
        for node in response_vigente.source_nodes:
            [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
            st.markdown(f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n')

    response_propuesta = query_engine_propuesta.query(prompt)
    with col2:
        st.subheader("Constitución Propuesta")
        response_propuesta_final = stream_llamaindex_response(st.empty(), response_propuesta)
        st.subheader("Fuentes")
        for node in response_propuesta.source_nodes:
            [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
            st.markdown(f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n')

    st.subheader("Comparación")
    st_callback = StreamHandler(st.empty(), display_method='markdown')
    response_final = get_final_response(prompt, response_vigente_final, response_propuesta_final, st_callback)    