import os
import uvicorn
from fastapi import FastAPI, HTTPException, status, Form
from pydantic import BaseModel
# ✅ სწორი იმპორტი: გამოიყენეთ langchain-chroma
from langchain_chroma import Chroma 
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from fastapi.staticfiles import StaticFiles

# -------------------------------------------------------------
# 1. OpenAI API Key Check
# -------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("FATAL: OPENAI_API_KEY environment variable not found!")

# -------------------------------------------------------------
# 2. RAG System Initialization
# -------------------------------------------------------------

vector_store = None
rag_chain = None

def init_rag_system():
    global vector_store, rag_chain
    try:
        # Load text from PDF
        loader = PyPDFLoader("prompt.pdf")
        documents = loader.load()
        print(f"პერსონის ტექსტი წარმატებით ჩაიტვირთა prompt.pdf-დან. სიგრძე: {sum(len(doc.page_content) for doc in documents)} სიმბოლო.")
        
        # Split document
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        # Initialize embeddings
        print(">>> RAG სისტემის ინიციალიზაცია (OpenAI)...")
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # Create and persist vector store
        vector_store = Chroma.from_documents(texts, embeddings, persist_directory="chroma_db")
        vector_store.persist()
        
        # Initialize RAG Retriever
        print("RAG Retriever წარმატებით ჩაიტვირთა chroma_db-დან.")
        
        # Initialize LLM
        llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        
        # RetrievalQA Chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )
        print("RAG Chain წარმატებით შეიქმნა.")

    except Exception as e:
        print(f"!!! RAG სისტემის ინიციალიზაციის შეცდომა: {e}")
        rag_chain = None 

# -------------------------------------------------------------
# 3. FastAPI Application and Routes
# -------------------------------------------------------------

app = FastAPI(title="GPT-RAG Chatbot API")

# Initialize RAG system on application startup
@app.on_event("startup")
async def startup_event():
    init_rag_system()

# Data Models (ეს მხოლოდ პასუხის მოდელია)
class ChatbotResponse(BaseModel):
    status: str
    processed_prompt: str
    ai_response: str
    result_data: dict

# *** განახლებული ენდპოინტი: /api/query იღებს Form Data-ს ***
@app.post("/api/query", response_model=ChatbotResponse, tags=["Public"])
async def process_query(
    prompt: str = Form(...), # მიიღებს prompt-ს Form Data-დან
    user_id: str = Form(...)  # მიიღებს user_id-ს Form Data-დან
):
    
    # Base64 დეკოდირება მოხსნილია, ვიღებთ წმინდა ტექსტს
    decoded_prompt = prompt 

    if not rag_chain:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAG სისტემა ინიციალიზაციის ფაზაშია ან ვერ ჩაიტვირთა.",
        )

    try:
        # გამოიყენეთ დაუშიფრავი ტექსტი RAG ჯაჭვში
        result = rag_chain.invoke({"query": decoded_prompt})
        ai_response = result.get('result', "პასუხის გენერირება ვერ მოხერხდა.")

        return ChatbotResponse(
            status="success",
            processed_prompt=f"თქვენი შეკითხვა დამუშავდა. სიგრძე: {len(decoded_prompt)}.",
            ai_response=ai_response,
            result_data={},
        )
    except Exception as e:
        print(f"Error running RAG chain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"შიდა სერვერის შეცდომა: {str(e)}",
        )

# Static files serving
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# -------------------------------------------------------------
# 4. Uvicorn run
# -------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8040))
    uvicorn.run(app, host="0.0.0.0", port=port)
