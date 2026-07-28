import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"
        self.user = self.scope['user']

        # Reject if not logged in
        
        if not self.user.is_authenticated:
            await self.close()
            return

        # Check user belongs to this conversation
        
        belongs = await self.user_belongs_to_conversation()
        if not belongs:
            await self.close()
            return

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')

        if msg_type == 'file':
            # File was already saved via HTTP upload
            # Just broadcast to the group so other person sees it
            await self.channel_layer.group_send
            (
                self.room_group_name,
                {
                    'type': 'chat_file',
                    'file_url': data['file_url'],
                    'file_type': data['file_type'],
                    'original_name': data['original_name'],
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'timestamp': data['timestamp'],
                }
            )

        elif data.get('signal'):
            # video signal — just forward to group, no DB saving
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_signal',
                    'signal_data': data,
                    'sender_id': self.user.id,
                }
            )

        else:    
            message_body = data.get('message', '').strip()

            if not message_body:
                return

            # Save to database
            message = await self.save_message(message_body)

            # Broadcast to everyone in the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_body,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'timestamp': message.created_at.strftime('%d %b %Y, %I:%M %p'),
                    'message_id': message.id,
                }
            )

    # This is called when group_send fires
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id'],
        }))

    async def chat_file(self, event):
        await self.send(text_data=json.dumps({
            'type': 'file',
            'file_url': event['file_url'],
            'file_type': event['file_type'],
            'original_name': event['original_name'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
        }))
    # --- Database helpers (sync → async) 

    @database_sync_to_async
    def user_belongs_to_conversation(self):
        from apps.bookings.models import Conversation
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            return self.user == conv.student or self.user == conv.teacher
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, body):
        from apps.bookings.models import Conversation, Message
        from apps.notifications.models import Notification
        conv = Conversation.objects.get(id=self.conversation_id)

        message = Message.objects.create(
            conversation=conv,
            sender=self.user,
            body=body,
        )

        # Notify the other person
        recipient = conv.teacher if self.user == conv.student else conv.student
        Notification.objects.create(
            user=recipient,
            type='message',
            title='New message',
            body=f'You received a new message in "{conv.job.title}".',
        )

        return message
    


    async def video_signal(self, event):
        # Don't send signal back to the person who sent it
        if event['sender_id'] == self.user.id:
            return
        
        await self.send(text_data=json.dumps(event['signal_data']))

