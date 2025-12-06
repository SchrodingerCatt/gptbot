import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import Chroma

# --- კონფიგურაცია ---
DATA_DIR = "Steam"  # საქაღალდე PDF ფაილებით (ეს უნდა ატვირთოთ GitHub-ზე ან გამოიყენოთ Render-ის File Storage-ი)
CHROMA_PATH = "chroma_db"  # ვექტორული ბაზის საქაღალდე

# ----------------------------------------------------------------------------------
# --- გასაღებების ჩატვირთვა ENVIRONMENT VARIABLES-იდან (უსაფრთხო) ---
#  ეს გასაღები Render-ზე უნდა შექმნათ: OPENAI_API_KEY
# ----------------------------------------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") 

# ----------------------------------------------------
# API გასაღების იძულებითი დაყენება
# LangChain-ისთვის საჭიროა, რომ ეს ცვლადი არსებობდეს გარემოში
# ----------------------------------------------------
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
# ----------------------------------------------------

def ingest_data():
    """
    კითხულობს PDF-ებს, ყოფს ტექსტს (chunking), ვექტორიზაციას უკეთებს და ინახავს ChromaDB-ში.
    """
    # 1. მონაცემების წაკითხვა (უცვლელი)
    print(f"--- 1. დაწყებულია მონაცემების წაკითხვა საქაღალდიდან: {DATA_DIR} ---")
    
    if not os.path.exists(DATA_DIR):
        print(f" შეცდომა: საქაღალდე '{DATA_DIR}' ვერ მოიძებნა. გთხოვთ, შეამოწმოთ მისამართი.")
        return

    try:
        loader = PyPDFDirectoryLoader(DATA_DIR)
        documents = loader.load()
    except Exception as e:
        print(f" შეცდომა დოკუმენტების წაკითხვისას: {e}")
        return

    if not documents:
        print(f" არცერთი დოკუმენტი არ მოიძებნა ინდექსირებისთვის საქაღალდეში: {DATA_DIR}.")
        return
        
    print(f" მოიძებნა {len(documents)} დოკუმენტი წასაკითხად.")

    # 2. ტექსტის დაყოფა (Chunking) (უცვლელი)
    print("--- 2. მიმდინარეობს ტექსტის ფრაგმენტებად დაყოფა (Chunking) ---")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    print(f"შექმნილია {len(texts)} ტექსტური ფრაგმენტი (chunk).")

    # 3. ვექტორიზაცია და შენახვა (ChromaDB)
    print("--- 3. მიმდინარეობს ვექტორიზაცია (Embedding) და შენახვა ChromaDB-ში ---")
    
    #  შემოწმება, რომ გასაღები ნამდვილად ჩაიტვირთა გარემოდან
    if not OPENAI_API_KEY:
         print(" ERROR: OpenAI API გასაღები ვერ მოიძებნა ვექტორიზაციისთვის. შეამოწმეთ Environment Variables.")
         return
         
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # ვექტორული ბაზის შექმნა და შენახვა
    Chroma.from_documents(
        texts,
        embeddings,
        persist_directory=CHROMA_PATH
    )
    
    print(f" ინდექსირება წარმატებით დასრულდა. ვექტორული ბაზა შენახულია: {CHROMA_PATH}")

if __name__ == "__main__":
    ingest_data()