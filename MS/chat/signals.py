from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Accaunt

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Создает новый профиль пользователя при создании пользователя 
    и обновляет профиль, если он уже существует.
    """
    if created:
        # Создание нового профиля аккаунта
        Accaunt.objects.create(user=instance)
    else:
        # Обновление профиля аккаунта
        instance.accaunt.save()