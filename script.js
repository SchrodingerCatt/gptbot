// -------------------------------------------------------------
// Configuration (Use only Latin characters for variables/keys)
// -------------------------------------------------------------
const API_URL = "/process_query"; 
const USER_ID = "web_client"; // Used to identify the client
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
    statusMessage.textContent = 'პასუხის გენერაცია მიმდინარეობს...';

    // 🛑 Payload uses only Latin keys (prompt, user_id)
    const payload = {
        prompt: prompt,
        user_id: USER_ID
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            // 🛑 Headers uses only Latin keys
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        // Error handling for non-2xx HTTP statuses (e.g., 500, 404)
        if (!response.ok) {
            const errorText = await response.text();
            let errorData;
            
            try {
                // Try to parse the error response as JSON (FastAPI usually returns JSON errors)
                errorData = JSON.parse(errorText);
            } catch (e) {
                // If not JSON, throw a generic error
                throw new Error(`API შეცდომა: HTTP სტატუსი ${response.status}.`);
            }
            
            // Extract the 'detail' message from the FastAPI JSON error
            const detail = errorData.detail || `API შეცდომა: HTTP სტატუსი ${response.status}`;
            throw new Error(detail); 
        }

        const data = await response.json();

        if (data.status === 'success') {
            // 3. Display success response
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            // If HTTP is 200 but internal status is not 'success'
            const errorMsg = data.ai_response || 'პასუხის მიღებისას დაფიქსირდა შიდა შეცდომა.';
            addMessage(`შიდა შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = 'API შეცდომა: შიდა პასუხი ვერ იქნა მიღებული.';
        }

    } catch (error) {
        // 5. Display network or caught HTTP error
        console.error('Error:', error);
        
        let displayMessage = error.message || 'სერვერთან დაკავშირება ვერ ხერხდება.';
        
        addMessage(`შეცდომა: ${displayMessage}`, 'ai');
        statusMessage.textContent = 'API მოთხოვნა ვერ შესრულდა.';
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
