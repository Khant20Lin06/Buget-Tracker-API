from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import PasswordResetToken
from .serializers import (
    RegisterSerializer, UserProfileSerializer, UserDetailSerializer,
    ResetPasswordSerializer, ForgotPasswordSerializer,GroupWithPermissionsSerializer
)
from .helpers import mmt
from rest_framework.pagination import PageNumberPagination
from django.db import transaction

from datetime import datetime, time
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware, is_naive
from django.http import HttpResponse
import csv



User = get_user_model()


# ======================================================
# ✅ Pagination
# ======================================================
class Pagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 100000000000000000000

    def get_paginated_response(self, data):
        total_pages = self.page.paginator.num_pages
        return Response({
            'count': self.page.paginator.count,
            'total_pages': total_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


# -------------------------
# ✅ Register View (created_at only)
# -------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        return Response({
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "phone": str(user.phone),
                "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
                "created_at": mmt(user.created_at),  # ✅ Myanmar Time
                "last_login": None,                  # ✅ Don’t set until real login
                "groups": [group.name for group in user.groups.all()],
                "permissions": [perm.codename for perm in user.user_permissions.all()],
            }
        }, status=status.HTTP_201_CREATED)

    return Response({
        "success": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)



# -------------------------
# ✅ Login View (using helpers.mmt)
# -------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    from django.utils import timezone
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            "success": False,
            "message": "Username and password are required."
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)

    if user is not None:
        # Update last_login manually
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "phone": str(user.phone),
                "profile_image": request.build_absolute_uri(user.profile_image.url) if user.profile_image else None,
                "created_at": mmt(user.created_at),
                "last_login": mmt(user.last_login),
                "groups": [group.name for group in user.groups.all()],
                "permissions": [perm.codename for perm in user.user_permissions.all()],
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token)
            }
        }, status=status.HTTP_200_OK)

    return Response({
        "success": False,
        "message": "Invalid username or password."
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "message": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = RefreshToken(refresh_token)
        token.blacklist()

        response = Response(
            {"success": True, "message": "Logout successful"},
            status=status.HTTP_200_OK
        )

        # ✅ httpOnly cookie သုံးရင်
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response

    except Exception as e:
        return Response(
            {"success": False, "message": "Invalid token"},
            status=status.HTTP_400_BAD_REQUEST
        )

# ======================================================
# ✅ User Profile (Self)
# ======================================================
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Profile updated successfully.",
                "user": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ======================================================
# ✅ User List (Admin or Staff) + Sorting + Date Filter + CSV Export
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    # ---------- filters ----------
    search_query = request.query_params.get('search', '').strip()
    username_query = request.query_params.get('username', '').strip()
    email_query = request.query_params.get('email', '').strip()
    phone_query = request.query_params.get('phone', '').strip()
    group_query = request.query_params.get('group', '').strip()

    # ---------- new: date filters ----------
    start_date = request.query_params.get('start_date')  # YYYY-MM-DD
    end_date = request.query_params.get('end_date')      # YYYY-MM-DD

    # ---------- new: sorting ----------
    ordering = request.query_params.get('ordering', '').strip()  # e.g. username, -username, created_at, -created_at

    # ---------- new: export ----------
    export_format = request.query_params.get('format', '').strip().lower()  # csv

    users = User.objects.all()

    # ✅ search filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(groups__name__icontains=search_query)
        ).distinct()

    if username_query:
        users = users.filter(username__icontains=username_query)
    if email_query:
        users = users.filter(email__icontains=email_query)
    if phone_query:
        users = users.filter(phone__icontains=phone_query)
    if group_query:
        users = users.filter(groups__name__icontains=group_query).distinct()

    # ✅ date range filter (created_at)
    # NOTE: CustomUser model မှာ created_at/updated_at ရှိရပါမယ်
    if start_date:
        d = parse_date(start_date)
        if not d:
            return Response({"success": False, "message": "Invalid start_date. Use YYYY-MM-DD"}, status=400)
        dt = datetime.combine(d, time.min)
        users = users.filter(created_at__gte=make_aware(dt) if is_naive(dt) else dt)

    if end_date:
        d = parse_date(end_date)
        if not d:
            return Response({"success": False, "message": "Invalid end_date. Use YYYY-MM-DD"}, status=400)
        dt = datetime.combine(d, time.max)
        users = users.filter(created_at__lte=make_aware(dt) if is_naive(dt) else dt)

    # ✅ sorting allowlist (security)
    allowed_order_fields = {
        "username": "username",
        "email": "email",
        "phone": "phone",
        "created_at": "created_at",
        "updated_at": "updated_at",
        "last_login": "last_login",
    }

    if ordering:
        desc = ordering.startswith("-")
        key = ordering[1:] if desc else ordering
        field = allowed_order_fields.get(key)
        if not field:
            return Response(
                {"success": False, "message": f"Invalid ordering field: {key}"},
                status=400
            )
        users = users.order_by(f"-{field}" if desc else field)
    else:
        users = users.order_by("-created_at")  # default

    # ✅ CSV EXPORT (no pagination)
    if export_format == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="users.csv"'

        writer = csv.writer(response)
        writer.writerow(["id", "username", "email", "phone", "is_active", "groups", "permissions", "created_at"])

        for u in users:
            writer.writerow([
                str(u.id),
                u.username,
                u.email,
                str(u.phone),
                "true" if getattr(u, "is_active", True) else "false",
                ",".join([g.name for g in u.groups.all()]),
                ",".join(list(u.get_all_permissions())),
                str(getattr(u, "created_at", "")),
            ])

        return response

    # ✅ normal paginated response (your current style)
    paginator = Pagination()
    paginated_users = paginator.paginate_queryset(users, request)

    data = []
    for u in paginated_users:
        data.append({
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "phone": str(u.phone),
            "is_active": getattr(u, "is_active", True),
            "groups": [g.name for g in u.groups.all()],
            "permissions": list(u.get_all_permissions()),

            # optional: include dates for frontend filtering UI display
            "created_at": str(getattr(u, "created_at", "")),
            "updated_at": str(getattr(u, "updated_at", "")),
        })

    return paginator.get_paginated_response(data)



# ======================================================
# ✅ User Detail / Update / Delete
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"success": False, "message": "User not found"}, status=404)

    groups_data = []
    for group in user.groups.all():
        groups_data.append({
            "name": group.name,
            "permissions": [perm.codename for perm in group.permissions.all()]
        })

    return Response({
        "success": True,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "phone": str(user.phone),
            "profile_image": user.profile_image.url if user.profile_image else None,
            "groups": groups_data,
            "permissions": [perm.codename for perm in user.user_permissions.all()]
        }
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_update(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"success": False, "message": "User not found"}, status=404)

    serializer = UserDetailSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "success": True,
            "message": "User updated successfully",
            "user": serializer.data
        })
    return Response({"success": False, "errors": serializer.errors}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"success": False, "message": "User not found"}, status=404)

    if request.user.id == user.id:
        return Response({"success": False, "message": "You cannot delete yourself."}, status=400)

    user.delete()
    return Response({"success": True, "message": "User deleted successfully."})


