import os
# თუ ლოკალურად იყენებთ, შეგიძლიათ გამოიყენოთ python-dotenv
# from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import Chroma

# ----------------------------------------------------
# 📢 კონფიგურაცია და გასაღებების წაკითხვა გარემოდან
# ----------------------------------------------------
# load_dotenv() # ლოკალური ტესტირებისთვის საჭიროა, Render-ზე - არა.

# 🔑 გასაღები წაიკითხება გარემოს ცვლადებიდან (Render-დან ან ლოკალური .env-დან)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 

# --- RAG კონფიგურაცია ---
DATA_DIR = "Steam"  # საქაღალდე PDF ფაილებით
CHROMA_PATH = "chroma_db"  # ვექტორული ბაზის საქაღალდე

# API გასაღების დაყენება LangChain-ის გამოსაყენებლად
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
else:
    print("❌ ERROR: OPENAI_API_KEY ვერ იქნა ნაპოვნი გარემოს ცვლადებში. ინდექსირება ვერ შესრულდება.")
    # უბრალოდ გაგრძელება შეცდომით, თუ გასაღები აკლია

def ingest_data():
    """
    კითხულობს PDF-ებს, ყოფს ტექსტს (chunking), ვექტორიზაციას უკეთებს და ინახავს ChromaDB-ში.
    """
    if not OPENAI_API_KEY:
        print("❌ ERROR: ვექტორიზაციისთვის საჭიროა OPENAI_API_KEY. ოპერაცია შეჩერებულია.")
        return
        
    # 1. მონაცემების წაკითხვა
    print(f"--- 1. დაწყებულია მონაცემების წაკითხვა საქაღალდიდან: {DATA_DIR} ---")
    
    if not os.path.exists(DATA_DIR):
        print(f"❌ შეცდომა: საქაღალდე '{DATA_DIR}' ვერ მოიძებნა.")
        return

    try:
        loader = PyPDFDirectoryLoader(DATA_DIR)
        documents = loader.load()
    except Exception as e:
        print(f"❌ შეცდომა დოკუმენტების წაკითხვისას: {e}")
        return

    if not documents:
        print(f"⚠️ არცერთი დოკუმენტი არ მოიძებნა ინდექსირებისთვის საქაღალდეში: {DATA_DIR}.")
        return
        
    print(f"✅ მოიძებნა {len(documents)} დოკუმენტი წასაკითხად.")

    # 2. ტექსტის დაყოფა (Chunking)
    print("--- 2. მიმდინარეობს ტექსტის ფრაგმენტებად დაყოფა (Chunking) ---")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    print(f"✅ შექმნილია {len(texts)} ტექსტური ფრაგმენტი (chunk).")

    # 3. ვექტორიზაცია და შენახვა (ChromaDB)
    print("--- 3. მიმდინარეობს ვექტორიზაცია (Embedding) და შენახვა ChromaDB-ში ---")
    
    # 📢 LangChain ავტომატურად იყენებს os.environ["OPENAI_API_KEY"]-ს
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # ChromaDB-ის შექმნა და შენახვა
    Chroma.from_documents(
        texts,
        embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print(f"✅ ინდექსირება წარმატებით დასრულდა. ვექტორული ბაზა შენახულია: {CHROMA_PATH}")

if __name__ == "__main__":
    ingest_data()
