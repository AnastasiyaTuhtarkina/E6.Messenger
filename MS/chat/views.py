import logging
from h11 import Response
from rest_framework import viewsets, status, permissions
from msilib.schema import ListView
from django.contrib import auth
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .serializers import ChatSerializer, MessageSerializer
from.models import *  # Assuming Chat is your model name
from .forms import UserRegistrationForm, ProfileForm, ChatForm

# Create your views here.

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse('default')


# Главная страница (список чатов)
def default_view(request):
    if request.user.is_authenticated:
        user_chats = Chat.objects.filter(participants=request.user)

        # Получаем фильтр из GET параметров
        chat_filter = request.GET.get('filter')

        # Если есть фильтр, применяем его
        if chat_filter == 'private':
            user_chats = user_chats.filter(is_group=False)
        elif chat_filter == 'group':
            user_chats = user_chats.filter(is_group=True)

        # Логика для замены имени чата на "чат с {пользователь}"
        chats_with_names = []
        for chat in user_chats:
            if not chat.is_group and chat.participants.count() == 2:
                # Находим другого участника чата
                other_user = chat.participants.exclude(id=request.user.id).first()
                chat.display_name = f"Chat with {other_user.username}" if other_user else chat.name
            else:
                chat.display_name = chat.name  # Оставляем стандартное имя для групповых чатов
            chats_with_names.append(chat)

        # Пагинация
        paginator = Paginator(chats_with_names, 10)  # 10 чатов на страницу
        page_number = request.GET.get('page')  # Получаем номер страницы из параметров запроса
        page_obj = paginator.get_page(page_number)  # Получаем объект страницы

        return render(request, 'default.html', {'page_obj': page_obj})
    else:
        return render(request, 'default.html', {'message': 'Please log in to see your chats.'})
    

def signup_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request,'signup.html', {'form': form})


def logout_view(request):
    auth.logout(request)
    return redirect('login')

logger = logging.getLogger(__name__)


def create_chat_view(request):
    chat_name = None  # Инициализация переменной
    if request.method == 'POST':
        chat_name = request.POST.get('chat_name')
    if not chat_name:
        return render(request, 'create_chat.html', {'error': 'Chat name cannot be empty'})

    try:
        Chat.objects.create(name=chat_name)
        return redirect('default')
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        return render(request, 'create_chat.html', {'error': str(e)})
    

def chats_view(request):
    if request.user.is_authenticated:
        user_chats = Chat.objects.filter(participants=request.user).prefetch_related('participants')

        # Логика для замены имени чата на "чат с {пользователь}"
        chats_with_names = []
        for chat in user_chats:
            if not chat.is_group and chat.participants.count() == 2:
                # Находим другого участника чата
                other_user = chat.participants.exclude(id=request.user.id).first()
                chat.display_name = f"Chat with {other_user.username}" if other_user else chat.name
            else:
                chat.display_name = chat.name  # Оставляем стандартное имя для групповых чатов
            chats_with_names.append(chat)

        # Пагинация
        paginator = Paginator(chats_with_names, 10)  # 10 чатов на страницу
        page_number = request.GET.get('page')  # Получаем номер страницы из параметров запроса
        page_obj = paginator.get_page(page_number)  # Получаем объект страницы

        return render(request, 'default.html', {'page_obj': page_obj})
    else:
        return render(request, 'default.html', {'message': 'Please log in to see your chats.'})


def private_chat_view(request, user_id):  # Изменено здесь
    if request.method == 'POST':
        if not user_id:
            return render(request, 'private_chat.html', {'error': 'User ID is required.'})
        
        try:
            user = User.objects.get(id=user_id)
            # Создаем чат с обоими участниками: текущим пользователем и найденным пользователем
            chat, created = Chat.objects.get_or_create(participants=[request.user, user])
            return redirect('chat_room', chat_id=chat.id)  # Перенаправляем пользователя в комнату чата
            
        except User.DoesNotExist:
            logger.error(f"User with id {user_id} does not exist.")
            return render(request, 'private_chat.html', {'error': 'User not found.'})

    # Если запрос GET, используйте get_object_or_404 для извлечения пользователя
    user = get_object_or_404(User, id=user_id)
    return render(request, 'private_chat.html', {'user': user})


def chat_room_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)  # Получаем чат по id
    room_name = chat.name  # Имя комнаты - название чата
    participants_count = chat.participants.count()  # Количество участников

    # Проверяем, является ли текущий пользователь участником чата
    if request.user not in chat.participants.all():
        logger.warning(f"User {request.user.username} attempted to access chat {chat_id} without permission.")
        return render(request, 'error.html', {'message': 'You are not a participant in this chat.'})

    return render(request, 'chat_room.html', {
        'chat': chat,
        'room_name': room_name,
        'participants_count': participants_count  # Передаем количество участников
    })