# ======================================================
# ✅ Group Management (Admin)
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_list(request):
    search_query = request.query_params.get('search', '')
    groups = Group.objects.all()
    if search_query:
        groups = groups.filter(name__icontains=search_query)

    paginator = Pagination()
    paginated_groups = paginator.paginate_queryset(groups, request)

    data = []
    for g in paginated_groups:
        data.append({
            "id": g.id,
            "name": g.name,
            "permissions": [perm.codename for perm in g.permissions.all()]
        })
    return paginator.get_paginated_response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_group(request):
    name = request.data.get('name')
    permissions = request.data.get('permissions', [])

    if not name:
        return Response({"success": False, "message": "Group name is required"}, status=400)
    if Group.objects.filter(name=name).exists():
        return Response({"success": False, "message": "Group already exists"}, status=400)

    group = Group.objects.create(name=name)
    if permissions:
        existing_perms = Permission.objects.filter(codename__in=permissions)
        group.permissions.set(existing_perms)

    return Response({
        "success": True,
        "message": "Group created successfully",
        "group": {
            "id": group.id,
            "name": group.name,
            "permissions": [p.codename for p in group.permissions.all()]
        }
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_detail(request, group_id):
    try:
        group = Group.objects.prefetch_related("permissions").get(id=group_id)
    except Group.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Group not found"
            },
            status=404
        )

    serializer = GroupWithPermissionsSerializer(group)

    return Response(
        {
            "success": True,
            "group": serializer.data
        },
        status=200
    )



@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def group_update(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({"success": False, "message": "Group not found"}, status=404)

    name = request.data.get('name')
    permissions = request.data.get('permissions')

    if name:
        if Group.objects.exclude(id=group_id).filter(name=name).exists():
            return Response({"success": False, "message": "Group name already exists"}, status=400)
        group.name = name

    if permissions is not None:
        existing_perms = Permission.objects.filter(codename__in=permissions)
        group.permissions.set(existing_perms)

    group.save()
    return Response({
        "success": True,
        "message": "Group updated successfully",
        "group": {
            "id": group.id,
            "name": group.name,
            "permissions": [p.codename for p in group.permissions.all()]
        }
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def group_delete(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
    except Group.DoesNotExist:
        return Response({"success": False, "message": "Group not found"}, status=404)

    group.delete()
    return Response({"success": True, "message": f"Group '{group.name}' deleted successfully"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def group_bulk_delete(request):
    ids = request.data.get("ids", [])

    if not isinstance(ids, list) or not ids:
        return Response(
            {
                "success": False,
                "message": "ids must be a non-empty list"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # filter existing groups
    groups = Group.objects.filter(id__in=ids)

    if not groups.exists():
        return Response(
            {
                "success": False,
                "message": "No groups found to delete"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    with transaction.atomic():
        deleted_count = groups.count()
        groups.delete()

    return Response(
        {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"{deleted_count} group(s) deleted successfully"
        },
        status=status.HTTP_200_OK
    )

# ======================================================
# ✅ Permission List
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permission_list(request):
    search = request.GET.get('search', '')
    perms = Permission.objects.all()
    if search:
        perms = perms.filter(codename__icontains=search)
    perms = perms.values('codename', 'name')
    return Response({"results": list(perms)})


# ======================================================
# ✅ Forgot & Reset Password
# ======================================================
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        PasswordResetToken.objects.filter(user=user).delete()

        token_obj = PasswordResetToken.objects.create(user=user)
        reset_token = str(token_obj.token)
        reset_link = f"http://localhost:8000/reset_password/{reset_token}/"

        return Response({
            "success": True,
            "message": "Password reset token generated successfully.",
            "reset_token": reset_token,
            "reset_link": reset_link
        })
    return Response({"success": False, "errors": serializer.errors}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            token_obj = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return Response({"success": False, "message": "Invalid or expired token."}, status=400)

        if not token_obj.is_valid():
            token_obj.delete()
            return Response({"success": False, "message": "Token expired."}, status=400)

        user = token_obj.user
        user.set_password(new_password)
        user.save()
        token_obj.delete()

        return Response({"success": True, "message": "Password reset successfully."})
    return Response({"success": False, "errors": serializer.errors}, status=400)