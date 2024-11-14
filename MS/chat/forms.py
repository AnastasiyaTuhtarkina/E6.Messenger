import logging
from venv import logger
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import *


logger = logging.getLogger(__name__)

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    avatar = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'avatar']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется.")
        return email

    def save(self, commit=True):
        user = super().save(commit)
        # Создаем или обновляем профиль
        profile, created = Accaunt.objects.get_or_create(user=user) 
        
        avatar = self.cleaned_data.get('avatar')  # Проверяем аватар
        if avatar:
            profile.avatar = avatar
        
        if commit:
            profile.save()
        
        logger.info(f"User {user.username} registered successfully.")
        return user
    

class ProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=200)

    class Meta:
        model = Accaunt
        fields = ['username', 'avatar']

    def save(self, commit=True):
        profile = super().save(commit)
        username = self.cleaned_data.get('username')

        if username:
            # Проверка уникальности имени пользователя
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError("Это имя пользователя уже используется.")
                
            profile.user.username = username

        if commit:
            profile.user.save()
            logger.info(f"User {profile.user.username} updated their profile successfully.")

        return profile    

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
        if user and isinstance(user, User):
            self.fields['username'].initial = user.username


class ChatForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Получаем всех пользователей
        widget=forms.CheckboxSelectMultiple, 
        required=True
    )

    class Meta:
        model = Chat
        fields = ['name', 'participants'] 
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Chat.objects.filter(name=name).exists():
            raise forms.ValidationError("Чат с таким именем уже существует.")
        return name

    def save(self, commit=True):
        chat = super(ChatForm, self).save(commit)
        logger.info(f"Chat {chat.name} created/updated successfully.")
        return chat

    def last_message(self):
        return self.instance.messages.last() if self.instance.messages.last() else None
