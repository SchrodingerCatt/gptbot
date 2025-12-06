// -------------------------------------------------------------
// 1. Fetch Override Fix
// -------------------------------------------------------------
// ვინახავთ ორიგინალ fetch ფუნქციას, სანამ WASM-ის ბაინდინგები შეცვლიან მას.
// ეს არის ყველაზე კრიტიკული ნაბიჯი Wasm/Unicode კონფლიქტის მოსაგვარებლად.
const nativeFetch = window.fetch; 

// -------------------------------------------------------------
// 2. Configuration
// -------------------------------------------------------------
const API_URL = "/process_query";
const USER_ID = "web_client";

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');

// -------------------------------------------------------------
// 3. Utility Functions
// -------------------------------------------------------------

function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    
    // Scroll to the bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

// -------------------------------------------------------------
// 4. Main Send Message Logic
// -------------------------------------------------------------

async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // A. UI განახლება
    addMessage(prompt, 'user');
    userInput.value = '';
    sendButton.disabled = true;
    statusMessage.textContent = 'Processing request...'; 

    let encodedPrompt;
    try {
        // 💡 Base64 კოდირება: ქართული ტექსტი გადაგვყავს UTF-8 ბაიტებად, 
        // შემდეგ კი სუფთა ASCII Base64 სტრიქონად.
        const encoder = new TextEncoder();
        const utf8Bytes = encoder.encode(prompt);
        const binaryString = String.fromCodePoint(...utf8Bytes);
        encodedPrompt = btoa(binaryString); // Base64 სტრიქონი
    } catch (e) {
        addMessage(`Error encoding prompt: ${e.message}`, 'ai');
        sendButton.disabled = false;
        statusMessage.textContent = 'Encoding Failed.';
        return;
    }

    const payload = {
        prompt: encodedPrompt, 
        user_id: USER_ID
    };

    try {
        // B. Fetch გამოძახება (nativeFetch-ის გამოყენებით)
        const response = await nativeFetch(API_URL, {
            method: 'POST',
            // ქუქიებისა და რეფერერის ბლოკირება გლობალური Unicode კონფლიქტის თავიდან ასაცილებლად
            credentials: 'omit', 
            referrerPolicy: 'no-referrer', 
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        // C. Error Handling (HTTP)
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

        // D. Success Handling
        if (data.status === 'success') {
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            const errorMsg = data.ai_response || 'Internal error occurred.';
            addMessage(`Error: ${errorMsg}`, 'ai');
            statusMessage.textContent = 'API Error: Internal response failed.';
        }

    } catch (error) {
        // E. General Error Handling
        console.error('Error:', error);
        
        let displayMessage = error.message || 'Could not connect to the server.';
        
        addMessage(`Error: ${displayMessage}`, 'ai');
        statusMessage.textContent = 'API Request Failed.';
    } finally {
        sendButton.disabled = false;
    }
}

// -------------------------------------------------------------
// 5. Event Listeners
// -------------------------------------------------------------

// Send message on button click
sendButton.addEventListener('click', sendMessage);

// Send message on Enter key press
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
