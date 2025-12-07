import os
import requests
import json
import time
import secrets
from fastapi import FastAPI, Header, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pypdf import PdfReader 
from typing import Optional

# 📢 გასაღებების წაკითხვა გარემოს ცვლადებიდან
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY") 

# --- RAG ინსტრუმენტების იმპორტი (LangChain/OpenAI-სთვის) ---
RAG_TOOLS_AVAILABLE = False
try:
    if OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY 
        
        from langchain_openai import OpenAIEmbeddings
        from langchain_community.vectorstores import Chroma 
        from langchain_core.documents import Document
        RAG_TOOLS_AVAILABLE = True
        print("✅ RAG ბიბლიოთეკები წარმატებით ჩაიტვირთა.")
    else:
        print("❌ WARNING: OPENAI_API_KEY ვერ იქნა ნაპოვნი. RAG ფუნქციები გამორთულია.")
except ImportError as e:
    print(f"❌ WARNING: RAG ბიბლიოთეკების იმპორტის შეცდომაა: {e}. RAG ფუნქციები გამორთულია.")

# --- კონფიგურაცია ---
API_KEY_NAME = "X-API-Key"
OPENAI_MODEL_NAME = "gpt-4o-mini"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
PERSONA_PDF_PATH = "prompt.pdf"
CHROMA_PATH = "chroma_db" 

global_rag_retriever: Optional[Chroma.as_retriever] = None

# --- ფუნქცია პერსონის PDF-დან ჩასატვირთად ---
def load_persona_from_pdf(file_path: str) -> str:
    """კითხულობს მთელ ტექსტს PDF ფაილიდან pypdf-ის გამოყენებით."""
    DEFAULT_PERSONA = "თქვენ ხართ სასარგებლო ასისტენტი, რომელიც პასუხობს ქართულ ენაზე."
    try:
        reader = PdfReader(file_path)
        text = "".join(page.extract_text() + "\n\n" for page in reader.pages if page.extract_text())
        
        if not text.strip():
            print(f"❌ ERROR: PDF ფაილი '{file_path}' ცარიელია.")
            return DEFAULT_PERSONA
            
        return text.strip()
    except Exception as e:
        print(f"❌ ERROR: პერსონის PDF-ის წაკითხვისას შეცდომა: {e}.")
        return DEFAULT_PERSONA

CUSTOM_PERSONA_TEXT = load_persona_from_pdf(PERSONA_PDF_PATH)

# --- FastAPI აპლიკაციის ინიციალიზაცია ---
app = FastAPI(title="OpenAI RAG API", version="1.0 - Secured")

# --- Startup ლოგიკა: RAG ინიციალიზაცია ---
@app.on_event("startup")
async def startup_event():
    global global_rag_retriever
    
    if not RAG_TOOLS_AVAILABLE:
        print("RAG ინიციალიზაცია გამოტოვებულია.")
        return
        
    print(">>> RAG სისტემის ინიციალიზაცია...")
    
    if os.path.exists(CHROMA_PATH):
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vector_store = Chroma(
                persist_directory=CHROMA_PATH, 
                embedding_function=embeddings
            )
            global_rag_retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            print(f"✅ RAG Retriever წარმატებით ჩაიტვირთა {CHROMA_PATH}-დან.")
        except Exception as e:
            print(f"❌ ERROR: ChromaDB-ის ჩატვირთვა ვერ მოხერხდა: {e}")
    else:
        print(f"⚠️ WARNING: ვექტორული ბაზა {CHROMA_PATH} ვერ მოიძებნა. RAG არააქტიურია.")
        
# --- CORS Middleware დამატება ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------------------------------

