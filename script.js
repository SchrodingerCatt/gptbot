// ეს ცვლადები უნდა შეცვალოთ თქვენი კონფიგურაციის მიხედვით
// API_URL უნდა მიუთითებდეს თქვენს სერვერზე
const API_URL = "/api/query"; // ემთხვევა main.py-ს ახალ მისამართს
const USER_ID = "test_user_001"; // მომხმარებლის იდენტიფიკატორი
// -------------------------------------------------------------

const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');

// ფუნქცია შეტყობინების ჩატ-ბოქსში დასამატებლად
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
    messageDiv.textContent = text;
    chatBox.appendChild(messageDiv);
    
    // ჩატის ბოქსის ბოლოში ჩასქროლვა
    chatBox.scrollTop = chatBox.scrollHeight;
}

// API-სთან კომუნიკაციის ფუნქცია
async function sendMessage() {
    const prompt = userInput.value.trim();
    if (!prompt) return;

    // 1. მომხმარებლის შეტყობინების დამატება
    addMessage(prompt, 'user');
    userInput.value = '';
    sendButton.disabled = true;
    statusMessage.textContent = 'პასუხის გენერაცია მიმდინარეობს...';

    // 🛑 მონაცემების შექმნა Form Data ფორმატში
    const formData = new URLSearchParams();
    formData.append('prompt', prompt); 
    formData.append('user_id', USER_ID);

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                // 💡 აუცილებელი ჰედერი Form Data-სთვის
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString() // მონაცემების გაგზავნა
        });

        const data = await response.json();

        if (response.ok && data.status === 'success') {
            // 2. წარმატებული პასუხის ჩვენება
            addMessage(data.ai_response, 'ai');
            statusMessage.textContent = '';
        } else {
            // 3. შეცდომის ჩვენება
            const errorMsg = data.detail || data.ai_response || 'პასუხის მიღებისას დაფიქსირდა შეცდომა.';
            addMessage(`შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = 'API შეცდომა: პასუხი ვერ იქნა მიღებული.';
        }

    } catch (error) {
        // 4. ქსელური შეცდომის ჩვენება
        console.error('ქსელური შეცდომა:', error);
        addMessage('შეცდომა: სერვერთან დაკავშირება ვერ ხერხდება.', 'ai');
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
