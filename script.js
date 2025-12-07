// სავარაუდო გლობალური ცვლადები
// const userInput = document.getElementById('user-input');
// const sendButton = document.getElementById('send-button');
// const statusMessage = document.getElementById('status-message');
// const API_URL = '/api/query'; // თქვენი API ენდპოინტი
// const USER_ID = 'session-123'; // მომხმარებლის იდენტიფიკატორი

async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // A. UI განახლება
    addMessage(prompt, 'user');
    userInput.value = '';
    sendButton.disabled = true;
    statusMessage.textContent = 'Processing request...'; 

    // 🛑 ყველაზე მნიშვნელოვანი ცვლილება: Base64 კოდირება მოხსნილია!
    // სერვერს ვუგზავნით უბრალო, დაუშიფრავ ტექსტს (prompt)
    const payload = {
        prompt: prompt, // prompt-ი გადის უცვლელად
        user_id: USER_ID
    };

    // B. FETCH API-ის გამოყენება
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                // Content-Type: application/json უზრუნველყოფს UTF-8-ის სწორად გაგზავნას
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        sendButton.disabled = false;
        statusMessage.textContent = '';

        if (response.ok) {
            // წარმატებული HTTP სტატუსი (200-299)
            const data = await response.json();
            if (data.status === 'success') {
                addMessage(data.ai_response, 'ai');
            } else {
                const errorMsg = data.ai_response || 'Internal API logic failure.';
                addMessage(`Error: ${errorMsg}`, 'ai');
                statusMessage.textContent = 'API Error: Internal response failed.';
            }
        } else {
            // HTTP შეცდომა (404, 500, etc.)
            let detail = `HTTP Status ${response.status}`;
            try {
                // ვცდილობთ ერორის დეტალები JSON-დან ამოვიღოთ
                const errorData = await response.json();
                detail = errorData.detail || detail;
            } catch (e) {
                // თუ პასუხი JSON ფორმატში არაა
            }
            addMessage(`Server Error: ${detail}`, 'ai');
            statusMessage.textContent = 'API Request Failed.';
        }
    } catch (error) {
        // ქსელური შეცდომა
        sendButton.disabled = false;
        statusMessage.textContent = '';
        addMessage(`Network Error: Failed to connect to API or request aborted.`, 'ai');
    }
}
