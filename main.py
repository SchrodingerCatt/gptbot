import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
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
    print("FATAL: OPENAI_API_KEY გარემოს ცვლადი ვერ მოიძებნა!")

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
        print(f"პერსონის ტექსტი წარმატებით ჩაიტვირთა prompt.pdf-დან. სიგრძე: {sum(len(doc.page_content) for doc in documents)} სიმბოლო.")
        
        # დოკუმენტის დაყოფა
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        # ემბედინგების ინიციალიზაცია
        print(">>> RAG სისტემის ინიციალიზაცია (OpenAI)...")
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # ვექტორული ბაზის შექმნა და შენახვა
        vector_store = Chroma.from_documents(texts, embeddings, persist_directory="chroma_db")
        vector_store.persist()
        
        # RAG Retriever-ის ინიციალიზაცია
        print(" RAG Retriever წარმატებით ჩაიტვირთა chroma_db-დან.")
        
        # LLM-ის ინიციალიზაცია
        llm = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
        
        # RetrievalQA Chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )
        print(" RAG Chain წარმატებით შეიქმნა.")

    except Exception as e:
        print(f"!!! RAG სისტემის ინიციალიზაციის შეცდომა: {e}")
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

# 🛑 ავტორიზაცია მოხსნილია, რადგან ინტერფეისი და API ერთსა და იმავე დომენზეა.
@app.post("/process_query", response_model=ChatbotResponse, tags=["Public"])
async def process_query(request_data: ChatbotRequest):
    if not rag_chain:
        # თუ RAG სისტემა ვერ ჩაიტვირთა, დაბრუნდება 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RAG სისტემა ინიციალიზაციის ფაზაშია ან ვერ მოხერხდა მისი ჩატვირთვა.",
        )

    try:
        # RAG ქოლის გაშვება
        result = rag_chain.invoke({"query": request_data.prompt})
        ai_response = result.get('result', "პასუხი ვერ იქნა გენერირებული.")

        return ChatbotResponse(
            status="success",
            processed_prompt=f"თქვენი მოთხოვნა დამუშავებულია. სიგრძე: {len(request_data.prompt)}.",
            ai_response=ai_response,
            result_data={},
        )
    except Exception as e:
        print(f"შეცდომა RAG chain-ის გაშვებისას: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"მოხდა შიდა სერვერული შეცდომა: {str(e)}",
        )

# სტატიკური ფაილების მომსახურება (HTML, CSS, JS)
# ეს არის კრიტიკული ნაწილი, რომელიც უზრუნველყოფს ინტერფეისის ჩატვირთვას.
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# -------------------------------------------------------------
# 4. Uvicorn-ის გაშვება (ლოკალური ტესტირებისთვის)
# -------------------------------------------------------------

if __name__ == "__main__":
    # Render იყენებს Start Command-ს, ამიტომ ეს ნაწილი მხოლოდ ლოკალურად იმუშავებს.
    port = int(os.getenv("PORT", 8040))
    uvicorn.run(app, host="0.0.0.0", port=port)
