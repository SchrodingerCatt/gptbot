// 🔑 !!! კონფიგურაცია !!!
const API_URL = "http://localhost:8040/process_query";
const USER_ID = "test_user_001";
// -------------------------------------------------------------

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');

// 📢 დაამატეთ ცალკე ველს API გასაღებისთვის (ან გამოიყენეთ გლობალური ცვლადი)
// ახალი ველი DOM-ში:
// <input type="password" id="api-key-input" placeholder="შეიყვანეთ API გასაღები"> 
const apiKeyInput = document.getElementById('api-key-input'); 

// ფუნქცია შეტყობინების ჩატ-ბოქსში დასამატებლად
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    // უსაფრთხოების გასაუმჯობესებლად: გამოიყენეთ innerHTML Markdown-ის მხარდასაჭერად, მაგრამ გაფილტრვით.
    messageDiv.textContent = text; 
    chatBox.appendChild(messageDiv);
    
    // ჩატის ბოქსის ბოლოში ჩასქროლვა
    chatBox.scrollTop = chatBox.scrollHeight;
}

// API-სთან კომუნიკაციის ფუნქცია
async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // 📢 გასაღების წაკითხვა ინპუტის ველიდან
    const currentApiKey = apiKeyInput ? apiKeyInput.value.trim() : "";
    
    if (!currentApiKey) {
        statusMessage.textContent = '❌ გთხოვთ, შეიყვანოთ API გასაღები.';
        return;
    }

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
                'X-API-Key': currentApiKey 
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            // 3. წარმატებული პასუხის ჩვენება
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            // 4. შეცდომის ჩვენება
            const errorMsg = data.detail || data.ai_response || 'პასუხის მიღებისას დაფიქსირდა შეცდომა.';
            addMessage(`შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = `API შეცდომა: ${response.status} - ${errorMsg}`;
        }

    } catch (error) {
        // 5. ქსელური შეცდომის ჩვენება
        console.error('ქსელური შეცდომა:', error);
        addMessage('შეცდომა: სერვერთან დაკავშირება ვერ ხერხდება. შეამოწმეთ API URL და რომ სერვერი ჩართულია.', 'ai');
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
