import django_filters
from apps.product.models import Product

class ProductFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="iexact")
    tags = django_filters.CharFilter(field_name="tags__name", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = ['price_min', 'price_max', 'category', 'tags']