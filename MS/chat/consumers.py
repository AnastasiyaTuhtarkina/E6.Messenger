import json
from channels.generic.websocket import AsyncWebsocketConsumer



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_type = self.scope['url_route']['kwargs']['chat_type']
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'{self.chat_type}_{self.room_name}'

        # Присоединяем к группе чата
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Отключаемся от группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        # Обрабатываем входящее сообщение
        message = text_data_json.get('message', '')
        username = text_data_json.get('username', '')
        avatar = text_data_json.get('avatar', '')

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'avatar': avatar
            }
        )

    async def chat_message(self, event):
        # Получаем сообщение и дополнительную информацию
        message = event['message']
        username = event['username']
        avatar = event['avatar']

        # Отправляем сообщение всем участникам
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'avatar': avatar
        }))


    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        avatar = event['avatar']

        # Отправляем сообщение обратно клиенту
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
            'avatar': avatar
        }))
