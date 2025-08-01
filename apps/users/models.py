from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not phone:
            raise ValueError("Phone number is required")

        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone", "first_name", "last_name"]

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        indexes = [
            # Email for authentication (most common)
            models.Index(fields=['email'], name='user_email_idx'),
            
            # Phone for lookups and verification
            models.Index(fields=['phone'], name='user_phone_idx'),
            
            # Status fields for admin filtering
            models.Index(fields=['is_active'], name='user_active_idx'),
            models.Index(fields=['is_staff'], name='user_staff_idx'),
            
            # Name searches
            models.Index(fields=['first_name'], name='user_firstname_idx'),
            models.Index(fields=['last_name'], name='user_lastname_idx'),
            models.Index(fields=['first_name', 'last_name'], name='user_fullname_idx'),
            
            # Combined for admin panel
            models.Index(fields=['is_active', 'is_staff'], name='user_status_idx'),
            models.Index(fields=['email', 'is_active'], name='user_email_active_idx'),
        ]

    def __str__(self):
        return self.email
    

class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tasdiqlash kodi"
        verbose_name_plural = "Tasdiqlash kodlari"
        indexes = [
            # Email lookup for verification
            models.Index(fields=['email'], name='verification_email_idx'),
            
            # Code lookup
            models.Index(fields=['code'], name='verification_code_idx'),
            
            # Time-based for cleanup old codes
            models.Index(fields=['created_at'], name='verification_time_idx'),
            
            # Combined for verification process
            models.Index(fields=['email', 'code'], name='verification_email_code_idx'),
            models.Index(fields=['email', 'created_at'], name='verification_email_time_idx'),
        ]

    def __str__(self):
        return f"Verification code for {self.email}"