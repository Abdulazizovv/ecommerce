from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from apps.cart.models import Cart, CartItem
from apps.cart.serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class BaseCartView(generics.GenericAPIView):
    """Base view for cart operations with common functionality"""
    permission_classes = [IsAuthenticated]
    
    def get_cart(self):
        """Get or create cart for the current user"""
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartView(BaseCartView, generics.RetrieveAPIView):
    serializer_class = CartSerializer

    @swagger_auto_schema(
        operation_summary="Get user's cart",
        operation_description="Returns the authenticated user's cart. Creates one if it doesn't exist.",
        responses={200: CartSerializer()},
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        cart = self.get_cart()
        # Prefetch related items with products to avoid N+1 queries
        return Cart.objects.prefetch_related(
            'items__product'
        ).get(pk=cart.pk)


class AddToCartView(BaseCartView):
    serializer_class = AddToCartSerializer

    @swagger_auto_schema(
        operation_summary="Add product to cart",
        operation_description="Adds a product to the cart or updates quantity if already exists.",
        request_body=AddToCartSerializer,
        responses={
            200: openapi.Response("Success", schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "detail": openapi.Schema(type=openapi.TYPE_STRING),
                    "cart": CartSerializer()
                },
            )),
            400: "Invalid input"
        },
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                cart = self.get_cart()
                product_id = serializer.validated_data["product_id"]
                quantity = serializer.validated_data["quantity"]

                item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product_id=product_id,
                    defaults={'quantity': quantity}
                )

                if not created:
                    item.quantity += quantity
                    item.save()

                # Return full cart state
                cart_serializer = CartSerializer(cart)
                return Response({
                    "detail": "Product added to cart successfully",
                    "cart": cart_serializer.data
                })

        except Exception as e:
            raise ValidationError(str(e))


class UpdateCartItemView(BaseCartView, generics.UpdateAPIView):
    serializer_class = UpdateCartItemSerializer

    @swagger_auto_schema(
        operation_summary="Update cart item quantity",
        operation_description="Updates the quantity of a specific item in the cart.",
        request_body=UpdateCartItemSerializer,
        responses={
            200: openapi.Response("Updated successfully", CartSerializer()),
            400: "Invalid input",
            404: "Not found"
        },
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                instance.quantity = serializer.validated_data['quantity']
                instance.save()
                
                cart = self.get_cart()
                cart_serializer = CartSerializer(cart)
                return Response(cart_serializer.data)
        except Exception as e:
            raise ValidationError(str(e))

    def get_object(self):
        cart = self.get_cart()
        return get_object_or_404(
            CartItem.objects.select_related('product'),
            cart=cart,
            id=self.kwargs["pk"]
        )


class RemoveCartItemView(BaseCartView, generics.DestroyAPIView):
    @swagger_auto_schema(
        operation_summary="Remove item from cart",
        operation_description="Completely removes an item from the cart.",
        responses={
            204: "Deleted successfully",
            404: "Not found"
        },
    )
    def destroy(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                instance.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise ValidationError(str(e))

    def get_object(self):
        cart = self.get_cart()
        return get_object_or_404(
            CartItem,
            cart=cart,
            id=self.kwargs["pk"]
        )