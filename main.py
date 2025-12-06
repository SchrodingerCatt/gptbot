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

# 📢 აუცილებელი იმპორტი სტატიკური ფაილებისთვის
from fastapi.staticfiles import StaticFiles 

# LangChain-ის იმპორტები
try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma 
    from langchain_core.documents import Document
    RAG_TOOLS_AVAILABLE = True
except ImportError:
    RAG_TOOLS_AVAILABLE = False

# ----------------------------------------------------------------------------------
# --- კონფიგურაცია: გასაღებების ჩატვირთვა ENVIRONMENT VARIABLES-იდან (უსაფრთხო) ---
# ----------------------------------------------------------------------------------
# Render-ზე უნდა შექმნათ ეს Environment Variables: OPENAI_API_KEY და LOCAL_API_KEY
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LOCAL_API_KEY = os.environ.get("LOCAL_API_KEY") 

# LangChain-ის გამოსაყენებლად გარემოს ცვლადის დაყენება
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY 

# მუდმივები
API_KEY_NAME = "X-API-Key"
OPENAI_MODEL_NAME = "gpt-4o-mini"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions" 
PERSONA_PDF_PATH = "prompt.pdf"
CHROMA_PATH = "chroma_db" 

global_rag_retriever: Optional[Chroma.as_retriever] = None

# --- ფუნქცია პერსონის PDF-დან ჩასატვირთად (უცვლელი) ---
def load_persona_from_pdf(file_path: str) -> str:
    """კითხულობს მთელ ტექსტს PDF ფაილიდან pypdf-ის გამოყენებით."""
    DEFAULT_PERSONA = "თქვენ ხართ სასარგებლო ასისტენტი, რომელიც პასუხობს ქართულ ენაზე."
    try:
        reader = PdfReader(file_path)
        text = "".join(page.extract_text() + "\n\n" for page in reader.pages if page.extract_text())
        
        if not text.strip():
            print(f" ERROR: PDF ფაილი '{file_path}' ცარიელია. გამოყენებულია დეფოლტური პერსონა.")
            return DEFAULT_PERSONA
            
        print(f"პერსონის ტექსტი წარმატებით ჩაიტვირთა {file_path}-დან. სიგრძე: {len(text.strip())} სიმბოლო.")
        return text.strip()
    except Exception as e:
        print(f" ERROR: პერსონის PDF-ის წაკითხვისას შეცდომა: {e}. გამოყენებულია დეფოლტური პერსონა.")
        return DEFAULT_PERSONA

CUSTOM_PERSONA_TEXT = load_persona_from_pdf(PERSONA_PDF_PATH)

# --- FastAPI აპლიკაციის ინიციალიზაცია ---
app = FastAPI(title="OpenAI RAG API", version="1.0 - Render Ready")

# --- Startup ლოგიკა: RAG ინიციალიზაცია (OPENAI_API_KEY-ს მოითხოვს) ---
@app.on_event("startup")
async def startup_event():
    global global_rag_retriever
    
    if not RAG_TOOLS_AVAILABLE:
        print("RAG ინიციალიზაცია გამოტოვებულია.")
        return
        
    print(">>> RAG სისტემის ინიციალიზაცია (OpenAI)...")
    
    if os.path.exists(CHROMA_PATH):
        try:
            # თუ გასაღები ვერ მოიძებნა, Embedding ფუნქცია ვერ იმუშავებს
            if not OPENAI_API_KEY:
                 print(" ERROR: OPENAI_API_KEY ვერ მოიძებნა. ChromaDB-ის ჩატვირთვა ვერ ხერხდება.")
                 return
                 
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            
            # ChromaDB-ის ჩატვირთვა
            vector_store = Chroma(
                persist_directory=CHROMA_PATH, 
                embedding_function=embeddings
            )
            global_rag_retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            print(f" RAG Retriever წარმატებით ჩაიტვირთა {CHROMA_PATH}-დან.")
        except Exception as e:
            print(f" ERROR: ChromaDB-ის ჩატვირთვა ვერ მოხერხდა: {e}.")
    else:
        print(f" WARNING: ვექტორული ბაზა {CHROMA_PATH} ვერ მოიძებნა. RAG არააქტიურია. (Render-ზე ეს ნიშნავს, რომ ინდექსირება არ გაგიშვებიათ)")
        
