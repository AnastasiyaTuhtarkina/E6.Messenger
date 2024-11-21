import logging
from pyexpat.errors import messages
from h11 import Response
from rest_framework import viewsets, status, permissions
from msilib.schema import ListView
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.db.models import Count, Value
from django.db.models.functions import Coalesce
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

        # Подготовка логики для отображаемого имени чата
        for chat in user_chats:
            if not chat.is_group and chat.participants.count() == 2:
                other_user = chat.participants.exclude(id=request.user.id).first()
                chat.display_name = f"Chat with {other_user.username}" if other_user else "Unknown User"
            else:
                chat.display_name = chat.name  # Оставляем стандартное имя для групповых чатов

        # Пагинация
        paginator = Paginator(user_chats, 10)  # 10 чатов на страницу
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

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

# Формируем страницу для создания чата 
def create_chat_view(request):
    users = User.objects.all()  # Получите всех пользователей

    if request.method == 'POST':
        chat_name = request.POST.get('name')
        participant_ids = request.POST.getlist('participants')  # Получение id участников как список
        is_group = request.POST.get('is_group') == 'on'  # Проверка значения

        # Проверка на пустое имя чата
        if not chat_name:
            return render(request, 'create_chat.html', {'users': users, 'error': 'Имя чата не может быть пустым'})

        # Проверка на уникальность имени чата
        existing_chats = Chat.objects.filter(name=chat_name)
        if is_group:
            existing_chats = existing_chats.filter(participants__in=[request.user]).distinct()  # Проверка для группового чата
            
        if existing_chats.exists():
            return render(request, 'create_chat.html', {'users': users, 'error': 'Чат с таким именем уже существует.'})

        # Получение объектов участников
        participants = User.objects.filter(id__in=participant_ids)
        if not participants.exists():
            return render(request, 'create_chat.html', {'users': users, 'error': 'Участники не найдены'})

        try:
            # Создание чата
            if is_group:
                participants = participants | User.objects.filter(id=request.user.id)  # Добавляем создателя в участников
            
            chat = Chat.objects.create(name=chat_name, creator=request.user, is_group=is_group)  # Создаем чат с создателем
            chat.participants.add(*participants)  # Добавляем объекты участников

            messages.success(request, 'Чат успешно создан!')
            return redirect('chat_room', chat_id=chat.id)  # Передаем chat_id в редиректе) 
        except Exception as e:
            logger.error(f"Error creating chat: {e}")
            return render(request, 'create_chat.html', {'users': users, 'error': str(e)})

    return render(request, 'create_chat.html', {'users': users})   # Передаем пользователей для отображения при создании чата


def chats_view(request):
    if request.user.is_authenticated:
    
        filter_type = request.GET.get('filter', None)  # Получаем тип фильтра из URL

        # Фильтруем чаты в зависимости от выбранного типа
        if filter_type == 'private':
            user_chats = Chat.objects.filter(participants=request.user, is_group=False).prefetch_related('participants')
        elif filter_type == 'group':
            user_chats = Chat.objects.filter(participants=request.user, is_group=True).prefetch_related('participants')
        else:
            user_chats = Chat.objects.filter(participants=request.user).prefetch_related('participants')

        # Логика для замены имени чата на "чат с {пользователь}"
        chats_with_names = []
        for chat in user_chats:
            if chat.is_group:
                chat.display_name = chat.name  # Оставляем стандартное имя для групповых чатов
            elif chat.participants.count() == 2:
                other_user = chat.participants.exclude(id=request.user.id).first()
                chat.display_name = f"Chat with {other_user.username}" if other_user else chat.name
            else:
                chat.display_name = chat.name  # В любом другом случае просто используем имя чата
            chats_with_names.append(chat)

        # Пагинация
        paginator = Paginator(chats_with_names, 10)  # 10 чатов на страницу
        page_number = request.GET.get('page')  # Получаем номер страницы из параметров запроса
        page_obj = paginator.get_page(page_number)  # Получаем объект страницы

        return render(request, 'default.html', {'page_obj': page_obj})
    else:
        return render(request, 'default.html', {'message': 'Please log in to see your chats.'})


@login_required
def private_chat_view(request, user_id):
    # Получаем текущего пользователя
    current_user = request.user

    # Находим другого пользователя
    other_user = get_object_or_404(User, id=user_id)

    # Пытаемся получить чат между текущим пользователем и другим пользователем
    chat = Chat.objects.filter(participants=current_user).filter(participants=other_user)

    # Если чата не существует, можно создать его (если нужно)
    if chat.exists():
        chat = chat.first()  # Получаем первый чат
    else:
        # Если чата не существует, создаем его
        chat = Chat.objects.create(name=f"Chat with {other_user.username}", is_group=False)
        chat.participants.add(current_user, other_user)

    # Здесь вы можете добавить логику для отображения чата
    return render(request, 'private_chat.html', {'chat': chat, 'other_user': other_user})


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
        'participants_count': participants_count,  # Передаем количество участников
        'chat_id': chat.id
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
        





