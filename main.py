import os
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from fastapi.staticfiles import StaticFiles

# -------------------------------------------------------------
# 1. OpenAI API გასაღების შემოწმება
# -------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    # ლოგირება, თუ გასაღები არ არის ნაპოვნი
    print("FATAL: OPENAI_API_KEY environment variable not found!")

# -------------------------------------------------------------
# 2. RAG სისტემის ინიციალიზაცია
# -------------------------------------------------------------

vector_store = None
rag_chain = None

def init_rag_system():
    global vector_store, rag_chain
    try:
        # ტექსტის ჩატვირთვა PDF-დან
        loader = PyPDFLoader("prompt.pdf")
        documents = loader.load()
        print(f"Text successfully loaded from prompt.pdf. Total length: {sum(len(doc.page_content) for doc in documents)} characters.")
        
        # დოკუმენტის დაყოფა
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        # ემბედინგების ინიციალიზაცია
        print(">>> Initializing RAG system (OpenAI)...")
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # ვექტორული ბაზის შექმნა და შენახვა
        # NOTE: Make sure 'chroma_db' directory is not uploaded to GitHub or is ignored.
        vector_store = Chroma.from_documents(texts, embeddings, persist_directory="chroma_db")
        vector_store.persist()
        
        # RAG Retriever-ის ინიციალიზაცია
        print(" RAG Retriever successfully loaded from chroma_db.")
        
        # LLM-ის ინიციალიზაცია
        llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        
        # RetrievalQA Chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )
        print(" RAG Chain successfully created.")

    except Exception as e:
        print(f"!!! RAG System Initialization Error: {e}")
        rag_chain = None # თუ ინიციალიზაცია ვერ მოხერხდა

# -------------------------------------------------------------
# 3. FastAPI აპლიკაცია და როუტები
# -------------------------------------------------------------

app = FastAPI(title="GPT-RAG Chatbot API")

# აპლიკაციის დაწყებისას RAG სისტემის ინიციალიზაცია
@app.on_event("startup")
async def startup_event():
    init_rag_system()

# მონაცემთა მოდელები
class ChatbotRequest(BaseModel):
    prompt: str
    user_id: str

class ChatbotResponse(BaseModel):
    status: str
    processed_prompt: str
    ai_response: str
    result_data: dict

# 🛑 Authentication removed for simplicity and deployment on the same domain
@app.post("/process_query", response_model=ChatbotResponse, tags=["Public"])
async def process_query(request_data: ChatbotRequest):
    if not rag_chain:
        # If RAG system failed to load, return 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAG system is still initializing or failed to load.",
        )

    try:
        # Run RAG call
        result = rag_chain.invoke({"query": request_data.prompt})
        ai_response = result.get('result', "Response could not be generated.")

        return ChatbotResponse(
            status="success",
            processed_prompt=f"Your query processed. Length: {len(request_data.prompt)}.",
            ai_response=ai_response,
            result_data={},
        )
    except Exception as e:
        print(f"Error running RAG chain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal server error occurred: {str(e)}",
        )

# Static files serving (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# -------------------------------------------------------------
# 4. Uvicorn run (for local testing, Render uses Start Command)
# -------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8040))
    uvicorn.run(app, host="0.0.0.0", port=port)
