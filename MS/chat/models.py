import datetime
from functools import cache
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

class Accaunt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default="/avatars/default_avatar.png")

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ['user__username']

    def last_seen(self):
        return cache.get(f'last_seen_{self.user.username}')

    def online(self):
        last_seen_at = self.last_seen()
        if not last_seen_at:
            return False
        return (datetime.datetime.now() - last_seen_at).total_seconds() < settings.USER_ONLINE_TIMEOUT

class Chat(models.Model):
    name = models.CharField(max_length=255)
    participants = models.ManyToManyField(User, related_name='chats')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_chats', null=True)
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Chat"
        verbose_name_plural = "Chats"
        ordering = ('name',)

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    text = models.CharField(max_length=1200)  
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ('timestamp',) 

    def formatted_timestamp(self):
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")      



