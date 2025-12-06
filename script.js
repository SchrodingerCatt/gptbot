// -------------------------------------------------------------
// Configuration (Use only Latin characters for variables/keys)
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
    // Status text in ASCII, but still displays on screen
    statusMessage.textContent = 'Processing request...'; 

    const payload = {
        // Keys must be Latin: prompt, user_id
        prompt: prompt,
        user_id: USER_ID
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                // Headers must be Latin: 'Content-Type'
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        // Error handling for non-2xx HTTP statuses
        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            
            try {
                // Try to parse the error response as JSON (FastAPI error)
                errorData = JSON.parse(errorText);
            } catch (e) {
                // If not JSON, throw a generic error
                throw new Error(`API Error: HTTP status ${response.status}.`); 
            }
            
            // Extract the 'detail' message from the FastAPI JSON error
            const detail = errorData.detail || `API Error: HTTP status ${response.status}`;
            throw new Error(detail); 
        }

        const data = await response.json();

        if (data.status === 'success') {
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            // Internal API logic failure
            const errorMsg = data.ai_response || 'Internal error occurred.';
            addMessage(`Error: ${errorMsg}`, 'ai');
            statusMessage.textContent = 'API Error: Internal response failed.';
        }

    } catch (error) {
        console.error('Error:', error);
        
        // Display generic error message to the user
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
