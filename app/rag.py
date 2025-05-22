import os
from dotenv import load_dotenv
load_dotenv()

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

os.environ['HF_TOKEN']=os.getenv("HF_TOKEN")
embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model="Gemma2-9b-it",groq_api_key=groq_api_key)

system_prompt = (
    "Use the given context to answer the question. "
    "If you don't know the answer, say you don't know. "
    "Use three sentence maximum and keep the answer concise. "
    "Context: {context}"
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 2000,
    chunk_overlap = 200,
    length_function = len
)

vector_db  = None
qa_chain = None

def process_document(filepath:str,filename:str) -> dict:
    global vector_db,qa_chain

    loader = PyPDFLoader(filepath)
    pages = loader.load_and_split()

    chunks = text_splitter.split_documents(pages)

    if vector_db is None:
        vector_db = FAISS.from_documents(
            documents=chunks,
            embedding=embeddings,
        )
        vector_db.save_local("vector_store")
    else:
        vector_db.add_documents(chunks)
        vector_db.save_local("vector_store")
    
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    qa_chain = create_retrieval_chain(vector_db.as_retriever(), question_answer_chain)


    return {
        "filename":filename,
        "page_count":len(pages),
        "chunk_count":len(chunks)
    }

def query_rag(query:str):
    if qa_chain is None:
        return {"annswer":"No documents processed yet"}

    result = qa_chain.invoke({"input":query})

    return result['answer']
    