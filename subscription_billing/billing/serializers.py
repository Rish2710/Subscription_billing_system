from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Plan, Subscription, Invoice
from django.utils import timezone
from datetime import timedelta

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs

class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        user = obj.get('user')
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        return None

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'description']
        read_only_fields = ['id']

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source='plan', read_only=True)
    end_date = serializers.DateField(required=False)
    
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'plan_details', 'start_date', 'end_date', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'plan_details']
    
    def create(self, validated_data):
        # Set user from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        if 'user' in validated_data and validated_data['user'].email:
            validated_data['email'] = validated_data['user'].email
        
        if 'end_date' not in validated_data:
            start_date = validated_data.get('start_date', timezone.now().date())
            validated_data['end_date'] = start_date + timedelta(days=30)
        
        if 'status' not in validated_data:
            validated_data['status'] = 'active'
        
        return super().create(validated_data)

class InvoiceSerializer(serializers.ModelSerializer):
    subscription_details = SubscriptionSerializer(source='subscription', read_only=True)
    
    class Meta:
        model = Invoice
        fields = ['uuid', 'user', 'subscription', 'subscription_details', 'amount', 'issue_date', 'due_date', 'status', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'subscription_details']

class PayInvoiceSerializer(serializers.Serializer):
    invoice_uuid = serializers.UUIDField()
    
    def validate_invoice_uuid(self, value):
        try:
            invoice = Invoice.objects.get(uuid=value)
            if invoice.status == 'paid':
                raise serializers.ValidationError("This invoice is already paid.")
            return value
        except Invoice.DoesNotExist:
            raise serializers.ValidationError("Invoice not found.") 