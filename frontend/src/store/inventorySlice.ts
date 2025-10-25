// store/inventorySlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Inventory {
  id: number;
  product: number;
  variant: number | null;
  warehouse: number;
  location: number | null;
  bin: number | null;
  bin_location: string;
  qty_on_hand: number;
  qty_reserved: number;
  min_stock_level: number;
  last_updated: string;
  product_name?: string;
  warehouse_name?: string;
  location_name?: string;
  bin_name?: string;
  available_stock?: number;
}

interface InventoryState {
  inventory: Inventory[];
  loading: boolean;
  error: string | null;
}

const initialState: InventoryState = {
  inventory: [],
  loading: false,
  error: null,
};

const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setInventory: (state, action: PayloadAction<Inventory[]>) => {
      state.inventory = action.payload;
      state.loading = false;
      state.error = null;
    },
    addInventory: (state, action: PayloadAction<Inventory>) => {
      // Check if inventory with same ID already exists in the state to prevent duplicates
      const existingIndex = state.inventory.findIndex(i => i.id === action.payload.id);
      if (existingIndex === -1) {
        // Only add if it doesn't already exist
        state.inventory.unshift(action.payload);
      } else {
        // If it exists, update it instead to ensure latest data
        state.inventory[existingIndex] = action.payload;
      }
    },
    updateInventory: (state, action: PayloadAction<Inventory>) => {
      const index = state.inventory.findIndex(i => i.id === action.payload.id);
      if (index !== -1) {
        state.inventory[index] = action.payload;
      }
    },
    deleteInventory: (state, action: PayloadAction<number>) => {
      state.inventory = state.inventory.filter(i => i.id !== action.payload);
    },
  },
});

export const { 
  setLoading, 
  setError, 
  setInventory, 
  addInventory, 
  updateInventory, 
  deleteInventory 
} = inventorySlice.actions;

export default inventorySlice.reducer;