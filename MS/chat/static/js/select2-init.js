$(document).ready(function() {
    // Инициализация Select2
    $('#participants').select2({
        templateResult: formatUser,
        templateSelection: formatUserSelection,
        escapeMarkup: function(markup) {
            return markup; // Не экранируем HTML
        }
    });
});

function formatUser(user) {
    if (!user.id) {
        return user.text; // Если не выбрано ничего, просто отображаем текст
    }

    // Получаем аватар или используем изображение по умолчанию
    var avatar = user.element.dataset.avatar || '{% static "not_avatar.png" %}';
    // Создаем HTML-код для отображения аватара и имени пользователя
    var $result = $(
        '<div style="display: flex; align-items: center;">' +
        '<img src="' + avatar + '" class="avatar" />' + user.text +
        '</div>'
    );
    return $result;
}

function formatUserSelection(user) {
    if (!user.id) {
        return user.text; // Если не выбрано ничего, просто отображаем текст
    }
    return user.text;
}