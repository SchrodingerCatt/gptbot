// -------------------------------------------------------------
// XHR-ზე გადართვა Wasm-ის კონფლიქტის თავიდან ასაცილებლად
// -------------------------------------------------------------

// ... (კონფიგურაცია და addMessage ფუნქცია უცვლელია)

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
        // Base64 კოდირება (უცვლელია)
        const encoder = new TextEncoder();
        const utf8Bytes = encoder.encode(prompt);
        const binaryString = String.fromCodePoint(...utf8Bytes);
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

    const xhr = new XMLHttpRequest();
    xhr.open("POST", API_URL, true);
    
    // 💡 XHR-ისთვის ჰედერი
    xhr.setRequestHeader("Content-Type", "application/json");

    // 💡 ქუქიების და რეფერერის ბლოკირება (XHR-ში განსხვავებულად მუშაობს, მაგრამ აუცილებელია)
    // credentials: 'omit' fetch-ის სპეციფიკურია, XHR-ში მას უბრალოდ არ ვრთავთ

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

// ... (Event Listeners უცვლელია)
