import React, { useState, useEffect } from 'react';
import { fetchProducts, processSale } from '../services/api';
import ProductList from './ProductList';
import WarehouseSelector from './WarehouseSelector';

const POSTerminal: React.FC = () => {
    const [products, setProducts] = useState([]);
    const [selectedProducts, setSelectedProducts] = useState([]);
    const [warehouseId, setWarehouseId] = useState(null);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        const loadProducts = async () => {
            const productData = await fetchProducts();
            setProducts(productData);
        };
        loadProducts();
    }, []);

    const handleProductSelect = (product) => {
        setSelectedProducts((prev) => [...prev, product]);
        setTotal((prev) => prev + product.price);
    };

    const handleSaleProcess = async () => {
        if (warehouseId && selectedProducts.length > 0) {
            await processSale({ warehouseId, products: selectedProducts });
            // Reset state after processing sale
            setSelectedProducts([]);
            setTotal(0);
        } else {
            alert('Please select a warehouse and at least one product.');
        }
    };

    return (
        <div>
            <h1>Point of Sale Terminal</h1>
            <WarehouseSelector onSelect={setWarehouseId} />
            <ProductList products={products} onSelect={handleProductSelect} />
            <h2>Total: ${total.toFixed(2)}</h2>
            <button onClick={handleSaleProcess}>Process Sale</button>
        </div>
    );
};

export default POSTerminal;