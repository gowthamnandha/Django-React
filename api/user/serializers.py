from __future__ import annotations

import re
from typing import Any, Dict

from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import CustomUser


PHONE_PATTERN = re.compile(r"^\+?\d{7,15}$")
VALID_GENDERS = {"male", "female", "other", "prefer_not_to_say"}


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the CustomUser model with basic validation."""

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "name",
            "email",
            "password",
            "phone",
            "gender",
            "is_active",
            "is_staff",
            "is_superuser",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value: str) -> str:
        normalized = value.lower()
        user_qs = CustomUser.objects.filter(email__iexact=normalized)
        if self.instance is not None:
            user_qs = user_qs.exclude(pk=self.instance.pk)
        if user_qs.exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return normalized

    def validate_phone(self, value: str | None) -> str | None:
        if value and not PHONE_PATTERN.match(value):
            raise serializers.ValidationError(
                "Phone number must contain 7 to 15 digits and may start with '+'."
            )
        return value

    def validate_gender(self, value: str | None) -> str | None:
        if value and value.lower() not in VALID_GENDERS:
            raise serializers.ValidationError(
                "Gender must be one of: male, female, other, prefer_not_to_say."
            )
        return value.lower() if value else value

    def create(self, validated_data: Dict[str, Any]) -> CustomUser:
        password = validated_data.pop("password", None)
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance: CustomUser, validated_data: Dict[str, Any]) -> CustomUser:
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        request = self.context.get("request")
        email = attrs.get("email", "").lower()
        password = attrs.get("password")

        user = authenticate(request=request, username=email, password=password)
        if not user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials.", code="authorization"
            )

        attrs["user"] = user
        return attrs