# Страница редактирования чата
def edit_chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)  # Получаем чат по ID

    # Проверка, является ли текущий пользователь участником чата
    if request.user not in chat.participants.all():
        logger.warning(f"User {request.user.username} attempted to edit chat {chat_id} without permission.")
        return render(request, 'error.html', {'message': 'You do not have permission to edit this chat.'})

    if request.method == 'POST':
        form = ChatForm(request.POST, instance=chat)  # Заполняем форму текущими данными чата
        if form.is_valid():
            form.save()  # Сохраняем изменения
            return redirect('chat_room', chat_id=chat.id)  # Перенаправление на страницу чата
        else:
            logger.error(f"Form submission error for chat {chat_id}: {form.errors}")

    else:
        form = ChatForm(instance=chat)  # Создаем форму с текущими данными

    return render(request, 'edit_chat.html', {'form': form, 'chat': chat})  # Возвращаем шаблон редактирования

    
# Страница удаления чата
def delete_chat_view(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    
    # Проверка, что пользователь участвует в чате
    if request.user in chat.participants.all():
        chat.delete()  # Удаляем чат
        logger.info(f"Chat {chat_id} was deleted by user {request.user.username}.")
        return redirect('default')  # Перенаправляем на главную страницу или куда нужно
    else:
        logger.warning(f"User {request.user.username} attempted to delete chat {chat_id} without permission.")
        return render(request, 'error.html', {'message': 'Вы не можете удалить этот чат.'})

@login_required
def accaunt_view(request):
    profile, created = Accaunt.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Проверка уникальности имени пользователя
            new_username = form.cleaned_data['username']
            if new_username != request.user.username and User.objects.filter(username=new_username).exists():
                form.add_error('username', 'Это имя пользователя уже занято.')
            else:
                form.save()
                request.user.username = new_username
                request.user.save()
                logger.info(f"User {request.user.username} updated their profile successfully.")
                return redirect('accaunt')  # Перенаправление на страницу профиля
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, 'accaunt.html', {'form': form, 'profile': profile})

    
# Функция для отображения всех пользователей
def all_users_view(request):
    users_list = User.objects.exclude(id=request.user.id)  # Исключаем текущего пользователя
    logger.info(f"Displaying users list - User count: {users_list.count()}.")

    paginator = Paginator(users_list, 10)  # Показываем по 10 пользователей на странице
    page_number = request.GET.get('page')
    try:
        users = paginator.get_page(page_number)
    except PageNotAnInteger:  # Если номер страницы не является целым числом
        users = paginator.get_page(1)  # Показываем первую страницу
    except EmptyPage:  # Если страница вне диапазона, возвращаем последнюю страницу;
        users = paginator.get_page(paginator.num_pages)

    return render(request, 'all_users.html', {
        'users': users,
        'empty': users_list.count() == 0,  # Флаг, указывающий, есть ли пользователи
    })

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all() 
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только те чаты, в которых участвует текущий пользователь
        return Chat.objects.filter(participants=self.request.user)

    def create(self, request, *args, **kwargs):
        # Вызываем родительский метод для обработки создания объекта
        response = super().create(request, *args, **kwargs)
        
        # Логируем создание чата
        logger.info(f"Chat created by {request.user.username}: {response.data}")
        return response

    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            logger.info(f"Chat updated by {request.user.username}: {response.data}")
            return response
        except Exception as e:
            logger.error(f"Error updating chat by {request.user.username}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        chat = serializer.save()  # Сохранить чат
        chat.users.add(self.request.user)  # Добавить текущего пользователя в чат

    def destroy(self, request, *args, **kwargs):
        try:
            response = super().destroy(request, *args, **kwargs)
            logger.info(f"Chat deleted by {request.user.username}")
            return response
        except Exception as e:
            logger.error(f"Error deleting chat by {request.user.username}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ViewSet для API сообщений
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat', None)
        if chat_id is not None:
            try:
                chat = Chat.objects.get(id=chat_id)
            except Chat.DoesNotExist:
                logger.warning(f"Chat with id {chat_id} does not exist.")
            return Message.objects.none()  # Возвращаем пустой queryset, если чат не существует

        return self.queryset.filter(chat_id=chat_id)

    def create(self, request, args, kwargs):
        request.data['user'] = request.user.id  # Указываем текущего пользователя как отправителя
        logger.info(f"User {request.user.username} sending message in chat {request.data.get('chat')}.")
        return super().create(request, args, kwargs)
        





