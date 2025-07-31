from rest_framework import serializers
from django.db import transaction
from apps.product.models import ProductImage, Product
from apps.category.models import Category
from taggit.models import Tag


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model"""
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']
        read_only_fields = ['id']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product list view (read-only)"""
    images = ProductImageSerializer(many=True, read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    category = serializers.SlugRelatedField(read_only=True, slug_field='name')
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    creator_name = serializers.CharField(source='creator.email', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discount_price', 
            'category', 'category_id', 'tags', 'status', 'status_display',
            'creator', 'creator_name', 'images', 'created_at', 'updated_at'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for Product detail view (read-only)"""
    images = ProductImageSerializer(many=True, read_only=True)
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    category = serializers.SlugRelatedField(read_only=True, slug_field='name')
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    creator_name = serializers.CharField(source='creator.email', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'discount_price', 'final_price',
            'category', 'category_id', 'tags', 'status', 'status_display',
            'creator', 'creator_name', 'images', 'created_at', 'updated_at'
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products (Admin only)"""
    category_id = serializers.IntegerField(write_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
        help_text="Teglar ro'yxati (masalan: ['electronics', 'smartphone'])"
    )
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text="Yuklash uchun rasmlar ro'yxati"
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'price', 'discount_price', 'status',
            'category_id', 'tag_names', 'uploaded_images'
        ]
        extra_kwargs = {
            'name': {'help_text': 'Mahsulot nomi'},
            'description': {'help_text': 'Mahsulot tavsifi'},
            'price': {'help_text': 'Mahsulot narxi'},
            'discount_price': {'help_text': 'Chegirma narxi (ixtiyoriy)'},
            'status': {'help_text': 'Mahsulot holati'},
        }
    
    def validate_category_id(self, value):
        """Validate category exists"""
        try:
            Category.objects.get(id=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Bunday toifa mavjud emas.")
        return value
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Narx musbat son bo'lishi kerak.")
        return value
    
    def validate_discount_price(self, value):
        """Validate discount price"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Chegirma narxi musbat son bo'lishi kerak.")
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        price = attrs.get('price')
        discount_price = attrs.get('discount_price')
        
        if discount_price and price and discount_price >= price:
            raise serializers.ValidationError({
                'discount_price': 'Chegirma narxi asosiy narxdan kichik bo\'lishi kerak.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create product with tags and images"""
        category_id = validated_data.pop('category_id')
        tag_names = validated_data.pop('tag_names', [])
        uploaded_images = validated_data.pop('uploaded_images', [])
        
        with transaction.atomic():
            # Set category and creator
            validated_data['category_id'] = category_id
            validated_data['creator'] = self.context['request'].user
            
            # Create product
            product = Product.objects.create(**validated_data)
            
            # Add tags
            if tag_names:
                for tag_name in tag_names:
                    product.tags.add(tag_name)
            
            # Create images
            if uploaded_images:
                for image in uploaded_images:
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        alt_text=f"{product.name} rasm"
                    )
        
        return product
    
    def update(self, instance, validated_data):
        """Update product with tags and images"""
        category_id = validated_data.pop('category_id', None)
        tag_names = validated_data.pop('tag_names', None)
        uploaded_images = validated_data.pop('uploaded_images', [])
        
        with transaction.atomic():
            # Update category if provided
            if category_id:
                validated_data['category_id'] = category_id
            
            # Update basic fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # Update tags if provided
            if tag_names is not None:
                instance.tags.clear()
                for tag_name in tag_names:
                    instance.tags.add(tag_name)
            
            # Add new images if provided
            if uploaded_images:
                for image in uploaded_images:
                    ProductImage.objects.create(
                        product=instance,
                        image=image,
                        alt_text=f"{instance.name} rasm"
                    )
        
        return instance


class ProductImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for adding images to existing product"""
    
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']
        extra_kwargs = {
            'alt_text': {'required': False}
        }
    
    def create(self, validated_data):
        """Add image to product"""
        product_id = self.context['product_id']
        validated_data['product_id'] = product_id
        
        if not validated_data.get('alt_text'):
            product = Product.objects.get(id=product_id)
            validated_data['alt_text'] = f"{product.name} rasm"
        
        return super().create(validated_data)


# Keep the original ProductSerializer for backward compatibility
class ProductSerializer(ProductListSerializer):
    """Original ProductSerializer for backward compatibility"""
    pass