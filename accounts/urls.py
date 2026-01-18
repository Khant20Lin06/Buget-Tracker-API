from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # 🧍‍♂️ USER AUTHENTICATION & PROFILE
    # =====================================================
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path("logout/", views.logout_user, name="logout"),
    path('profile/', views.user_profile, name='profile'),

    # =====================================================
    # 👥 USER MANAGEMENT (Admin or Staff)
    # =====================================================
    path('users/', views.user_list, name='user-list'),
    path('users/<uuid:user_id>/', views.user_detail, name='user-detail'),
    path('users/<uuid:user_id>/update/', views.user_update, name='user-update'),
    path('users/<uuid:user_id>/delete/', views.user_delete, name='user-delete'),

    # =====================================================
    # 🧩 GROUP MANAGEMENT (Admin)
    # =====================================================
    path('groups/', views.group_list, name='group-list'),
    path('groups/create/', views.create_group, name='group-create'),
    path('groups/<int:group_id>/', views.group_detail, name='group-detail'),
    path('groups/<int:group_id>/update/', views.group_update, name='group-update'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group-delete'),

    # 🔥 BULK DELETE (NEW)
    path('groups/bulk-delete/', views.group_bulk_delete, name='group-bulk-delete'),


    # =====================================================
    # 🔐 PERMISSIONS LIST
    # =====================================================
    path('permissions/', views.permission_list, name='permission-list'),

    # =====================================================
    # 🔑 PASSWORD RESET (Public)
    # =====================================================
    path('password/forgot/', views.forgot_password, name='forgot-password'),
    path('password/reset/', views.reset_password, name='reset-password'),
]