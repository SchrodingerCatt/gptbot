// -------------------------------------------------------------
// Configuration
// -------------------------------------------------------------
const API_URL = "/process_query";
const USER_ID = "web_client";
// -------------------------------------------------------------

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');

// Function to add a message to the chat box
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    
    // Scroll to the bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Function to communicate with the API
async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // 1. Add user message
    addMessage(prompt, 'user');
    userInput.value = '';
    sendButton.disabled = true;
    statusMessage.textContent = 'Processing request...'; 

    let encodedPrompt;
    try {
        // 💡 ყველაზე სტაბილური კოდირება Wasm კონფლიქტისთვის:
        // 1. ტექსტი გადაჰყავს UTF-8 ბაიტებად
        const encoder = new TextEncoder();
        const utf8Bytes = encoder.encode(prompt);
        
        // 2. ბაიტები გადაჰყავს Base64-ში (ASCII სტრიქონი)
        const binaryString = String.fromCodePoint(...utf8Bytes);
        encodedPrompt = btoa(binaryString);

    } catch (e) {
        // თუ კოდირება ვერ მოხერხდა
        addMessage(`Error encoding prompt: ${e.message}`, 'ai');
        sendButton.disabled = false;
        statusMessage.textContent = 'Encoding Failed.';
        return;
    }

    const payload = {
        // prompt ველი ახლა შეიცავს მხოლოდ ASCII-ზე დაფუძნებულ Base64 სტრიქონს
        prompt: encodedPrompt, 
        user_id: USER_ID
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        // Error handling for non-2xx HTTP statuses
        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            
            try {
                errorData = JSON.parse(errorText);
            } catch (e) {
                throw new Error(`API Error: HTTP status ${response.status}.`); 
            }
            
            const detail = errorData.detail || `API Error: HTTP status ${response.status}`;
            throw new Error(detail); 
        }

        const data = await response.json();

        if (data.status === 'success') {
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            const errorMsg = data.ai_response || 'Internal error occurred.';
            addMessage(`Error: ${errorMsg}`, 'ai');
            statusMessage.textContent = 'API Error: Internal response failed.';
        }

    } catch (error) {
        console.error('Error:', error);
        
        let displayMessage = error.message || 'Could not connect to the server.';
        
        addMessage(`Error: ${displayMessage}`, 'ai');
        statusMessage.textContent = 'API Request Failed.';
    } finally {
        sendButton.disabled = false;
    }
}

// Send message on button click
sendButton.addEventListener('click', sendMessage);

// Send message on Enter key press
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
