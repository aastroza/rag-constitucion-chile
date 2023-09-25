import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
#from langchain.llms import OpenAI
from llama_index.langchain_helpers.text_splitter import SentenceSplitter
from llama_index.node_parser.simple import SimpleNodeParser
from llama_index.query_engine import CitationQueryEngine
from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    LLMPredictor,
    ServiceContext,
)
from llama_index.llms import OpenAI
from llama_index.chat_engine import SimpleChatEngine
from dotenv import load_dotenv
import openai

OPENAI_MODEL = 'gpt-4'

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]

def create_index(documents_path = "data/documents/", persist_dir = "./citation", ):
    text_splitter = SentenceSplitter(separator=";\n", chunk_size=1024,
                                    chunk_overlap=0)
    node_parser = SimpleNodeParser(text_splitter=text_splitter)
    service_context = ServiceContext.from_defaults(
    llm_predictor=LLMPredictor(
        llm=ChatOpenAI(model_name=OPENAI_MODEL, temperature=0,
                                              streaming=True)),
        node_parser=node_parser
    )

    documents = SimpleDirectoryReader(documents_path).load_data()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    index.storage_context.persist(persist_dir=persist_dir)
    return index

def create_query_engine(index):
    text_splitter = SentenceSplitter(separator=";\n", chunk_size=1024,
                                    chunk_overlap=0)
    query_engine = CitationQueryEngine.from_args(
        index,
        text_splitter=text_splitter,
        similarity_top_k=3,
        streaming=True,
    )

    return query_engine


def get_final_response(query, response_vigente, response_propuesta, callback):
    template = """
            You are a Constitutional Lawyer. You are asked to give a brief response about 
            the diferences of two constitutions about this topic: {query}.

            The first constitution is the current one, and the second one is a proposed one.
            Always refer to the first constitution as Constitución Actual and the second one as Constitución Propuesta.

            The first constitution says the following about the topic: {first_response}.
            The second constitution says the following about the topic: {second_response}.

            Please detail the differences between the two constitutions about this topic.
            Please be concise and respond in spanish.
            
           """
    prompt = PromptTemplate(template=template, input_variables=["query", "first_response", "second_response"])
    llm_chain = LLMChain(prompt=prompt, llm=ChatOpenAI(model_name=OPENAI_MODEL, temperature=0, streaming=True, callbacks=[callback]))

    final_response = llm_chain.predict(query=query, first_response=response_vigente,
                                       second_response=response_propuesta)

    return final_response

def stream_llamaindex_response(response):
    result = ""
    for text in response.response_gen:
        result += text
    return result

def get_response(query_engine, prompt):

    response = query_engine.query(prompt)

    #response_final = stream_llamaindex_response(response)

    # sources = []
    # sources_idx = set(re.findall(r'[\d]', response))
    # if len(sources_idx) > 0:
    #     for idx in sources_idx:
    #         node = response.source_nodes[int(idx)-1]
    #         [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
    #         sources.append(f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n')

    result = {
        "question": prompt,
        #"sources": sources,
        "answer": response
    }

    return result

def get_final_response_llama_index(query, first_response, second_response):
    template = f"""
            You are a Constitutional Lawyer. You are asked to give a brief response about 
            the diferences of two constitutions about this topic: {query}.

            The first constitution is the current one, and the second one is a proposed one.
            Always refer to the first constitution as Constitución Actual and the second one as Constitución Propuesta.

            The first constitution says the following about the topic: {first_response}.
            The second constitution says the following about the topic: {second_response}.

            Please detail the differences between the two constitutions about this topic.
            Please be concise and respond in spanish.
            
           """
    service_context = ServiceContext.from_defaults(llm=OpenAI(temperature=0.0, model=OPENAI_MODEL))
    chat_engine = SimpleChatEngine.from_defaults(service_context=service_context)
    final_response = chat_engine.stream_chat(template)
    return final_response