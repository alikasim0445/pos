export interface ProductVariant {
  id: number;
  name: string;
  sku: string;
  additional_price: number;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  barcode: string;
  description: string;
  price: number;
  category: number;
  variants: ProductVariant[];
  is_active: boolean;
  image: string;
  tags: string;
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
    permissions?: string[];  // Add permissions array
  };
}

export interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

// Customer interfaces
export interface Customer {
  id: number;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  loyalty_points: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerPurchaseHistory {
  id: number;
  name: string;
  email?: string;
  phone?: string;
}

export interface SaleItem {
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Payment {
  method: string;
  amount: number;
  reference?: string;
}

export interface SaleHistory {
  id: number;
  receipt_number: string;
  sale_date: string;
  total_amount: number;
  payment_status: string;
  items: SaleItem[];
  payments: Payment[];
}

export interface Transfer {
  id: number;
  transfer_number: string;
  from_warehouse: Warehouse;
  from_location?: number | null;
  from_bin?: number | null;
  to_warehouse: Warehouse;
  to_location?: number | null;
  to_bin?: number | null;
  requested_by?: User;
  approved_by?: User;
  status: 'draft' | 'requested' | 'approved' | 'in_transit' | 'received' | 'rejected' | 'cancelled';
  notes: string;
  requested_at: string;
  approved_at?: string | null;
  received_at?: string | null;
  completed_at?: string | null;
  lines: TransferLine[];
  from_warehouse_name?: string;
  from_location_name?: string;
  from_bin_name?: string;
  to_warehouse_name?: string;
  to_location_name?: string;
  to_bin_name?: string;
  requested_by_name?: string;
  approved_by_name?: string;
}

export interface TransferLine {
  id: number;
  transfer: number;
  product: number;
  variant?: number | null;
  requested_qty: number;
  transferred_qty: number;
  received_qty: number;
  from_inventory?: number | null;
}

export interface Reservation {
  id: number;
  reservation_number: string;
  user: number;
  user_name: string;
  warehouse: number;
  warehouse_name: string;
  status: string;
  created_at: string;
  expires_at: string;
  notes: string;
  lines: ReservationLine[];
}

export interface ReservationLine {
  id: number;
  product: number;
  product_name: string;
  variant: number | null;
  variant_name: string | null;
  quantity: number;
}