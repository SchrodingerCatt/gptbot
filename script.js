const API_URL = "/process_query"; 

// 2. LOCAL_API_KEY: აქ ჩაწერეთ ზუსტად ის ლოკალური გასაღები, რომელიც Render-ზე გაქვთ LOCAL_API_KEY ცვლადში.
const PUBLIC_CLIENT_API_KEY = "აქ_ჩაწერეთ_თქვენი_LOCAL_API_KEY"; 

const USER_ID = "web_client";
// -------------------------------------------------------------

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');

// ფუნქცია შეტყობინების ჩატ-ბოქსში დასამატებლად
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    
    // ჩატის ბოქსის ბოლოში ჩასქროლვა
    chatBox.scrollTop = chatBox.scrollHeight;
}

// API-სთან კომუნიკაციის ფუნქცია
async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // 1. მომხმარებლის შეტყობინების დამატება
    addMessage(prompt, 'user');
    userInput.value = '';
    sendButton.disabled = true;
    statusMessage.textContent = 'პასუხის გენერაცია მიმდინარეობს...';

    const payload = {
        prompt: prompt,
        user_id: USER_ID
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 2. API Key-ს გაგზავნა ჰედერში
                'X-API-Key': PUBLIC_CLIENT_API_KEY 
            },
            body: JSON.stringify(payload)
        });

        // 📢 !!! კრიტიკული ცვლილება: შეცდომის სტატუსის დამუშავება !!!
        if (!response.ok) {
            // თუ HTTP სტატუსი არ არის 2xx (მაგ. 401, 404, 500)
            const errorText = await response.text();
            let errorData;
            try {
                errorData = JSON.parse(errorText);
            } catch (e) {
                // თუ პასუხი JSON ფორმატით არ დაბრუნდა (იშვიათია)
                throw new Error(`API შეცდომა: HTTP სტატუსი ${response.status}. პასუხი: ${errorText.substring(0, 100)}...`);
            }
            
            const detail = errorData.detail || `API შეცდომა: HTTP სტატუსი ${response.status}`;
            throw new Error(detail); // გადააგდებს შეცდომას catch ბლოკში
        }
        // 📢 !!! ცვლილების დასასრული !!!

        const data = await response.json();

        if (data.status === 'success') {
            // 3. წარმატებული პასუხის ჩვენება
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            // თუ API პასუხი წარმატებულია (HTTP 200), მაგრამ შიდა სტატუსი არაა 'success'
            const errorMsg = data.ai_response || 'პასუხის მიღებისას დაფიქსირდა შიდა შეცდომა.';
            addMessage(`შიდა შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = 'API შეცდომა: შიდა პასუხი ვერ იქნა მიღებული.';
        }

    } catch (error) {
        // 5. ქსელური ან HTTP შეცდომის ჩვენება
        console.error('შეცდომა:', error);
        
        let displayMessage = error.message || 'სერვერთან დაკავშირება ვერ ხერხდება.';
        
        // 401 შეცდომის შემთხვევაში კონკრეტული შეტყობინება
        if (displayMessage.includes("არასწორი API გასაღები")) {
             displayMessage = "არასწორი API გასაღები (401). გთხოვთ, შეამოწმოთ PUBLIC_CLIENT_API_KEY.";
        }
        
        addMessage(`შეცდომა: ${displayMessage}`, 'ai');
        statusMessage.textContent = 'API შეცდომა: მოთხოვნა ვერ შესრულდა.';
    } finally {
        sendButton.disabled = false;
    }
}

// ღილაკზე დაჭერით გაგზავნა
sendButton.addEventListener('click', sendMessage);

// Enter-ზე დაჭერით გაგზავნა
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
