// store/salesSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Sale {
  id: number;
  receipt_number: string;
  cashier: number;
  customer: number | null;
  warehouse: number;
  total_amount: number;
  tax_amount: number;
  discount_amount: number;
  payment_status: string;
  sale_date: string;
}

interface SalesState {
  sales: Sale[];
  loading: boolean;
  error: string | null;
}

const initialState: SalesState = {
  sales: [],
  loading: false,
  error: null,
};

const salesSlice = createSlice({
  name: 'sales',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setSales: (state, action: PayloadAction<Sale[]>) => {
      state.sales = action.payload;
      state.loading = false;
      state.error = null;
    },
    addSale: (state, action: PayloadAction<Sale>) => {
      // Check if sale with same ID already exists in the state to prevent duplicates
      const existingIndex = state.sales.findIndex(s => s.id === action.payload.id);
      if (existingIndex === -1) {
        // Only add if it doesn't already exist
        state.sales.unshift(action.payload);
      } else {
        // If it exists, update it instead to ensure latest data
        state.sales[existingIndex] = action.payload;
      }
    },
    updateSale: (state, action: PayloadAction<Sale>) => {
      const index = state.sales.findIndex(s => s.id === action.payload.id);
      if (index !== -1) {
        state.sales[index] = action.payload;
      }
    },
    deleteSale: (state, action: PayloadAction<number>) => {
      state.sales = state.sales.filter(s => s.id !== action.payload);
    },
  },
});

export const { 
  setLoading, 
  setError, 
  setSales, 
  addSale, 
  updateSale, 
  deleteSale 
} = salesSlice.actions;

export default salesSlice.reducer;