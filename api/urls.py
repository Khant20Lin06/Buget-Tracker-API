from django.urls import path
from . import views

urlpatterns = [
    # -------------------------
    # Categories
    # -------------------------
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category-create"),
    path("categories/<uuid:id>/", views.CategoryDetailView.as_view(), name="category-detail"),
    path("categories/<uuid:id>/update/", views.CategoryUpdateView.as_view(), name="category-update"),
    path("categories/<uuid:id>/delete/", views.CategoryDeleteView.as_view(), name="category-delete"),

    # -------------------------
    # Transactions
    # -------------------------
    path("transactions/", views.TransactionListView.as_view(), name="transaction-list"),
    path("transactions/create/", views.TransactionCreateView.as_view(), name="transaction-create"),
    path("transactions/<uuid:id>/", views.TransactionDetailView.as_view(), name="transaction-detail"),
    path("transactions/<uuid:id>/update/", views.TransactionUpdateView.as_view(), name="transaction-update"),
    path("transactions/<uuid:id>/delete/", views.TransactionDeleteView.as_view(), name="transaction-delete"),
    path("transactions/summary/", views.TransactionSummaryView.as_view(), name="transaction-summary"),

    # -------------------------
    # Goals
    # -------------------------
    path("goals/", views.BudgetGoalListView.as_view(), name="goal-list"),
    path("goals/upsert/", views.BudgetGoalUpsertView.as_view(), name="goal-upsert"),
    path("goals/<uuid:id>/", views.BudgetGoalDetailView.as_view(), name="goal-detail"),
    path("goals/<uuid:id>/delete/", views.BudgetGoalDeleteView.as_view(), name="goal-delete"),
]
