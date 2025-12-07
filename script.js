// სავარაუდო გლობალური ცვლადები
// const userInput = document.getElementById('user-input');
// const sendButton = document.getElementById('send-button');
// const statusMessage = document.getElementById('status-message');
// const API_URL = '/api/query'; // ან თქვენი რეალური API URL
// const USER_ID = 'session-123'; // ან თქვენი რეალური User ID

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
        // Base64 კოდირება UTF-8 სიმბოლოებისთვის (გასწორებული ლოგიკა)
        const encoder = new TextEncoder();
        const utf8Bytes = encoder.encode(prompt); // 1. მივიღოთ UTF-8 ბაიტები

        // 2. ბაიტების მასივის გადაყვანა "ერთბაიტიან" სტრიქონში
        // (რაც თავიდან აგვაცილებს უნიკოდის 4304-ის შეცდომას btoa-ში)
        const binaryString = Array.from(utf8Bytes, byte => 
            String.fromCharCode(byte)
        ).join('');
        
        // 3. სტრიქონის დაშიფვრა Base64-ში
        encodedPrompt = btoa(binaryString); 

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

    // B. FETCH API-ის გამოყენება (ჩანაცვლებულია XMLHttpRequest)
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            // აუცილებელია Content-Type
            headers: {
                'Content-Type': 'application/json',
            },
            // მონაცემების გაგზავნა JSON ფორმატში
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
        // ქსელური შეცდომა (Network Error, სერვერთან კავშირის პრობლემა)
        sendButton.disabled = false;
        statusMessage.textContent = '';
        addMessage(`Network Error: Failed to connect to API or request aborted.`, 'ai');
    }
}
