from rest_framework import generics
from apps.users.models import User, VerificationCode
from apps.users.serializers import (
    RegisterSerializer,
    CustomUserSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from django.core.mail import send_mail
from django.conf import settings
import random


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Parolni o'zgartirish",
        operation_description="""Foydalanuvchi eski parolini va yangi parolini yuboradi.
Agar eski parol to'g'ri bo'lsa, yangi parol o'rnatiladi.""",
        request_body=PasswordChangeSerializer,
        responses={200: "Parol muvaffaqiyatli o‘zgartirildi", 400: "Noto‘g‘ri so‘rov"},
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Parol muvaffaqiyatli o‘zgartirildi"}, status=status.HTTP_200_OK
        )


# Parol tiklash so'rovi
class PasswordResetRequestView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Parolni tiklashni so'rash",
        operation_description="""
Foydalanuvchi email manzilini yuboradi.
Tizim ushbu emailga tasdiqlash kodini yuboradi.
Keyingi bosqichda ushbu kod orqali yangi parol o'rnatish mumkin bo'ladi.
""",
        request_body=PasswordResetRequestSerializer,
        responses={200: "Kod yuborildi", 400: "Email noto‘g‘ri yoki mavjud emas"},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.get(email=email)

        # Tasdiqlash kodi yaratish va saqlash
        code = str(random.randint(100000, 999999))
        VerificationCode.objects.update_or_create(email=email, defaults={"code": code})

        # Email yuborish
        send_mail(
            subject="Parolni tiklash tasdiqlash kodi",
            message=f"Sizning parolni tiklash tasdiqlash kodingiz: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response(
            {"message": "Tasdiqlash kodi yuborildi"}, status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Parolni yangilash",
        operation_description="""
Foydalanuvchi tasdiqlash kodi (`code`) yordamida yangi parolni o‘rnatadi.

Agar yuborilgan ma’lumotlar to‘g‘ri bo‘lsa, foydalanuvchining paroli yangilanadi.
""",
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: "Parol muvaffaqiyatli yangilandi",
            400: "Kod yoki token noto‘g‘ri",
        },
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        # Tasdiqlash kodini tekshirish
        try:
            verification = VerificationCode.objects.get(email=email, code=code)
        except VerificationCode.DoesNotExist:
            return Response(
                {"error": "Noto‘g‘ri tasdiqlash kodi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        # Tasdiqlash kodini o‘chirish
        verification.delete()

        return Response(
            {"message": "Parol muvaffaqiyatli yangilandi"}, status=status.HTTP_200_OK
        )
