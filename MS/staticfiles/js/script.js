document.addEventListener("DOMContentLoaded", function() {
    let conn = new WebSocket("wss://127.0.0.1:8000/ws/chat/");
    const msg = document.getElementById("msg");
    const log = document.getElementById("log");
    const form = document.getElementById("form");
    const usernameInput = document.getElementById("username");
    const avatarInput = document.getElementById("avatar");
    const updateInfoBtn = document.getElementById("update-info");
    const disconnectBtn = document.getElementById("disconnectBtn");

    // Проверки на существование
    if (!form || !msg || !log || !disconnectBtn) {
        console.error("One or more DOM elements are missing!");
        return;
    }

    function appendLog(item) {
        const doScroll = log.scrollTop > log.scrollHeight - log.clientHeight - 1;
        log.appendChild(item);
        if (doScroll) {
            log.scrollTop = log.scrollHeight - log.clientHeight;
        }
    }

    // Обработчик отправки сообщения
    form.onsubmit = function () {
        // Проверка состояния соединения и наличия сообщения
        if (!conn || conn.readyState !== WebSocket.OPEN) {
            console.warn("WebSocket is not open. Can't send message.");
            return false;
        }
        if (!msg.value.trim()) { // Проверка на пустое сообщение
            console.warn("Message cannot be empty.");
            return false;
        }
    
        // Формируем сообщение с username и avatar
        const messageData = {
            username: usernameInput.value.trim(),
            avatar: avatarInput.value.trim(),
            message: msg.value.trim()
        };
    
        // Отправка сообщения
        conn.send(JSON.stringify(messageData));
        msg.value = ""; // Очистка поля ввода сообщения
        return false; // Предотвращение отправки формы
    };

    // Обработчик обновления информации пользователя
    updateInfoBtn.onclick = function() {
        if (!conn || conn.readyState !== WebSocket.OPEN) {
            return false;
        }

        const userInfo = {
            username: usernameInput.value.trim(),
            avatar: avatarInput.value.trim()
        };

        if (!userInfo.username && !userInfo.avatar) {
            console.warn("Username and avatar cannot be empty.");
            return;
        }

        // Отправка обновленных данных на сервер
        conn.send(JSON.stringify({ type: "update_profile", ...userInfo }));
    };

    conn.onopen = function () {
        const item = document.createElement("div");
        item.innerHTML = "<b>Connection established.</b>";
        appendLog(item);
    };    


    if (window["WebSocket"]) {
        conn.onclose = function (evt) {
            const item = document.createElement("div");
            item.innerHTML = "<b>Connection closed.</b>";
            appendLog(item);
            conn = null; // Обнуление переменной 'conn'
        };

        conn.onmessage = function (evt) {
            const messages = evt.data.split('\n');
            for (let i = 0; i < messages.length; i++) {
                const item = document.createElement("div");
                let message = messages[i];
                try {
                    message = JSON.parse(message);
                    if (message.lat && message.lng) {
                        message = `https://www.openstreetmap.org/#map=18/${message.lat}/${message.lng}`;
                    } else {
                        message = message.message;
                    }
                } catch (e) {
                    // Ничего не делать
                }
                item.innerText = message;
                appendLog(item);
            }
        };
    } else {
        const item = document.createElement("div");
        item.innerHTML = "<b>Your browser does not support WebSockets.</b>";
        appendLog(item);
    }

    // Обработчик событий для ошибок соединения
    conn.onerror = function (evt) {
        console.error("WebSocket error:", evt);
        const item = document.createElement("div");
        item.innerHTML = "<b>Error occurred: </b>" + evt.message;
        appendLog(item);
    };

    conn.onclose = function () {
        const item = document.createElement("div");
        item.innerHTML = "<b>Connection closed.</b>";
        appendLog(item);
    };

    setInterval(() => {
        console.log("WebSocket readyState: ", conn.readyState);
    }, 5000); // Логирование состояния каждые 5 секунд
    

    // Событие для закрытия соединения при уходе со страницы
    window.addEventListener("beforeunload", function() {
        if (conn) {
            conn.close();
        }
    });

    // Обработчик кнопки отключения
    disconnectBtn.onclick = function () {
        if (conn) {
            conn.close();
            const item = document.createElement("div");
            item.innerHTML = "<b>Connection closed by user.</b>";
            appendLog(item);
        }
    };
});