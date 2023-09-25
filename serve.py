from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from modal import asgi_app, Secret, Image, Stub, Mount
from llm import create_index, get_response, create_query_engine, get_final_response_llama_index
from dotenv import load_dotenv
from pathlib import Path
import re


load_dotenv()

static_path = Path(__file__).with_name("static").resolve()

# Creates the FastAPI web server.
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image = (
    Image.debian_slim()
    .pip_install(
        "openai",
        "llama-index",
        "langchain",
        "python-dotenv",
        "nltk"
    )
)
stub = Stub("rag-discolab")

class Query(BaseModel):
    query: str

class Answer(BaseModel):
    question: str
    answer_doc1: str
    sources_doc1: List[str]
    answer_doc2: str
    sources_doc2: List[str]
    answer: str
    llm: str


def get_index_vigente():
    return create_index(documents_path = str(static_path)+"/data/documents/", persist_dir = str(static_path)+"/citation")

def get_index_propuesta():
    return create_index(documents_path = str(static_path)+"/data/documents_propuesta", persist_dir = str(static_path)+"/citation_propuesta")

query_engine_vigente = create_query_engine(get_index_vigente())
query_engine_propuesta = create_query_engine(get_index_propuesta())

def stream_llamaindex_response(response):
    result = ""
    for text in response.response_gen:
        result += text
    return result

@app.get("/ping")
async def ping():
    return "pong"


def produce_streaming_answer(qe_result1, qe_result2, prompt):
    
    yield "\n\n**[DOCUMENT 1]**\n"
    answer = []
    for answer_piece in qe_result1["answer"].response_gen:
        answer.append(answer_piece)
        yield answer_piece
    response_final_1 = "".join(answer)

    yield "\n\n**[SOURCES DOCUMENT 1]**\n"
    sources_idx_1 = set(re.findall(r'[\d]', response_final_1))
    if len(sources_idx_1) > 0:
        for idx in sources_idx_1:
            node = qe_result1["answer"].source_nodes[int(idx)-1]
            [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
            yield f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n'

    yield "\n\n**[DOCUMENT 2]**\n"
    answer = []
    for answer_piece in qe_result2["answer"].response_gen:
        answer.append(answer_piece)
        yield answer_piece
    response_final_2 = "".join(answer)

    yield "\n\n**[SOURCES DOCUMENT 2]**\n"
    sources_idx_2 = set(re.findall(r'[\d]', response_final_2))
    if len(sources_idx_2) > 0:
        for idx in sources_idx_2:
            node = qe_result2["answer"].source_nodes[int(idx)-1]
            [source, capitulo, articulo] = node.node.get_text().split('\n', 3)[0:3]
            yield f'[{source.replace("Source ", "" ).replace(":", "")}] {capitulo}, {articulo}\n'
    
    if len(sources_idx_1) + len(sources_idx_2) > 0:
        yield "\n\n**[FINAL RESPONSE]**\n"
        response_final = get_final_response_llama_index(query=prompt, first_response=response_final_1, second_response=response_final_2)
        for answer_piece in response_final.response_gen:
            yield answer_piece

@app.post("/stream")
def stream(query: Query) -> StreamingResponse:
    print(query.query)
    result1 = get_response(query_engine_vigente, query.query)
    result2 = get_response(query_engine_propuesta, query.query)
    #print(result["answer"].source_nodes)
    return StreamingResponse(
        produce_streaming_answer(qe_result1 = result1, qe_result2 = result2, prompt=query.query), media_type="text/event-stream")

@stub.function(
    mounts=[Mount.from_local_dir(static_path, remote_path="/root/static")],
    image=image,
    secret=Secret.from_name("discolab"),
    keep_warm=1,
)
@asgi_app()
def fastapi_stub():
    app.mount("/static", StaticFiles(directory="/root/static", html=True))
    return app