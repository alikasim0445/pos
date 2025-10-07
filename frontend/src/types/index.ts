export interface Product {
  id: number;
  name: string;
  price: number;
  quantity: number;
  warehouseId: number;
}

export interface Warehouse {
  id: number;
  name: string;
  location: string;
  capacity: number;
}

export interface Sale {
  id: number;
  productId: number;
  quantity: number;
  totalPrice: number;
  date: string;
}

export interface User {
  id: number;
  username?: string;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
  profile?: {
    role: string;
  };
}

export interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}