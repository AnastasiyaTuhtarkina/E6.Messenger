$(document).ready(function() {
    // Инициализация Select2 для селектора с ID 'participants'
    $('#participants').select2({
        templateResult: formatUser, // Функция для отображения элементов в списке
        templateSelection: formatUserSelection, // Функция для отображения выбранного элемента
        escapeMarkup: function(markup) {
            return markup; // Возвращаем HTML без экранирования
        }
    });
});

// Функция для форматирования отображения пользователя в списке
function formatUser(user) {
    if (!user.id) {
        return user.text; // Если ID пользователя отсутствует, просто отображаем текст
    }

    // Получение аватара пользователя, если он есть; иначе использовать стандартный аватар
    var avatar = user.element.dataset.avatar ? user.element.dataset.avatar : '{% static "not_avatar.png" %}';
    
    // Создаем HTML для отображения аватара и имени пользователя
    var $result = $(
        '<div style="display: flex; align-items: center;">' +
        '<img src="' + avatar + '" class="avatar" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px;/> ' + user.text +
        '</div>'
    );
    return $result; // Возвращаем созданный элемент
}

// Функция для отображения текста выбранного пользователя
function formatUserSelection(user) {
    if (!user.id) {
        return user.text; // Если ID отсутствует, просто отображаем текст
    }
    return user.text; // Возвращаем текст имени пользователя
}