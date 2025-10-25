from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from pos_app import views

from django.conf import settings
from django.conf.urls.static import static

# Create router and register ViewSets
router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'warehouses', views.WarehouseViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'bins', views.BinViewSet)
router.register(r'customers', views.CustomerViewSet)
router.register(r'sales', views.SaleViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('pos_app.urls')),
    path('api/v1/', include(router.urls)),  # Include ViewSet URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)