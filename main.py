import os
import requests
import json
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pypdf import PdfReader
from typing import Optional

# დამატებული იმპორტები სტატიკური ფაილებისთვის
from fastapi.responses import HTMLResponse
# 💡 საჭიროა ფაილების უსაფრთხოდ წასაკითხად ნებისმიერ გარემოში
from pathlib import Path

# 🚀 .env ფაილის ჩატვირთვა
from dotenv import load_dotenv
load_dotenv()

# 🔑 გასაღებების წაკითხვა გარემოს ცვლადებიდან
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- RAG ინსტრუმენტების იმპორტი ---
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
except Exception as e:
    print(f"❌ WARNING: RAG ბიბლიოთეკების იმპორტის შეცდომაა: {e}. RAG ფუნქციები გამორთულია.")

# --- კონფიგურაცია ---
OPENAI_MODEL_NAME = "gpt-4o-mini"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
PERSONA_PDF_PATH = "prompt.pdf"
CHROMA_PATH = "chroma_db"

global_rag_retriever: Optional[Chroma.as_retriever] = None

# --- ფუნქცია პერსონის PDF-დან ჩასატვირთად ---
def load_persona_from_pdf(file_path: str) -> str:
    # 💡 იყენებს Path-ს უსაფრთხოებისათვის
    DEFAULT_PERSONA = "თქვენ ხართ სასარგებლო ასისტენტი, რომელიც პასუხობს ქართულ ენაზე."
    
    # ფაილის აბსოლუტური გზა
    base_dir = Path(__file__).parent
    full_path = base_dir / file_path
    
    try:
        reader = PdfReader(full_path)
        text = "".join(page.extract_text() + "\n\n" for page in reader.pages if page.extract_text())
        if not text.strip():
            print(f"❌ ERROR: PDF ფაილი '{file_path}' ცარიელია. გამოყენებულია დეფოლტური პერსონა.")
            return DEFAULT_PERSONA
        print(f"✅ პერსონის ტექსტი წარმატებით ჩაიტვირთა {file_path}-დან. სიგრძე: {len(text.strip())} სიმბოლო.")
        return text.strip()
    except Exception as e:
        print(f"❌ ERROR: პერსონის PDF-ის წაკითხვისას შეცდომა: {e}. გამოყენებულია დეფოლტური პერსონა.")
        return DEFAULT_PERSONA

CUSTOM_PERSONA_TEXT = load_persona_from_pdf(PERSONA_PDF_PATH)

# --- FastAPI აპლიკაციის ინიციალიზაცია ---
app = FastAPI(title="OpenAI RAG API", version="1.0 - GPT Activated")

# --- Startup ლოგიკა: RAG ინიციალიზაცია ---
@app.on_event("startup")
async def startup_event():
    global global_rag_retriever

    if not RAG_TOOLS_AVAILABLE:
        print("RAG ინიციალიზაცია გამოტოვებულია.")
        return

    print(">>> RAG სისტემის ინიციალიზაცია (OpenAI)...")
    
    # 💡 იყენებს Path-ს ChromaDB-ის აბსოლუტური გზის მისაღებად
    base_dir = Path(__file__).parent
    full_chroma_path = base_dir / CHROMA_PATH

    if full_chroma_path.exists():
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vector_store = Chroma(
                persist_directory=str(full_chroma_path),
                embedding_function=embeddings
            )
            global_rag_retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            print(f"✅ RAG Retriever წარმატებით ჩაიტვირთა {CHROMA_PATH}-დან.")
        except Exception as e:
            print(f"❌ ERROR: ChromaDB-ის ჩატვირთვა ვერ მოხერხდა: {e}. შეამოწმეთ OPENAI_API_KEY.")
    else:
        print(f"⚠️ WARNING: ვექტორული ბაზა {CHROMA_PATH} ვერ მოიძებნა. RAG არააქტიურია. გაუშვით 'python ingest.py' და ატვირთეთ chroma_db.")

# --- CORS Middleware დამატება ---
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 💡 ROOT ენდფოინტი, რომელიც index.html-ს ემსახურება ---
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_index():
    """აბრუნებს index.html-ს მთავარ მისამართზე, იყენებს უსაფრთხო გზას."""
    # 💡 იყენებს Path-ს index.html-ის აბსოლუტური გზის მისაღებად
    base_dir = Path(__file__).parent
    file_path = base_dir / "index.html"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>Error 500: index.html not found!</h1>", status_code=500)
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading index.html: {e}</h1>", status_code=500)


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
    # (ფუნქციის შიგთავსი რჩება იგივე)
    if not OPENAI_API_KEY:
        return "ERROR: OPENAI API გასაღები აკლია გარემოს ცვლადებში."

    rag_context = ""
    is_rag_active = global_rag_retriever is not None

    if is_rag_active:
        try:
            docs: list[Document] = global_rag_retriever.invoke(prompt)
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
                print(f"⚠️ Warning: OpenAI API-სთან დაკავშირება ვერ მოხერხდა. ცდა {attempt + 1}/{max_retries}. ლოდინი {wait_time} წმ.")
                time.sleep(wait_time)
            else:
                return f"ERROR: OpenAI API-სთან დაკავშირება ვერ მოხერხდა. შეცდომა: {e}"
        except Exception as e:
            return f"ERROR: მოულოდნელი შეცდომა: {e}"

    return "ERROR: პასუხი ვერ იქნა გენერირებული."


@app.post("/process_query", response_model=ChatbotResponse, tags=["Secured"])
async def process_query(
    request_data: ChatbotRequest,
):
    # (ფუნქციის შიგთავსი რჩება იგივე)
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
