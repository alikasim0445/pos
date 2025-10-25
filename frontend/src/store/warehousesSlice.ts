// store/warehousesSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Warehouse {
  id: number;
  name: string;
  location: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  capacity: number;
  is_active: boolean;
  created_at: string;
}

interface WarehousesState {
  warehouses: Warehouse[];
  loading: boolean;
  error: string | null;
}

const initialState: WarehousesState = {
  warehouses: [],
  loading: false,
  error: null,
};

const warehousesSlice = createSlice({
  name: 'warehouses',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setWarehouses: (state, action: PayloadAction<Warehouse[]>) => {
      state.warehouses = action.payload;
      state.loading = false;
      state.error = null;
    },
    addWarehouse: (state, action: PayloadAction<Warehouse>) => {
      // Check if warehouse with same ID already exists in the state to prevent duplicates
      const existingIndex = state.warehouses.findIndex(w => w.id === action.payload.id);
      if (existingIndex === -1) {
        // Only add if it doesn't already exist
        state.warehouses.unshift(action.payload);
      } else {
        // If it exists, update it instead to ensure latest data
        state.warehouses[existingIndex] = action.payload;
      }
    },
    updateWarehouse: (state, action: PayloadAction<Warehouse>) => {
      const index = state.warehouses.findIndex(w => w.id === action.payload.id);
      if (index !== -1) {
        state.warehouses[index] = action.payload;
      }
    },
    deleteWarehouse: (state, action: PayloadAction<number>) => {
      state.warehouses = state.warehouses.filter(w => w.id !== action.payload);
    },
  },
});

export const { 
  setLoading, 
  setError, 
  setWarehouses, 
  addWarehouse, 
  updateWarehouse, 
  deleteWarehouse 
} = warehousesSlice.actions;

export default warehousesSlice.reducer;