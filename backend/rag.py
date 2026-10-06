import os
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
    load_index_from_storage,
)
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.tools import QueryEngineTool
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

KNOWLEDGE_DIR = ROOT / "knowledge"
PERSIST_DIR = ROOT / "storage"

SYSTEM_PROMPT = (
    "You are a friendly customer support assistant. "
    "Always search the knowledge_base tool before answering. "
    "Answer only from what the knowledge base returns, in clear, concise markdown. "
    "If the answer is not in the knowledge base, say you don't have that information "
    "and suggest contacting a human support agent."
)


def build_agent() -> AgentWorkflow:
    llm = HuggingFaceInferenceAPI(
        model_name="Qwen/Qwen2.5-Coder-32B-Instruct",
        token=os.getenv("HF_TOKEN"),
    )
    Settings.llm = llm
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    if PERSIST_DIR.exists():
        storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
        index = load_index_from_storage(storage_context)
    else:
        documents = SimpleDirectoryReader(
            input_dir=str(KNOWLEDGE_DIR), required_exts=[".md"], recursive=True
        ).load_data()
        index = VectorStoreIndex.from_documents(documents, show_progress=True)
        index.storage_context.persist(persist_dir=str(PERSIST_DIR))

    query_engine = index.as_query_engine(llm=llm, similarity_top_k=4, response_mode="compact")

    knowledge_tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="knowledge_base",
        description="Searches the support knowledge base. Use it for any customer question.",
    )

    return AgentWorkflow.from_tools_or_functions(
        [knowledge_tool], llm=llm, system_prompt=SYSTEM_PROMPT
    )