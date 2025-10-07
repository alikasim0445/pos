import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Alert,
  IconButton,
} from '@mui/material';
import { Edit as EditIcon } from '@mui/icons-material';

interface ProductListProps {
  products: any[];
  onSelect?: (product: any) => void;
  onEdit?: (product: any) => void;
  loading?: boolean;
  error?: string | null;
}

const ProductList: React.FC<ProductListProps> = ({ 
  products, 
  onSelect, 
  onEdit,
  loading = false, 
  error = null 
}) => {
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Product List
      </Typography>
      <Grid container spacing={2}>
        {products.map((product) => (
          <Grid item xs={12} sm={6} md={4} key={product.id}>
            <Card 
              onClick={onSelect ? () => onSelect(product) : undefined}
              style={{ 
                cursor: onSelect ? 'pointer' : 'default',
                opacity: onSelect ? 1 : 0.7,
              }}
            >
              <CardContent>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <Typography variant="h6" component="h3">
                      {product.name}
                    </Typography>
                    <Typography color="textSecondary">
                      SKU: {product.sku}
                    </Typography>
                    <Typography variant="h6" color="primary">
                      ${product.price}
                    </Typography>
                    {product.category && (
                      <Typography variant="body2" color="textSecondary">
                        Category: {typeof product.category === 'object' ? product.category.name : product.category}
                      </Typography>
                    )}
                  </div>
                  {onEdit && (
                    <IconButton 
                      size="small" 
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit(product);
                      }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  )}
                </div>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default ProductList;