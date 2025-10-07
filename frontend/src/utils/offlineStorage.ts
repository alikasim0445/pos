// utils/offlineStorage.ts
import { Sale } from '../types';

class OfflineStorage {
  private db: IDBDatabase | null = null;
  private dbName = 'POSOfflineDB';
  private version = 1;

  constructor() {
    this.initDB();
  }

  private initDB() {
    const request = indexedDB.open(this.dbName, this.version);

    request.onerror = () => {
      console.error('Failed to open IndexedDB:', request.error);
    };

    request.onsuccess = () => {
      this.db = request.result;
    };

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      
      // Create object stores for different types of data
      if (!db.objectStoreNames.contains('offlineSales')) {
        const salesStore = db.createObjectStore('offlineSales', { keyPath: 'id', autoIncrement: true });
        salesStore.createIndex('timestamp', 'timestamp', { unique: false });
        salesStore.createIndex('synced', 'synced', { unique: false });
      }

      if (!db.objectStoreNames.contains('offlineProducts')) {
        const productsStore = db.createObjectStore('offlineProducts', { keyPath: 'id' });
        productsStore.createIndex('name', 'name', { unique: false });
        productsStore.createIndex('barcode', 'barcode', { unique: true });
      }
    };
  }

  async saveOfflineSale(sale: any): Promise<number> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const transaction = this.db.transaction(['offlineSales'], 'readwrite');
      const store = transaction.objectStore('offlineSales');
      
      // Mark as not synced yet
      const saleToStore = {
        ...sale,
        synced: false,
        timestamp: new Date().toISOString(),
      };
      
      const request = store.add(saleToStore);
      
      request.onsuccess = () => {
        resolve(request.result as number);
      };
      
      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  async getOfflineSales(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const transaction = this.db.transaction(['offlineSales'], 'readonly');
      const store = transaction.objectStore('offlineSales');
      const request = store.getAll();
      
      request.onsuccess = () => {
        resolve(request.result);
      };
      
      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  async markSaleAsSynced(id: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const transaction = this.db.transaction(['offlineSales'], 'readwrite');
      const store = transaction.objectStore('offlineSales');
      
      const getRequest = store.get(id);
      getRequest.onsuccess = () => {
        const sale = getRequest.result;
        sale.synced = true;
        
        const updateRequest = store.put(sale);
        updateRequest.onsuccess = () => resolve();
        updateRequest.onerror = () => reject(updateRequest.error);
      };
      
      getRequest.onerror = () => {
        reject(getRequest.error);
      };
    });
  }

  async clearSyncedSales(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const transaction = this.db.transaction(['offlineSales'], 'readwrite');
      const store = transaction.objectStore('offlineSales');
      
      const index = store.index('synced');
      const request = index.openCursor(IDBKeyRange.only(true));
      
      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          resolve();
        }
      };
      
      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  async saveProductsForOffline(products: any[]): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const transaction = this.db.transaction(['offlineProducts'], 'readwrite');
      const store = transaction.objectStore('offlineProducts');
      
      // Clear existing products
      store.clear();

      // Add new products
      products.forEach(product => {
        store.add(product);
      });

      transaction.oncomplete = () => {
        resolve();
      };
      
      transaction.onerror = () => {
        reject(transaction.error);
      };
    });
  }

  async getProductByBarcode(barcode: string): Promise<any | null> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const transaction = this.db.transaction(['offlineProducts'], 'readonly');
      const store = transaction.objectStore('offlineProducts');
      const index = store.index('barcode');
      const request = index.get(barcode);
      
      request.onsuccess = () => {
        resolve(request.result || null);
      };
      
      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  async getProductsForOffline(): Promise<any[]> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        reject(new Error('Database not initialized'));
        return;
      }

      const transaction = this.db.transaction(['offlineProducts'], 'readonly');
      const store = transaction.objectStore('offlineProducts');
      const request = store.getAll();
      
      request.onsuccess = () => {
        resolve(request.result);
      };
      
      request.onerror = () => {
        reject(request.error);
      };
    });
  }
}

export default new OfflineStorage();