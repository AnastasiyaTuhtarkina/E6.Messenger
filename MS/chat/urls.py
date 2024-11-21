from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *  # Импорт всех представлений из views.py
from . import views

# Создание маршрутизатора для API
router = DefaultRouter()
router.register(r'chats', views.ChatViewSet, basename='chats')  # Добавить маршруты для API чатов
router.register(r'messages', views.MessageViewSet, basename='messages')  # Добавить маршруты для API сообщений

urlpatterns = [
    path('', include(router.urls)),  # Включение маршрутов для API
    path('home/', views.default_view, name='default'),  # Главная страница (список чатов)
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Страница входа
    path('signup/', views.signup_view, name='signup'),  # Страница регистрации
    path('logout/', views.logout_view, name='logout'),  # Страница выхода
    path('create_chat/', views.create_chat_view, name='create_chat'),  # Страница создания чата
    path('edit_chat/<int:chat_id>/', views.edit_chat_view, name='edit_chat'),  # Страница редактирования чата по ID
    path('delete/<int:chat_id>/', views.delete_chat_view, name='delete_chat'),  # Страница удаления чата
    path('chat/<int:chat_id>/', views.chat_room_view, name='chat_room'),  # Страница конкретного чата по ID
    path('private/<int:user_id>/', views.private_chat_view, name='private_chat'),  # Личный чат с пользователем по ID
    path('my_profile/', views.accaunt_view, name='profile'),  # Страница профиля пользователя
    path('users/', views.all_users_view, name='all_users'),  # URL для страницы всех пользователей
]