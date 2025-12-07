# main.py

import os
import requests
import json
import time
import secrets
# ... (დანარჩენი იმპორტები)

# 🔑 გასაღებების წაკითხვა გარემოს ცვლადებიდან (უსაფრთხოება!)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY") 

# ... (კოდის შუა ნაწილი უცვლელია)

if __name__ == "__main__":
    # 📢 Render იყენებს PORT გარემოს ცვლადს, ლოკალურად 8040
    PORT = int(os.getenv("PORT", 8040))
    print(f"🚀 აპლიკაცია იშვება: http://0.0.0.0:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
