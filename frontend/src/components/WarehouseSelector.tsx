import React, { useEffect, useState } from 'react';
import { fetchWarehouses } from '../services/api';

const WarehouseSelector: React.FC<{ onSelect: (warehouseId: string) => void }> = ({ onSelect }) => {
    const [warehouses, setWarehouses] = useState<{ id: string; name: string }[]>([]);
    const [selectedWarehouse, setSelectedWarehouse] = useState<string | null>(null);

    useEffect(() => {
        const loadWarehouses = async () => {
            const data = await fetchWarehouses();
            setWarehouses(data);
        };

        loadWarehouses();
    }, []);

    const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const warehouseId = event.target.value;
        setSelectedWarehouse(warehouseId);
        onSelect(warehouseId);
    };

    return (
        <div>
            <label htmlFor="warehouse-selector">Select Warehouse:</label>
            <select id="warehouse-selector" value={selectedWarehouse || ''} onChange={handleChange}>
                <option value="" disabled>Select a warehouse</option>
                {warehouses.map(warehouse => (
                    <option key={warehouse.id} value={warehouse.id}>
                        {warehouse.name}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default WarehouseSelector;