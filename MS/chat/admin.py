from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Accaunt, Chat, Message


@admin.register(Accaunt)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')  
    search_fields = ('user__username',)  


admin.site.unregister(User)  
admin.site.register(User, UserAdmin) 
admin.site.register(Chat)
admin.site.register(Message)