# --- CORS Middleware (უცვლელი) ---
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
    #  შემოწმება, რომ ლოკალური გასაღები კონფიგურირებულია
    if not LOCAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="სერვერზე API გასაღები არ არის კონფიგურირებული. შეამოწმეთ Render-ის ცვლადები.",
        )
    
    # გასაღებების შედარება
    if not secrets.compare_digest(api_key, LOCAL_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="არასწორი API გასაღები",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key

# მონაცემთა მოდელები (უცვლელი)
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
    """უკავშირდება OpenAI API-ს, იყენებს RAG-ს კონტექსტის დასამატებლად."""
    #  შემოწმება, რომ OpenAI გასაღები არსებობს
    if not OPENAI_API_KEY:
        return "ERROR: OpenAI API გასაღები არ არის კონფიგურირებული სერვერზე."
    
    # 1. კონტექსტის ამოღება RAG-ის საშუალებით (უცვლელი)
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
        except Exception as e:
            rag_context = ""

    # 2. საბოლოო პრომპტის ფორმირება (უცვლელი)
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

    # API-ს გამოძახება ექსპონენციალური Backoff-ით (უცვლელი)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OPENAI_API_URL, 
                headers=headers, 
                data=json.dumps(payload),
                timeout=30 
            )
            
            # ... (შეცდომების დამუშავების ლოგიკა უცვლელია) ...
            if response.status_code >= 400:
                try:
                    error_detail = response.json()
                    return f"ERROR: OpenAI API-მ დააბრუნა {response.status_code} შეცდომა. დეტალები: {error_detail.get('error', {}).get('message', 'დეტალური შეტყობინება ვერ მიიღეს.')}"
                except json.JSONDecodeError:
                    return f"ERROR: OpenAI API-მ დააბრუნა {response.status_code} შეცდომა. პასუხი არ არის JSON-ში."

            response.raise_for_status() 
            result = response.json()
            
            if result.get('choices'):
                return result['choices'][0]['message']['content']
            
            return f"OpenAI API-მ დააბრუნა არასტანდარტული პასუხი."

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                return f"ERROR: OpenAI API-სთან დაკავშირება ვერ მოხერხდა. შეცდომა: {e}"
        except Exception as e:
            return f"ERROR: მოულოდნელი შეცდომა: {e}"
    
    return "ERROR: პასუხი ვერ იქნა გენერირებული."


@app.get("/")
def read_root():
    rag_status = "აქტიურია" if global_rag_retriever else "არააქტიურია (გაუშვით ingest.py)"
    return {"message": "API მუშაობს!", "RAG_Status": rag_status, "model": OPENAI_MODEL_NAME}

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

# =========================================================================
# 📢 !!! დამატებული სტატიკური ფაილების მომსახურება !!!
# =========================================================================
# ეს არის კრიტიკული ნაწილი, რომელიც უზრუნველყოფს, რომ Render-ზე შესვლისას 
# გამოჩნდეს index.html და მასთან დაკავშირებული CSS/JS ფაილები.
app.mount("/", StaticFiles(directory=".", html=True), name="static") 
# =========================================================================


if __name__ == "__main__":
    # ----------------------------------------------------------------------------------
    # Render-ზე ადაპტირება: 
    #   1. პორტი იტვირთება გარემოს ცვლადიდან (რომელსაც Render აწვდის)
    #   2. host დაყენებულია "0.0.0.0"-ზე
    # ----------------------------------------------------------------------------------
    port = int(os.environ.get("PORT", 8000)) 
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


            
           
