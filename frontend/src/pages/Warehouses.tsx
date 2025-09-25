import React, { useEffect, useState } from 'react';
import { fetchWarehouses } from '../services/api';

const Warehouses: React.FC = () => {
    const [warehouses, setWarehouses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const loadWarehouses = async () => {
            try {
                const data = await fetchWarehouses();
                setWarehouses(data);
            } catch (err) {
                setError('Failed to load warehouses');
            } finally {
                setLoading(false);
            }
        };

        loadWarehouses();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    if (error) {
        return <div>{error}</div>;
    }

    return (
        <div>
            <h1>Warehouses</h1>
            <ul>
                {warehouses.map((warehouse) => (
                    <li key={warehouse.id}>{warehouse.name}</li>
                ))}
            </ul>
        </div>
    );
};

export default Warehouses;