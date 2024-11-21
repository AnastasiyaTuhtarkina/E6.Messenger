let chatSocket; 

function initializeChat(chatType, roomName, username) {
    if (!chatType || !roomName || !username) {
        console.error('Chat type, room name, or username is missing');
        return;
    }

    if (chatSocket) {
        console.warn('WebSocket is already open. Closing the existing socket.');
        try {
            chatSocket.close();  // Закрываем старое соединение, если оно существует
        } catch(e) {
            console.error('Error closing WebSocket:', e);
        }
    }

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsURL = `${protocol}://${window.location.host}/ws/chat/${chatType}/${roomName}/`;
    console.log('Connecting to WebSocket:', wsURL);

    chatSocket = new WebSocket(wsURL);

    chatSocket.onopen = function() {
        console.log('WebSocket is open');
        addMessageToChat('System', `${username} has joined the chat.`);
        updateConnectionStatus('CONNECTED');
    };

    chatSocket.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);
            // Дебагинг входящих данных
            console.log('Message received from server:', data);
    
            // Извлекаем данные из объекта
            const { message, username, avatar } = data;
    
            // Проверяем наличие всех необходимых полей
            if (message && username && avatar) {
                addMessageToChat(username, message, avatar); // Вызов функции для добавления сообщения
            } else {
                console.warn('Received incomplete message data:', data);
            }
        } catch (error) {
            console.error('Error processing message:', error);
        }
    };

    chatSocket.onclose = function() {
        console.log('WebSocket closed');
        updateConnectionStatus('DISCONNECTED');
        document.getElementById('open-button').disabled = false;
    };

    chatSocket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus('ERROR');
    };
}

// ��ункция для добавления сообщения в чат
function addMessageToChat(username, message, avatar) {
    const chatLog = document.getElementById('chat-log');
    if (!chatLog) return;

    const messageElement = document.createElement('div');
    
    // Создание элемента сообщения
    messageElement.innerHTML = `
        <img src="${avatar}" alt="${escapeHTML(username)}'s avatar" style="width: 30px; height: 30px;">
        <strong>${escapeHTML(username)}:</strong> ${escapeHTML(message)}
    `;

    chatLog.appendChild(messageElement);
    chatLog.scrollTop = chatLog.scrollHeight; // Прокрутка вниз к последнему сообщению
}

console.log('chatSocket before sending:', chatSocket);
// Функция для отправки сообщения
function sendMessage(event) {
    event.preventDefault();
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        const messageInput = document.getElementById('chat-message-input');
        const message = messageInput.value;
        chatSocket.send(JSON.stringify({
            message: message,
            username: document.getElementById('username').value
        }));
        messageInput.value = ''; // Очистка поля ввода
    } else {
        console.error('Cannot send message: WebSocket is not open.', chatSocket);
        alert('Cannot send message, WebSocket is not open.');
    }
}

// Функция для открытия соединения
function openConnection() {
    const chatType = document.getElementById('chat-type').value; // Получаем тип чата
    const roomName = document.getElementById('room-name').value; // Получаем имя комнаты
    const username = document.getElementById('username').value;

    if (!chatSocket || chatSocket.readyState === WebSocket.CLOSED) {
        initializeChat(chatType, roomName, username); // Вызов инициализации
        document.getElementById('open-button').disabled = true; // Отключаем кнопку после открытия соединения
    } else {
        console.warn('WebSocket is already open.');
    }
}

// Функция для закрытия соединения
function closeConnection() {
    if (chatSocket) {
        chatSocket.close();
        chatSocket = null; // Сбросить переменную
    }
}

// Функция для обновления статуса соединения
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');

    if (statusElement) {
        statusElement.innerText = status;
        statusElement.className = ''; // Сбросить предыдущие классы статуса

        if (status === 'CONNECTED') {
            statusElement.classList.add('text-success');
        } else if (status === 'DISCONNECTED') {
            statusElement.classList.add('text-danger');
        } else if (status === 'ERROR') {
            statusElement.classList.add('text-warning');
        }
    }
}

// Привязываем события к форме и кнопкам
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form'); // Убедитесь, что у вас есть этот элемент
    const closeButton = document.getElementById('close-button'); // Получаем кнопку закрытия

    if (chatForm) {
        chatForm.onsubmit = sendMessage; // Обработчик отправки сообщения
    }

    const openButton = document.getElementById('open-button');

    if (openButton) {
        openButton.addEventListener('click', openConnection); // Открытие соединения
    }

    if (closeButton) {
        closeButton.addEventListener('click', closeConnection); // Закрытие соединения
    }
});

//экранирование для предотвращения XSS
function escapeHTML(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// Экранирование HTML
function escapeHTML(unsafe) {
    return unsafe.replace(/[&<>"']/g, function(match) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return map[match];
    });
}