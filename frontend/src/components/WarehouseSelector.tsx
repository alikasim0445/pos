import React, { useState } from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
} from '@mui/material';

interface Warehouse {
  id: number;
  name: string;
}

interface WarehouseSelectorProps {
  warehouses: Warehouse[];
  onSelect: (warehouseId: number) => void;
}

const WarehouseSelector: React.FC<WarehouseSelectorProps> = ({ warehouses, onSelect }) => {
    const [selectedWarehouse, setSelectedWarehouse] = useState<number | null>(null);

    const handleChange = (event: any) => {
        const warehouseId = Number(event.target.value);
        setSelectedWarehouse(warehouseId);
        onSelect(warehouseId);
    };

    return (
        <Box mb={2}>
            <FormControl fullWidth>
                <InputLabel id="warehouse-select-label">Select Warehouse</InputLabel>
                <Select
                    labelId="warehouse-select-label"
                    id="warehouse-select"
                    value={selectedWarehouse || ''}
                    label="Select Warehouse"
                    onChange={handleChange}
                >
                    <MenuItem value="" disabled>
                        Select a warehouse
                    </MenuItem>
                    {warehouses.map((warehouse) => (
                        <MenuItem key={warehouse.id} value={warehouse.id}>
                            {warehouse.name}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
        </Box>
    );
};

export default WarehouseSelector;