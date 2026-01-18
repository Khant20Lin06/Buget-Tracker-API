from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group, Permission
from .models import CustomUser

User = get_user_model()


# -------------------------
# 🟢 User Registration Serializer
# -------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    # Optional: groups and permissions
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all(),
        required=False
    )
    user_permissions = serializers.SlugRelatedField(
        many=True,
        slug_field='codename',
        queryset=Permission.objects.all(),
        required=False
    )

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'phone',
            'password',
            'confirm_password',
            'profile_image',
            'groups',
            'user_permissions',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'phone': {'required': True},
            'username': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        groups_data = validated_data.pop('groups', [])
        permissions_data = validated_data.pop('user_permissions', [])

        # ✅ Create user using username/email/phone/password
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            password=validated_data['password'],
            profile_image=validated_data.get('profile_image', None),
        )

        # Add groups and permissions
        if groups_data:
            user.groups.set(groups_data)
        if permissions_data:
            user.user_permissions.set(permissions_data)

        user.save()
        return user


# -------------------------
# 🟢 User Profile Serializer
# -------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone',
            'profile_image', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = ['username', 'email', 'last_login', 'created_at', 'updated_at']


# -------------------------
# 🟢 User List / Admin Serializer
# -------------------------
class UserListSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone',
            'is_staff', 'is_superuser', 'groups', 'permissions'
        ]

    def get_permissions(self, obj):
        perms = obj.user_permissions.all()
        for group in obj.groups.all():
            perms = perms | group.permissions.all()
        return list(perms.values_list('codename', flat=True))


# -------------------------
# 🟢 Group With Permissions Serializer
# -------------------------
class GroupWithPermissionsSerializer(serializers.ModelSerializer):
    permissions = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='codename'
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']



# -------------------------
# 🟢 User Detail (Update) Serializer
# -------------------------
class UserDetailSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Group.objects.all(),
        required=False
    )
    user_permissions = serializers.SlugRelatedField(
        many=True,
        slug_field='codename',
        queryset=Permission.objects.all(),
        required=False
    )

    # ✅ add password fields for update
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'profile_image',
            'groups', 'user_permissions',
            'password', 'confirm_password'   # ✅ add
        ]

    def validate(self, attrs):
        password = attrs.get("password")
        confirm = attrs.get("confirm_password")

        # password တင်မယ်ဆို confirm လို
        if password or confirm:
            if not password:
                raise serializers.ValidationError({"password": "This field is required."})
            if not confirm:
                raise serializers.ValidationError({"confirm_password": "This field is required."})
            if password != confirm:
                raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return attrs

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)

        if 'groups' in validated_data:
            instance.groups.set(validated_data['groups'])
        if 'user_permissions' in validated_data:
            instance.user_permissions.set(validated_data['user_permissions'])

        # ✅ set password if provided
        password = validated_data.get("password")
        if password:
            instance.set_password(password)

        instance.save()
        return instance



# -------------------------
# 🟢 Forgot Password Serializer
# -------------------------
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


# -------------------------
# 🟢 Reset Password Serializer
# -------------------------
class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, required=True, min_length=6)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs