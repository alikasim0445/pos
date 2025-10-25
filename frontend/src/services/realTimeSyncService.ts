// services/realTimeSyncService.ts
import { store } from '../store/store'
import { addProduct, updateProduct, deleteProduct } from '../store/productsSlice';
import { addSale, updateSale, deleteSale } from '../store/salesSlice';
import { addInventory, updateInventory, deleteInventory } from '../store/inventorySlice';
import { addWarehouse, updateWarehouse, deleteWarehouse } from '../store/warehousesSlice';

class RealTimeSyncService {
  private socket: WebSocket | null = null;
  private isConnected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private connectionTimeout: NodeJS.Timeout | null = null;
  private onConnectionChangeCallbacks: ((connected: boolean) => void)[] = [];

  connect() {
    // Clear any existing connection
    this.disconnect();

    // Get the server URL from environment variables or use default
    const serverUrl = import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8000';
    
    // Get JWT token from localStorage - handle different storage scenarios
    let token: string | null = null;
    
    try {
      // Try multiple possible token storage locations
      token = localStorage.getItem('token') || 
               localStorage.getItem('access_token') ||
               localStorage.getItem('jwt_token');
      
      // If token looks like an object, try to parse it
      if (token && token.startsWith('{')) {
        try {
          const tokenObj = JSON.parse(token);
          token = tokenObj.access || tokenObj.token || token;
        } catch {
          // If parsing fails, use the original token
        }
      }

      // Validate token format (basic JWT format check)
      if (token && !this.isValidJWT(token)) {
        console.warn('Token format appears invalid:', token);
        token = null;
      }
    } catch (error) {
      console.error('Error retrieving token:', error);
      token = null;
    }

    // Construct WebSocket URL with token as query parameter
    const url = new URL(serverUrl.replace('http', 'ws'));
    url.pathname = '/ws/socket-server/';
    let cleanToken: string | null = null;

    if (token) {
      // Clean the token - remove any quotes or special characters
      cleanToken = token.replace(/['"']/g, '');
      url.searchParams.set('token', cleanToken);
    } else {
      console.warn('No valid JWT token found. WebSocket connection may fail due to authentication requirement.');
    }
    const wsUrl = url.href;

    console.log('Attempting WebSocket connection to:', wsUrl.replace(cleanToken ? encodeURIComponent(cleanToken) : '', '[TOKEN]'));
    
    try {
      this.socket = new WebSocket(wsUrl);

      // Set connection timeout
      this.connectionTimeout = setTimeout(() => {
        if (!this.isConnected && this.socket) {
          console.error('WebSocket connection timeout');
          this.socket.close();
        }
      }, 5000);

      this.socket.onopen = (event) => {
        console.log('✅ Successfully connected to real-time sync server');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        
        // Clear connection timeout
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout);
          this.connectionTimeout = null;
        }
        
        // Start ping interval
        this.startPingInterval();
        
        // Notify connection change
        this.notifyConnectionChange(true);
        
        // Subscribe to relevant channels after connection
        setTimeout(() => {
          this.subscribeToUpdates();
        }, 100);
      };

