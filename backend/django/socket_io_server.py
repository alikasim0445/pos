import socketio
import os
import django
from django.contrib.auth import get_user_model
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')
django.setup()

# Initialize Django models access
User = get_user_model()

# Create a Socket.IO server instance
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = socketio.ASGIApp(sio)

# Store connected users and their rooms
connected_users = {}

@sio.event
async def connect(sid, environ, auth):
    """Handle new connections"""
    print(f"Client {sid} connected")
    
    # Extract token from query string or headers
    query_string = environ.get('QUERY_STRING', '')
    token = None
    
    # Parse query string for token
    if 'token=' in query_string:
        import urllib.parse
        params = urllib.parse.parse_qs(query_string)
        token = params.get('token', [None])[0]
    
    # For now, we'll just acknowledge the connection
    # In a real implementation, you would validate the JWT token here
    connected_users[sid] = {
        'authenticated': True,  # For now, assume all connections are valid
        'sid': sid
    }
    
    # Join default rooms
    await sio.enter_room(sid, 'products')
    await sio.enter_room(sid, 'sales')
    await sio.enter_room(sid, 'inventory')
    await sio.enter_room(sid, 'warehouses')
    
    print(f"Client {sid} joined rooms: products, sales, inventory, warehouses")

@sio.event
async def disconnect(sid):
    """Handle disconnections"""
    print(f"Client {sid} disconnected")
    if sid in connected_users:
        del connected_users[sid]

@sio.on('subscribe_products')
async def handle_subscribe_products(sid, data):
    """Handle product subscription"""
    await sio.enter_room(sid, 'products')
    await sio.emit('subscription_success', {'message': 'Subscribed to product updates'}, room=sid)

@sio.on('subscribe_sales')
async def handle_subscribe_sales(sid, data):
    """Handle sales subscription"""
    await sio.enter_room(sid, 'sales')
    await sio.emit('subscription_success', {'message': 'Subscribed to sale updates'}, room=sid)

@sio.on('subscribe_inventory')
async def handle_subscribe_inventory(sid, data):
    """Handle inventory subscription"""
    await sio.enter_room(sid, 'inventory')
    await sio.emit('subscription_success', {'message': 'Subscribed to inventory updates'}, room=sid)

@sio.on('subscribe_warehouses')
async def handle_subscribe_warehouses(sid, data):
    """Handle warehouse subscription"""
    await sio.enter_room(sid, 'warehouses')
    await sio.emit('subscription_success', {'message': 'Subscribed to warehouse updates'}, room=sid)

@sio.on('product_update')
async def handle_product_update(sid, data):
    """Handle product update events"""
    action = data.get('action', 'update')
    product = data.get('product', {})
    
    # Broadcast to all clients in the products room
    await sio.emit('product_update', {'action': action, 'product': product}, room='products')

@sio.on('sale_update')
async def handle_sale_update(sid, data):
    """Handle sale update events"""
    action = data.get('action', 'update')
    sale = data.get('sale', {})
    
    # Broadcast to all clients in the sales room
    await sio.emit('sale_update', {'action': action, 'sale': sale}, room='sales')

@sio.on('inventory_update')
async def handle_inventory_update(sid, data):
    """Handle inventory update events"""
    action = data.get('action', 'update')
    inventory = data.get('inventory', {})
    
    # Broadcast to all clients in the inventory room
    await sio.emit('inventory_update', {'action': action, 'inventory': inventory}, room='inventory')

@sio.on('warehouse_update')
async def handle_warehouse_update(sid, data):
    """Handle warehouse update events"""
    action = data.get('action', 'update')
    warehouse = data.get('warehouse', {})
    
    # Broadcast to all clients in the warehouses room
    await sio.emit('warehouse_update', {'action': action, 'warehouse': warehouse}, room='warehouses')

if __name__ == '__main__':
    import eventlet
    eventlet.wsgi.server(eventlet.listen(('', 8001)), app)