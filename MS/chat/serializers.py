from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Chat, Message

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ChatSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)

    class Meta:
        model = Chat
        fields = ['id', 'name', 'participants']

    def create(self, validated_data):
        participants_data = validated_data.pop('participants')
        chat = Chat.objects.create(**validated_data)
        for participant_data in participants_data:
            user = User.objects.get(id=participant_data['id'])  # или используйте get_or_create
            chat.participants.add(user)
        return chat

    def update(self, instance, validated_data):
        participants_data = validated_data.pop('participants', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        
        if participants_data is not None:
            instance.participants.clear()  # Удаление старых участников
            for participant_data in participants_data:
                user = User.objects.get(id=participant_data['id'])  # или используйте get_or_create
                instance.participants.add(user)
        
        return instance


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'text', 'timestamp']

    def create(self, validated_data):
        sender_data = validated_data.pop('sender')
        user = User.objects.get(id=sender_data['id'])  # он должен уже существовать
        message = Message.objects.create(sender=user, **validated_data)
        return message