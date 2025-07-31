from rest_framework import serializers
from apps.category.models import Category


class CategoryListSerializer(serializers.ModelSerializer):
    """Serializer for Category list view"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'created_at', 'products_count']
    
    def get_products_count(self, obj):
        """Get products count for category"""
        return obj.products.count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Serializer for Category detail view"""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at', 'products_count']
    
    def get_products_count(self, obj):
        """Get products count for category"""
        return obj.products.count()


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating categories (Admin only)"""
    
    class Meta:
        model = Category
        fields = ['name']
        extra_kwargs = {
            'name': {'help_text': 'Toifa nomi'},
        }
    
    def validate_name(self, value):
        """Validate category name"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Toifa nomi kamida 2 ta belgidan iborat bo'lishi kerak.")
        
        # Check for uniqueness (excluding current instance if updating)
        queryset = Category.objects.filter(name__iexact=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Bu nomda toifa allaqachon mavjud.")
        
        return value.strip().title()


class CategoryStatsSerializer(serializers.ModelSerializer):
    """Serializer for category statistics (Admin only)"""
    products_count = serializers.SerializerMethodField()
    total_products_value = serializers.SerializerMethodField()
    average_product_price = serializers.SerializerMethodField()
    most_expensive_product = serializers.SerializerMethodField()
    cheapest_product = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'products_count', 'total_products_value',
            'average_product_price', 'most_expensive_product', 'cheapest_product'
        ]
    
    def get_products_count(self, obj):
        """Get total products count"""
        return obj.products.count()
    
    def get_total_products_value(self, obj):
        """Get total value of all products in category"""
        products = obj.products.all()
        total = sum(product.final_price for product in products)
        return total
    
    def get_average_product_price(self, obj):
        """Get average product price in category"""
        products = obj.products.all()
        if not products:
            return 0
        
        total = sum(product.final_price for product in products)
        return total / len(products)
    
    def get_most_expensive_product(self, obj):
        """Get most expensive product in category"""
        product = obj.products.order_by('-price').first()
        if product:
            return {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'final_price': product.final_price
            }
        return None
    
    def get_cheapest_product(self, obj):
        """Get cheapest product in category"""
        product = obj.products.order_by('price').first()
        if product:
            return {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'final_price': product.final_price
            }
        return None


# Backward compatibility
class CategorySerializer(CategoryListSerializer):
    """Original CategorySerializer for backward compatibility"""
    pass
