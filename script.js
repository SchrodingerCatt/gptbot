// სავარაუდო გლობალური ცვლადები (დავუშვათ, რომ ესენი სწორად არის განსაზღვრული სხვაგან)
// const userInput = document.getElementById('user-input');
// const sendButton = document.getElementById('send-button');
// const statusMessage = document.getElementById('status-message');
// const API_URL = '/api/query'; // ან თქვენი რეალური API URL
// const USER_ID = 'session-123'; // ან თქვენი რეალური User ID

// დანარჩენი დამხმარე ფუნქციები (addMessage) უნდა დარჩეს უცვლელი

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

        // 2. ბაიტების მასივი გადავიყვანოთ "ერთბაიტიან" სტრიქონად, რომელიც btoa-ს სჭირდება
        // (რათა თავიდან ავიცილოთ შეცდომა 4304-ზე მეტი სიმბოლოების გამო)
        const rawBinary = Array.prototype.map.call(new Uint8Array(utf8Bytes), (byte) => {
            return String.fromCharCode(byte);
        }).join('');
        
        // 3. სტრიქონის დაშიფვრა Base64-ში
        encodedPrompt = btoa(rawBinary); 
        
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

    // B. XHR მოთხოვნის მომზადება და გაგზავნა
    const xhr = new XMLHttpRequest();
    xhr.open("POST", API_URL, true);
    
    // XHR-ისთვის ჰედერი
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            sendButton.disabled = false;
            statusMessage.textContent = '';

            if (xhr.status >= 200 && xhr.status < 300) {
                // Success
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (data.status === 'success') {
                        addMessage(data.ai_response, 'ai');
                    } else {
                        const errorMsg = data.ai_response || 'Internal API logic failure.';
                        addMessage(`Error: ${errorMsg}`, 'ai');
                        statusMessage.textContent = 'API Error: Internal response failed.';
                    }
                } catch (e) {
                    // JSON parsing error
                    addMessage(`API Error: Invalid response format.`, 'ai');
                }

            } else {
                // HTTP Error (404, 500, etc.)
                let detail = `HTTP Status ${xhr.status}`;
                try {
                    const errorData = JSON.parse(xhr.responseText);
                    detail = errorData.detail || detail;
                } catch (e) {
                    // responseText is not JSON
                }
                addMessage(`Server Error: ${detail}`, 'ai');
                statusMessage.textContent = 'API Request Failed.';
            }
        }
    };
    
    // E. XHR გაგზავნა
    xhr.send(JSON.stringify(payload));
}
