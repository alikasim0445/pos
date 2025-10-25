import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardMedia,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Alert,
  IconButton,
  Chip,
  Tooltip,
  Badge,
  CardActionArea,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  LocalOffer as OfferIcon,
  Inventory as StockIcon,
  Category as CategoryIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

interface ProductListProps {
  products: any[];
  onSelect?: (product: any) => void;
  onEdit?: (product: any) => void;
  onDelete?: (productId: number) => void;
  loading?: boolean;
  error?: string | null;
}

const ProductList: React.FC<ProductListProps> = ({
  products,
  onSelect,
  onEdit,
  onDelete,
  loading = false,
  error = null,
}) => {
  const [quickViewProduct, setQuickViewProduct] = useState<any>(null);
  const [imageLoadError, setImageLoadError] = useState<{[key: number]: boolean}>({});
  
  const theme = useTheme();
  const isXs = useMediaQuery(theme.breakpoints.only('xs'));
  const isSm = useMediaQuery(theme.breakpoints.only('sm'));
  const isMd = useMediaQuery(theme.breakpoints.only('md'));
  const isLg = useMediaQuery(theme.breakpoints.only('lg'));
  const isXl = useMediaQuery(theme.breakpoints.only('xl'));

  // Determine grid columns based on screen size
  let gridColumns;
  if (isXs) gridColumns = 2;      // 2 cards per row on extra small screens
  else if (isSm) gridColumns = 3; // 3 cards per row on small screens
  else if (isMd) gridColumns = 4; // 4 cards per row on medium screens
  else if (isLg) gridColumns = 5; // 5 cards per row on large screens
  else gridColumns = 6;           // 6 cards per row on extra large screens

  const gridSize = 5;

  // Function to get the full image URL
  const getImageUrl = (image: string | null) => {
    if (!image) return null;
    
    if (image.startsWith('http')) {
      return image;
    }
    
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${image}`;
  };

  // Calculate discount percentage
  const getDiscountPercentage = (price: number, wholesalePrice: number) => {
    if (!wholesalePrice || wholesalePrice >= price) return 0;
    return Math.round(((price - wholesalePrice) / price) * 100);
  };

  // Handle image load error
  const handleImageError = (productId: number) => {
    setImageLoadError(prev => ({ ...prev, [productId]: true }));
  };

  // Quick view dialog
  const QuickViewDialog = () => (
    <Dialog
      open={!!quickViewProduct}
      onClose={() => setQuickViewProduct(null)}
      maxWidth="sm"
      fullWidth
    >
      {quickViewProduct && (
        <>
          <DialogTitle sx={{ pb: 1 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6" sx={{ fontSize: '1.1rem' }}>
                {quickViewProduct.name}
              </Typography>
              <IconButton 
                size="small" 
                onClick={() => setQuickViewProduct(null)}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          </DialogTitle>
          <DialogContent sx={{ pt: 1 }}>
            <Box sx={{ textAlign: 'center', mb: 2 }}>
              {getImageUrl(quickViewProduct.image) && !imageLoadError[quickViewProduct.id] ? (
                <CardMedia
                  component="img"
                  image={getImageUrl(quickViewProduct.image)}
                  alt={quickViewProduct.name}
                  sx={{
                    width: '100%',
                    maxWidth: 300,
                    height: 'auto',
                    maxHeight: 200,
                    objectFit: 'contain',
                    borderRadius: 1,
                    mb: 2,
                    mx: 'auto',
                  }}
                  onError={() => handleImageError(quickViewProduct.id)}
                />
              ) : (
                <Box
                  sx={{
                    height: 180,
                    backgroundColor: 'grey.100',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 1,
                    mb: 2,
                  }}
                >
                  <Typography color="textSecondary">No Image</Typography>
                </Box>
              )}
            </Box>

            <Typography variant="body2" color="textSecondary" gutterBottom>
              SKU: {quickViewProduct.sku}
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="h6" color="primary" fontWeight="bold">
                ${parseFloat(quickViewProduct.price).toFixed(2)}
              </Typography>
              {quickViewProduct.wholesale_price && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                  <Typography variant="body2" color="success.main">
                    Wholesale: ${parseFloat(quickViewProduct.wholesale_price).toFixed(2)}
                  </Typography>
                  <Chip
                    label={`${getDiscountPercentage(
                      parseFloat(quickViewProduct.price),
                      parseFloat(quickViewProduct.wholesale_price)
                    )}% OFF`}
                    size="small"
                    color="success"
                  />
                </Box>
              )}
            </Box>

            {quickViewProduct.description && (
              <Typography variant="body2" paragraph sx={{ fontSize: '0.9rem' }}>
                {quickViewProduct.description}
              </Typography>
            )}

            <Box sx={{ mt: 2 }}>
              {quickViewProduct.category && (
                <Chip
                  icon={<CategoryIcon sx={{ fontSize: 16 }} />}
                  label={typeof quickViewProduct.category === 'object' 
                    ? quickViewProduct.category.name 
                    : quickViewProduct.category}
                  size="small"
                  variant="outlined"
                  sx={{ mr: 1, mb: 1, fontSize: '0.75rem' }}
                />
              )}
            </Box>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2 }}>
            <Button 
              size="small" 
              onClick={() => setQuickViewProduct(null)}
            >
              Close
            </Button>
            {onEdit && (
              <Button 
                size="small"
                variant="contained" 
                startIcon={<EditIcon sx={{ fontSize: 18 }} />}
                onClick={() => {
                  onEdit(quickViewProduct);
                  setQuickViewProduct(null);
                }}
              >
                Edit
              </Button>
            )}
          </DialogActions>
        </>
      )}
    </Dialog>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <Box textAlign="center">
          <CircularProgress size={40} />
          <Typography variant="body1" sx={{ mt: 1 }}>Loading...</Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        sx={{ mb: 2 }}
      >
        {error}
      </Alert>
    );
  }

  if (products.length === 0) {
    return (
      <Box textAlign="center" py={4}>
        <Typography variant="body1" color="textSecondary">
          No products found
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Products
        </Typography>
        <Chip 
          label={`${products.length}`} 
          size="small"
          color="primary" 
          variant="outlined"
        />
      </Box>

      <Grid container spacing={2}>
        {products.map((product) => {
          const imageUrl = getImageUrl(product.image);
          const discountPercent = getDiscountPercentage(
            parseFloat(product.price),
            parseFloat(product.wholesale_price)
          );
          const hasImage = imageUrl && !imageLoadError[product.id];
          
          return (
            <Grid item 
              xs={6} 
              sm={4} 
              md={3} 
              lg={gridSize} 
              xl={gridSize}
              key={product.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 2,
                  },
                  position: 'relative',
                  overflow: 'visible',
                }}
              >
                {/* Discount Badge */}
                {discountPercent > 0 && (
                  <Badge
                    badgeContent={`${discountPercent}%`}
                    color="error"
                    sx={{
                      position: 'absolute',
                      top: 8,
                      left: 8,
                      zIndex: 2,
                      '& .MuiBadge-badge': {
                        fontSize: '0.6rem',
                        fontWeight: 'bold',
                        padding: '2px 6px',
                        minWidth: 'auto',
                        height: '18px',
                      },
                    }}
                  />
                )}

                {/* Stock Status Badge */}
                {product.total_inventory && (
                  <Chip
                    label={product.total_inventory.total_available || 0}
                    size="small"
                    color={product.total_inventory.total_available > 0 ? 'success' : 'error'}
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      zIndex: 2,
                      fontWeight: 'bold',
                      fontSize: '0.6rem',
                      height: '18px',
                      '& .MuiChip-label': {
                        px: 1,
                      },
                    }}
                  />
                )}

                <CardActionArea
                  onClick={onSelect ? () => onSelect(product) : undefined}
                  sx={{ 
                    flexGrow: 1, 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'stretch',
                    overflow: 'hidden'
                  }}
                >
                  {/* Product Image Container - Fixed height */}
                  <Box sx={{ 
                    position: 'relative', 
                    height: 140, 
                    width: '100%',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'grey.50',
                    p: 1
                  }}>
                    {hasImage ? (
                      <CardMedia
                        component="img"
                        image={imageUrl}
                        alt={product.name}
                        sx={{
                          width: 'auto',
                          maxWidth: '100%',
                          height: 'auto',
                          maxHeight: '100%',
                          objectFit: 'contain',
                          transition: 'transform 0.3s ease',
                          '&:hover': {
                            transform: 'scale(1.05)',
                          },
                        }}
                        onError={() => handleImageError(product.id)}
                      />
                    ) : (
                      <Box
                        sx={{
                          height: '100%',
                          width: '100%',
                          backgroundColor: 'grey.50',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'grey.400',
                        }}
                      >
                        <OfferIcon sx={{ fontSize: 40 }} />
                      </Box>
                    )}

                    {/* Quick View FAB */}
                    <Fab
                      size="small"
                      color="primary"
                      sx={{
                        position: 'absolute',
                        bottom: 8,
                        right: 8,
                        zIndex: 3,
                        width: 32,
                        height: 32,
                        minHeight: 32,
                        '& .MuiSvgIcon-root': {
                          fontSize: 18,
                        },
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setQuickViewProduct(product);
                      }}
                    >
                      <ViewIcon />
                    </Fab>
                  </Box>

                  <CardContent sx={{ 
                    flexGrow: 1, 
                    p: 1.5, 
                    '&:last-child': { pb: 1.5 },
                    width: '100%',
                    boxSizing: 'border-box'
                  }}>
                    {/* Product Name */}
                    <Typography
                      variant="body2"
                      component="h3"
                      gutterBottom
                      sx={{
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        lineHeight: 1.2,
                        height: '2.4em',
                        overflow: 'hidden',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        wordBreak: 'break-word'
                      }}
                    >
                      {product.name}
                    </Typography>

                    {/* SKU */}
                    <Typography
                      variant="caption"
                      color="textSecondary"
                      gutterBottom
                      sx={{ 
                        fontSize: '0.65rem',
                        fontFamily: 'monospace',
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      #{product.sku}
                    </Typography>

                    {/* Prices */}
                    <Box sx={{ mb: 1 }}>
                      <Typography 
                        variant="body1" 
                        color="primary" 
                        fontWeight="bold" 
                        sx={{ 
                          fontSize: '0.9rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        ${parseFloat(product.price).toFixed(2)}
                      </Typography>
                      
                      {product.wholesale_price && (
                        <Typography 
                          variant="caption" 
                          color="success.main"
                          sx={{
                            display: 'block',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          Wholesale: ${parseFloat(product.wholesale_price).toFixed(2)}
                        </Typography>
                      )}

                      {product.min_wholesale_qty && product.min_wholesale_qty > 1 && (
                        <Chip
                          label={`Min ${product.min_wholesale_qty}`}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{ 
                            fontSize: '0.6rem',
                            height: '18px',
                            mt: 0.5,
                            '& .MuiChip-label': {
                              px: 1,
                            },
                          }}
                        />
                      )}
                    </Box>

                    {/* Category */}
                    {product.category && (
                      <Typography
                        variant="caption"
                        color="textSecondary"
                        sx={{
                          display: 'block',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {typeof product.category === 'object' 
                          ? product.category.name 
                          : product.category}
                      </Typography>
                    )}
                  </CardContent>
                </CardActionArea>

                {/* Action Buttons */}
                <Box sx={{ 
                  p: 1, 
                  pt: 0.5, 
                  borderTop: 1, 
                  borderColor: 'divider',
                  mt: 'auto'
                }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {onEdit && (
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            sx={{ 
                              width: 28, 
                              height: 28,
                              '& .MuiSvgIcon-root': { fontSize: 16 }
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              onEdit(product);
                            }}
                            color="primary"
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>

                    {onDelete && (
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          sx={{ 
                            width: 28, 
                            height: 28,
                            '& .MuiSvgIcon-root': { fontSize: 16 }
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            onDelete(product.id);
                          }}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </Box>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Quick View Dialog */}
      <QuickViewDialog />
    </Box>
  );
};

export default ProductList;