      this.socket.onclose = (event) => {
        console.log('🔌 Disconnected from real-time sync server:', event.code, event.reason);
        this.isConnected = false;
        
        // Clear intervals and timeouts
        this.stopPingInterval();
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout);
          this.connectionTimeout = null;
        }
        
        // Notify connection change
        this.notifyConnectionChange(false);
        
        // Attempt to reconnect if it wasn't a manual disconnect
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000); // Exponential backoff with max 30s
          console.log(`🔄 Attempting to reconnect in ${delay}ms... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
          
          this.reconnectTimeout = setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
          }, delay);
        } else if (event.code !== 1000) {
          console.error('❌ Max reconnection attempts reached');
        }
      };

      this.socket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        // The error event is usually followed by a close event, so we don't need to handle reconnection here
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket message received:', data);
          
          this.handleWebSocketMessage(data);
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error, event.data);
        }
      };

    } catch (error) {
      console.error('❌ Failed to create WebSocket connection:', error);
      this.handleConnectionFailure();
    }
  }

  private handleWebSocketMessage(data: any) {
    // Handle different types of messages
    switch(data.type) {
      case 'connection_established':
        console.log('✅ WebSocket connection confirmed:', data.message);
        break;
        
      case 'pong':
        // Response to our ping, connection is healthy
        break;
        
      case 'product_update':
        console.log('📦 Product update received:', data);
        this.handleProductUpdate(data);
        break;
        
      case 'sale_update':
        console.log('💰 Sale update received:', data);
        this.handleSaleUpdate(data);
        break;
        
      case 'inventory_update':
        console.log('📊 Inventory update received:', data);
        this.handleInventoryUpdate(data);
        break;
        
      case 'warehouse_update':
        console.log('🏭 Warehouse update received:', data);
        this.handleWarehouseUpdate(data);
        break;
        
      case 'subscription_success':
        console.log('✅ Subscription confirmed:', data.message);
        break;
        
      case 'error':
        console.error('❌ WebSocket error message:', data.message);
        break;
        
      default:
        console.log('❓ Unknown message type:', data.type, data);
    }
  }

  private handleProductUpdate(data: any) {
    switch(data.action) {
      case 'update':
        store.dispatch(updateProduct(data.product));
        break;
      case 'create':
        store.dispatch(addProduct(data.product));
        break;
      case 'delete':
        store.dispatch(deleteProduct(data.productId || data.product?.id));
        break;
      default:
        console.warn('Unknown product action:', data.action);
    }
  }

  private handleSaleUpdate(data: any) {
    switch(data.action) {
      case 'update':
        store.dispatch(updateSale(data.sale));
        break;
      case 'create':
        store.dispatch(addSale(data.sale));
        break;
      case 'delete':
        store.dispatch(deleteSale(data.saleId || data.sale?.id));
        break;
      default:
        console.warn('Unknown sale action:', data.action);
    }
  }

  private handleInventoryUpdate(data: any) {
    switch(data.action) {
      case 'update':
        store.dispatch(updateInventory(data.inventory));
        break;
      case 'create':
        store.dispatch(addInventory(data.inventory));
        break;
      case 'delete':
        store.dispatch(deleteInventory(data.inventoryId || data.inventory?.id));
        break;
      default:
        console.warn('Unknown inventory action:', data.action);
    }
  }

  private handleWarehouseUpdate(data: any) {
    switch(data.action) {
      case 'update':
        store.dispatch(updateWarehouse(data.warehouse));
        break;
      case 'create':
        store.dispatch(addWarehouse(data.warehouse));
        break;
      case 'delete':
        store.dispatch(deleteWarehouse(data.warehouseId || data.warehouse?.id));
        break;
      default:
        console.warn('Unknown warehouse action:', data.action);
    }
  }

  private startPingInterval() {
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.socket && this.isConnected && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private isValidJWT(token: string): boolean {
    // Basic JWT format validation (3 parts separated by dots)
    const parts = token.split('.');
    return parts.length === 3 && 
           parts.every(part => part.length > 0) &&
           /^[A-Za-z0-9_-]+$/.test(parts[0]) &&
           /^[A-Za-z0-9_-]+$/.test(parts[1]);
  }

  private handleConnectionFailure() {
    this.isConnected = false;
    this.notifyConnectionChange(false);
    
    // Attempt reconnect
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = 1000 * (this.reconnectAttempts + 1);
      console.log(`🔄 Scheduling reconnect in ${delay}ms due to connection failure...`);
      
      this.reconnectTimeout = setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, delay);
    }
  }

  private notifyConnectionChange(connected: boolean) {
    this.onConnectionChangeCallbacks.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        console.error('Error in connection change callback:', error);
      }
    });
  }

  disconnect() {
    console.log('🛑 Disconnecting WebSocket...');
    
    // Clear all timeouts and intervals
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.stopPingInterval();
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
    
    // Close WebSocket connection
    if (this.socket) {
      this.socket.close(1000, "Manual disconnect");
      this.socket = null;
    }
    
    this.isConnected = false;
    this.notifyConnectionChange(false);
  }

  private subscribeToUpdates() {
    if (this.socket && this.isConnected && this.socket.readyState === WebSocket.OPEN) {
      const subscriptions = [
        'subscribe_products',
        'subscribe_sales', 
        'subscribe_inventory',
        'subscribe_warehouses'
      ];
      
      subscriptions.forEach(subscription => {
        this.socket!.send(JSON.stringify({ type: subscription }));
      });
      
      console.log('✅ Subscribed to all update channels');
    } else {
      console.warn('⚠️ Cannot subscribe - WebSocket not connected');
    }
  }

  // Public method to check connection status
  getStatus(): boolean {
    return this.isConnected;
  }

  // Method to add connection status listeners
  onConnectionChange(callback: (connected: boolean) => void) {
    this.onConnectionChangeCallbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      const index = this.onConnectionChangeCallbacks.indexOf(callback);
      if (index > -1) {
        this.onConnectionChangeCallbacks.splice(index, 1);
      }
    };
  }

  // Method to manually trigger reconnection
  reconnect() {
    console.log('🔄 Manual reconnection triggered');
    this.reconnectAttempts = 0;
    this.connect();
  }

  // Send updates to the server
  sendProductUpdate(action: string, product: any) {
    this.sendUpdate('product_update', action, product);
  }

  sendSaleUpdate(action: string, sale: any) {
    this.sendUpdate('sale_update', action, sale);
  }

  sendInventoryUpdate(action: string, inventory: any) {
    this.sendUpdate('inventory_update', action, inventory);
  }

  sendWarehouseUpdate(action: string, warehouse: any) {
    this.sendUpdate('warehouse_update', action, warehouse);
  }

  private sendUpdate(type: string, action: string, data: any) {
    if (this.socket && this.isConnected && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ 
        type, 
        action, 
        [type.split('_')[0]]: data // product, sale, inventory, or warehouse
      }));
    } else {
      console.warn(`⚠️ Cannot send ${type} - WebSocket not connected`);
    }
  }
}

// Create and export singleton instance
export default new RealTimeSyncService();