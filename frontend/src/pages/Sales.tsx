import React, { useEffect, useState } from 'react';
import { fetchSalesData } from '../services/api';
import POSTerminal from '../components/POSTerminal';
import ProductList from '../components/ProductList';

const Sales: React.FC = () => {
    const [salesData, setSalesData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadSalesData = async () => {
            try {
                const data = await fetchSalesData();
                setSalesData(data);
            } catch (error) {
                console.error('Error fetching sales data:', error);
            } finally {
                setLoading(false);
            }
        };

        loadSalesData();
    }, []);

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h1>Sales Management</h1>
            <POSTerminal salesData={salesData} />
            <ProductList salesData={salesData} />
        </div>
    );
};

export default Sales;