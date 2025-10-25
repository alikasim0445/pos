import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class POSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is authenticated
        if self.scope["user"].is_anonymous:
            logger.warning("WebSocket connection rejected: User not authenticated")
            await self.close(code=4001)  # Custom close code for unauthenticated
            return
        
        try:
            # Accept the connection first
            await self.accept()
            
            # Add to general groups
            await self.channel_layer.group_add("products", self.channel_name)
            await self.channel_layer.group_add("sales", self.channel_name)
            await self.channel_layer.group_add("inventory", self.channel_name)
            await self.channel_layer.group_add("warehouses", self.channel_name)
            
            logger.info(f"WebSocket connected for user: {self.scope['user'].username}")
            
            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'WebSocket connection established successfully'
            }))
            
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {e}")
            await self.close(code=4002)

    async def disconnect(self, close_code):
        # Remove from groups
        try:
            await self.channel_layer.group_discard("products", self.channel_name)
            await self.channel_layer.group_discard("sales", self.channel_name)
            await self.channel_layer.group_discard("inventory", self.channel_name)
            await self.channel_layer.group_discard("warehouses", self.channel_name)
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection: {e}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', '')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'pong'
                }))
            elif message_type.startswith('subscribe_'):
                channel = message_type.replace('subscribe_', '')
                await self.send(text_data=json.dumps({
                    'type': 'subscription_success',
                    'message': f'Subscribed to {channel} updates'
                }))
                logger.info(f"Client subscribed to {channel}")
            else:
                # Handle other message types
                logger.warning(f"Received unhandled message type: {message_type}")
                await self.send(text_data=json.dumps({
                    'type': 'message_received',
                    'message': f'Received: {message_type}'
                }))

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    # Product update handler
    async def product_update_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'product_update',
            'product': event['product'],
            'action': event['action']
        }))

    # Sale update handler
    async def sale_update_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'sale_update',
            'sale': event['sale'],
            'action': event['action']
        }))

    # Inventory update handler
    async def inventory_update_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'inventory_update',
            'inventory': event['inventory'],
            'action': event['action']
        }))

    # Warehouse update handler
    async def warehouse_update_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'warehouse_update',
            'warehouse': event['warehouse'],
            'action': event['action']
        }))