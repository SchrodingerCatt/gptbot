// 🔑 !!! კონფიგურაცია !!!
// შეცვალეთ ეს მისამართი თქვენი Render სერვისის საბაზისო URL-ით.
// მაგ: "https://your-service-name.onrender.com/process_query"
const API_URL = "http://localhost:8040/process_query"; 
const USER_ID = "test_user_001";
// -------------------------------------------------------------

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');
const apiKeyInput = document.getElementById('api-key-input'); // იღებს გასაღებს HTML-ის ველიდან

// ფუნქცია შეტყობინების ჩატ-ბოქსში დასამატებლად
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    // 📢 გამოიყენება textContent, რათა თავიდან იქნას აცილებული XSS შეტევები.
    messageDiv.textContent = text; 
    chatBox.appendChild(messageDiv);
    
    // ჩატის ბოქსის ბოლოში ჩასქროლვა
    chatBox.scrollTop = chatBox.scrollHeight;
}

// API-სთან კომუნიკაციის ფუნქცია
async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // 1. უსაფრთხოების შემოწმება: გასაღების წაკითხვა ინპუტის ველიდან
    const currentApiKey = apiKeyInput ? apiKeyInput.value.trim() : "";
    
    if (!currentApiKey) {
        statusMessage.textContent = '❌ გთხოვთ, შეიყვანოთ X-API-Key.';
        return;
    }

    // 2. ინტერფეისის განახლება
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
                // 3. API Key-ს გაგზავნა ჰედერში
                'X-API-Key': currentApiKey 
            },
            body: JSON.stringify(payload)
        });

        // 4. JSON პასუხის წაკითხვა
        const data = await response.json(); 

        if (response.ok && data.status === 'success') {
            // 🛑 კრიტიკული ხაზი: მხოლოდ 'ai_response' ველის ამოღება და ჩვენება
            addMessage(data.ai_response, 'ai'); 
            statusMessage.textContent = '';
        } else {
            // 5. შეცდომის დამუშავება (მათ შორის 401 Unauthorized)
            const errorMsg = data.detail || data.ai_response || JSON.stringify(data);
            addMessage(`შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = `API შეცდომა: ${response.status} - ${errorMsg.substring(0, 50)}...`;
        }

    } catch (error) {
        // 6. ქსელური შეცდომის დამუშავება
        console.error('ქსელური შეცდომა:', error);
        addMessage('შეცდომა: სერვერთან დაკავშირება ვერ ხერხდება. შეამოწმეთ URL.', 'ai');
        statusMessage.textContent = 'შეცდომა: სერვერი მიუწვდომელია.';
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
