import django_filters
from django.db.models import Q
from .models import Order


class OrderFilter(django_filters.FilterSet):
    """Order model uchun filter set"""
    
    # Status bo'yicha filtrlash
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=Order.OrderStatus.choices,
        help_text="Buyurtma holati bo'yicha filtrlash"
    )
    
    # Sana oralig'i bo'yicha filtrlash
    created_date_from = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__gte",
        help_text="Boshlanish sanasi (YYYY-MM-DD)"
    )
    
    created_date_to = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="date__lte",
        help_text="Tugash sanasi (YYYY-MM-DD)"
    )
    
    # Narx oralig'i bo'yicha filtrlash
    price_min = django_filters.NumberFilter(
        field_name="order_price",
        lookup_expr="gte",
        help_text="Minimal narx"
    )
    
    price_max = django_filters.NumberFilter(
        field_name="order_price",
        lookup_expr="lte",
        help_text="Maksimal narx"
    )
    
    # Order ID bo'yicha qidirish
    order_id = django_filters.CharFilter(
        field_name="order_id",
        lookup_expr="icontains",
        help_text="Order ID bo'yicha qidirish"
    )
    
    # Mahsulot nomi bo'yicha qidirish
    product_name = django_filters.CharFilter(
        method="filter_by_product_name",
        help_text="Buyurtmadagi mahsulot nomi bo'yicha qidirish"
    )
    
    def filter_by_product_name(self, queryset, name, value):
        """Buyurtmadagi mahsulotlar nomi bo'yicha filtrlash"""
        return queryset.filter(
            items__product__name__icontains=value
        ).distinct()
    
    class Meta:
        model = Order
        fields = [
            'status', 
            'created_date_from', 
            'created_date_to',
            'price_min', 
            'price_max',
            'order_id',
            'product_name'
        ]
