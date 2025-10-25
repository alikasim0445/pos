import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import productsReducer from './productsSlice';
import salesReducer from './salesSlice';
import inventoryReducer from './inventorySlice';
import warehousesReducer from './warehousesSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    products: productsReducer,
    sales: salesReducer,
    inventory: inventoryReducer,
    warehouses: warehousesReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types during serialization checks
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;