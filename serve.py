from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from modal import asgi_app, Secret, Image, Stub
from citation import query_engine_vigente, query_engine_propuesta, get_final_response
from dotenv import load_dotenv
load_dotenv()

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

@app.get("/ping")
async def ping():
    return "pong"

@app.post("/query")
def query(self, query: Query) -> Answer:
    use_oss_agent = self.router.predict([query.query])[0]
    agent = self.oss_agent if use_oss_agent else self.gpt_agent
    result = agent(query=query.query, num_chunks=self.num_chunks, stream=False)
    return Answer.parse_obj(result)

def produce_streaming_answer(self, result):
    for answer_piece in result["answer"]:
        yield answer_piece
    if result["sources"]:
        yield "\n\n**Sources:**\n"
        for source in result["sources"]:
            yield "* " + source + "\n"

@app.post("/stream")
def stream(self, query: Query) -> StreamingResponse:
    use_oss_agent = self.router.predict([query.query])[0]
    agent = self.oss_agent if use_oss_agent else self.gpt_agent
    result = agent(query=query.query, num_chunks=self.num_chunks, stream=True)
    return StreamingResponse(
        self.produce_streaming_answer(result), media_type="text/plain")

@stub.function(
    image=image,
    secret=Secret.from_name("discolab"),
    keep_warm=1,
)
@asgi_app()
def fastapi_stub():
    return app