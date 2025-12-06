
const API_URL = "/process_query"; 

// 2. LOCAL_API_KEY: ეს გასაღები საჯარო იქნება. თუ აუცილებელია დაცვა, გამოიყენეთ 
// უფრო კომპლექსური მექანიზმები (მაგ. JWT-ები), მაგრამ ამ მარტივი დემოსთვის 
// ვდებთ იმავე გასაღებს, რაც Python-შია LOCAL_API_KEY-ად (რადგან მის გარეშე API არ იმუშავებს).
// უმჯობესია, ეს იყოს საჯარო, მაგრამ კლიენტისთვის უნიკალური გასაღები.
const PUBLIC_CLIENT_API_KEY = "აქ_ჩაწერეთ_თქვენი_LOCAL_API_KEY"; 

const USER_ID = "web_client";
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
                'X-API-Key': PUBLIC_CLIENT_API_KEY 
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
            // მოიცავს 401 Unauthorized შეცდომას, თუ გასაღები არასწორია
            const errorMsg = data.detail || data.ai_response || 'პასუხის მიღებისას დაფიქსირდა შეცდომა.';
            addMessage(`შეცდომა: ${errorMsg}`, 'ai');
            statusMessage.textContent = 'API შეცდომა: პასუხი ვერ იქნა მიღებული.';
        }

    } catch (error) {
        // 5. ქსელური შეცდომის ჩვენება
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