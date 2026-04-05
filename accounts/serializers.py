from rest_framework import serializers
from .models import User, Role


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = [
            'email',
            'password',
            'role',
            'first_name',
            'last_name',
            'staff_id',
            'department',
            'student_id',
            'enrollment_year',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user     = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id',
            'email',
            'role',
            'first_name',
            'last_name',
            'staff_id',
            'department',
            'student_id',
            'enrollment_year',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
