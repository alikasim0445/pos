// store/productsSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Product {
  id: number;
  name: string;
  sku: string;
  barcode: string | null;
  description: string;
  category: number | null;
  price: number;
  cost_price: number | null;
  wholesale_price: number | null;
  min_wholesale_qty: number;
  effective_date?: string;
  image: string | null;
  tags: string;
}

interface ProductsState {
  products: Product[];
  loading: boolean;
  error: string | null;
}

const initialState: ProductsState = {
  products: [],
  loading: false,
  error: null,
};

const productsSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setProducts: (state, action: PayloadAction<Product[]>) => {
      state.products = action.payload;
      state.loading = false;
      state.error = null;
    },
    addProduct: (state, action: PayloadAction<Product>) => {
      // Check if product with same ID already exists in the state to prevent duplicates
      const existingIndex = state.products.findIndex(p => p.id === action.payload.id);
      if (existingIndex === -1) {
        // Only add if it doesn't already exist
        state.products.unshift(action.payload);
      } else {
        // If it exists, update it instead to ensure latest data
        state.products[existingIndex] = action.payload;
      }
    },
    updateProduct: (state, action: PayloadAction<Product>) => {
      const index = state.products.findIndex(p => p.id === action.payload.id);
      if (index !== -1) {
        state.products[index] = action.payload;
      }
    },
    deleteProduct: (state, action: PayloadAction<number>) => {
      state.products = state.products.filter(p => p.id !== action.payload);
    },
  },
});

export const { 
  setLoading, 
  setError, 
  setProducts, 
  addProduct, 
  updateProduct, 
  deleteProduct 
} = productsSlice.actions;

export default productsSlice.reducer;