// 🔑 !!! კონფიგურაცია !!!
// Render-ზე დეპლოის შემდეგ, შეცვალეთ API_URL თქვენი Render სერვისის მისამართით:
// მაგ: const API_URL = "https://your-render-service.onrender.com/process_query";
const API_URL = "http://localhost:8040/process_query"; 
const USER_ID = "test_user_001";
// -------------------------------------------------------------

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');
const apiKeyInput = document.getElementById('api-key-input'); // 📢 API გასაღების ველი

// ფუნქცია შეტყობინების ჩატ-ბოქსში დასამატებლად
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    messageDiv.textContent = text; 
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// API-სთან კომუნიკაციის ფუნქცია
async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // 📢 გასაღების წაკითხვა ინპუტის ველიდან
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
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': currentApiKey // გასაღების გაგზავნა
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            const errorMsg = data.detail || data.ai_response || 'პასუხის მიღებისას დაფიქსირდა შეცდომა.';
            addMessage(`შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = `API შეცდომა: ${response.status} - ${errorMsg}`;
        }

    } catch (error) {
        console.error('ქსელური შეცდომა:', error);
        addMessage('შეცდომა: სერვერთან დაკავშირება ვერ ხერხდება.', 'ai');
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
