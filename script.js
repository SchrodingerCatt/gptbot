// script.js

// 🔑 !!! კონფიგურაცია !!!
// 🛑 აუცილებლად შეცვალეთ ეს მისამართი თქვენი Render სერვისის სრული URL-ით.
// მაგალითად: "https://gptbot-v1.1.onrender.com/process_query"
const API_URL = "https://your-render-domain-name.onrender.com/process_query"; 
const USER_ID = "test_user_001";
// -------------------------------------------------------------

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');
const apiKeyInput = document.getElementById('api-key-input'); 

// ფუნქცია შეტყობინების ჩატ-ბოქსში დასამატებლად
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    
    // 🛑 გარდაქმნის ყველაფერს უსაფრთხოდ ტექსტად
    messageDiv.textContent = String(text); 
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    const currentApiKey = apiKeyInput ? apiKeyInput.value.trim() : "";
    
    if (!currentApiKey) {
        statusMessage.textContent = '❌ გთხოვთ, შეიყვანოთ X-API-Key.';
        return;
    }

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
            method: 'POST', // 🔑 კრიტიკულია 404-ის თავიდან ასაცილებლად
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': currentApiKey 
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json(); 

        if (response.ok && data.status === 'success') {
            let aiResponseText = data.ai_response;
            
            if (typeof aiResponseText !== 'string' || !aiResponseText) {
                // თუ პასუხი ვერ მოიძებნა, გამოიტანეთ მთელი JSON ტექსტად
                aiResponseText = `ERROR: პასუხი ვერ იქნა ამოღებული. სრული პასუხი: ${JSON.stringify(data)}`;
            }
            
            // 🛑 სწორედ აქ ხდება მხოლოდ ტექსტის ჩვენება
            addMessage(aiResponseText, 'ai'); 
            statusMessage.textContent = '';

        } else {
            // 404, 401, ან სხვა შეცდომის დამუშავება
            const errorMsg = data.detail || data.ai_response || JSON.stringify(data, null, 2);
            addMessage(`API შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = `API შეცდომა: ${response.status}. შეამოწმეთ URL/გასაღები.`;
        }

    } catch (error) {
        console.error('ქსელური შეცდომა:', error);
        addMessage('შეცდომა: სერვერთან დაკავშირება ვერ ხერხდება. შეამოწმეთ URL.', 'ai');
        statusMessage.textContent = 'შეცდომა: სერვერი მიუწვდომელია.';
    } finally {
        sendButton.disabled = false;
    }
}

sendButton.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