# (Dependency) ავტორიზაციის ფუნქცია
async def verify_api_key(api_key: str = Header(..., alias=API_KEY_NAME)):
    if not LOCAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="სერვერის კონფიგურაციის შეცდომა: ავტორიზაციის გასაღები აკლია (Render ENV).",
        )
    
    if not secrets.compare_digest(api_key, LOCAL_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="არასწორი API გასაღები",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key

# მონაცემთა მოდელები
class ChatbotRequest(BaseModel):
    prompt: str
    user_id: str

class ChatbotResponse(BaseModel):
    status: str
    processed_prompt: str
    ai_response: str
    result_data: dict

# --- OpenAI API-ს გამოძახება (RAG ლოგიკით) ---
def generate_openai_content(prompt: str) -> str:
    if not OPENAI_API_KEY:
        return "ERROR: OPENAI API გასაღები აკლია."
    
    rag_context = ""
    is_rag_active = global_rag_retriever is not None
    
    if is_rag_active:
        try:
            docs: list[Document] = global_rag_retriever.get_relevant_documents(prompt)
            context_text = "\n---\n".join([doc.page_content for doc in docs])
            
            rag_context = (
                f"გამოიყენეთ შემდეგი კონტექსტი პასუხის გასაცემად. თუ პასუხი მოცემულ კონტექსტში არ არის, "
                f"მაშინ უპასუხეთ ზოგადი ცოდნის საფუძველზე: \n\n--- DOCUMENTS ---\n{context_text}\n---"
            )
            print(f"🔎 RAG-მა იპოვა {len(docs)} რელევანტური ფრაგმენტი.")
            
        except Exception as e:
            print(f"❌ ERROR: RAG Retrieval-ის შეცდომა: {e}")
            rag_context = ""

    final_user_prompt = f"{rag_context}\n\nმომხმარებლის შეკითხვა: {prompt}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}" 
    }
    
    payload = {
        "model": OPENAI_MODEL_NAME,
        "messages": [
            {"role": "system", "content": f"{CUSTOM_PERSONA_TEXT}"},
            {"role": "user", "content": final_user_prompt}
        ]
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OPENAI_API_URL, 
                headers=headers, 
                data=json.dumps(payload),
                timeout=30  
            )
            
            if response.status_code >= 400:
                error_detail = response.json()
                return f"ERROR: OpenAI API-მ დააბრუნა {response.status_code} შეცდომა. დეტალები: {error_detail.get('error', {}).get('message', 'დეტალური შეტყობინება ვერ მიიღეს.')}"

            response.raise_for_status() 
            result = response.json()
            
            if result.get('choices'):
                return result['choices'][0]['message']['content']
            
            return f"OpenAI API-მ დააბრუნა არასტანდარტული პასუხი."

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️ Warning: OpenAI API-სთან დაკავშირება ვერ მოხერხდა. ლოდინი {wait_time} წმ.")
                time.sleep(wait_time)
            else:
                return f"ERROR: OpenAI API-სთან დაკავშირება ვერ მოხერხდა. შეცდომა: {e}"
        except Exception as e:
            return f"ERROR: მოულოდნელი შეცდომა: {e}"
    
    return "ERROR: პასუხი ვერ იქნა გენერირებული."

# --- API მარშრუტები ---

@app.get("/")
def read_root():
    rag_status = "აქტიურია" if global_rag_retriever else "არააქტიურია (გაუშვით ingest.py)"
    config_ok = "✅" if OPENAI_API_KEY and LOCAL_API_KEY else "❌ (API გასაღებები აკლია!)"
    return {"message": "API მუშაობს!", "Configuration_Status": config_ok, "RAG_Status": rag_status, "model": OPENAI_MODEL_NAME}

@app.post("/process_query", response_model=ChatbotResponse, tags=["Secured"])
async def process_query(
    request_data: ChatbotRequest,
    api_key: str = Depends(verify_api_key) 
):
    openai_response = generate_openai_content(request_data.prompt)
    
    response_data = {
        "user": request_data.user_id,
        "length": len(request_data.prompt),
        "is_rag_active": global_rag_retriever is not None,
        "openai_model": OPENAI_MODEL_NAME
    }
    
    return ChatbotResponse(
        status="success",
        processed_prompt=f"თქვენი მოთხოვნა დამუშავებულია. სიგრძე: {len(request_data.prompt)}.",
        ai_response=openai_response,
        result_data=response_data,
    )

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8040))
    print(f"🚀 აპლიკაცია იშვება: http://0.0.0.0:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
