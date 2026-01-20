# app/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q

from .models import Category, Transaction, BudgetGoal
from .serializers import CategorySerializer, TransactionSerializer, BudgetGoalSerializer


# =========================
# Category
# =========================
class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by("-created_at")


class CategoryCreateView(generics.CreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class CategoryDetailView(generics.RetrieveAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class CategoryUpdateView(generics.UpdateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class CategoryDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


# =========================
# Transaction
# =========================
class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.select_related("category").filter(user=self.request.user).order_by("-date", "-created_at")

        tx_type = self.request.query_params.get("type")
        category = self.request.query_params.get("category")
        min_amount = self.request.query_params.get("min")
        max_amount = self.request.query_params.get("max")
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")
        search = (self.request.query_params.get("search") or "").strip()

        if tx_type and tx_type != "all":
            qs = qs.filter(type=tx_type)

        if category:
            qs = qs.filter(category_id=category)

        if min_amount not in [None, ""]:
            qs = qs.filter(amount__gte=min_amount)

        if max_amount not in [None, ""]:
            qs = qs.filter(amount__lte=max_amount)

        if date_from:
            qs = qs.filter(date__gte=date_from)

        if date_to:
            qs = qs.filter(date__lte=date_to)

        if search:
            qs = qs.filter(Q(note__icontains=search) | Q(category__name__icontains=search))

        return qs


class TransactionCreateView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Transaction.objects.select_related("category").filter(user=self.request.user)


class TransactionUpdateView(generics.UpdateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class TransactionDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class TransactionSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user)

        tx_type = request.query_params.get("type")
        category = request.query_params.get("category")
        min_amount = request.query_params.get("min")
        max_amount = request.query_params.get("max")
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        search = (request.query_params.get("search") or "").strip()

        if tx_type and tx_type != "all":
            qs = qs.filter(type=tx_type)

        if category:
            qs = qs.filter(category_id=category)

        if min_amount not in [None, ""]:
            qs = qs.filter(amount__gte=min_amount)

        if max_amount not in [None, ""]:
            qs = qs.filter(amount__lte=max_amount)

        if date_from:
            qs = qs.filter(date__gte=date_from)

        if date_to:
            qs = qs.filter(date__lte=date_to)

        if search:
            qs = qs.filter(Q(note__icontains=search) | Q(category__name__icontains=search))

        income = qs.filter(type="income").aggregate(total=Sum("amount"))["total"] or 0
        expense = qs.filter(type="expense").aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "count": qs.count()
        })


# =========================
# Goals
# =========================
class BudgetGoalListView(generics.ListAPIView):
    serializer_class = BudgetGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BudgetGoal.objects.filter(user=self.request.user).order_by("-month")


class BudgetGoalUpsertView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BudgetGoalSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        month = serializer.validated_data["month"].replace(day=1)

        obj, _ = BudgetGoal.objects.update_or_create(
            user=request.user,   # ✅ IMPORTANT
            month=month,
            defaults={
                "target_amount": serializer.validated_data["target_amount"],
                "gold_amount": serializer.validated_data["gold_amount"],
            }
        )

        return Response(BudgetGoalSerializer(obj).data, status=status.HTTP_201_CREATED)


class BudgetGoalDetailView(generics.RetrieveAPIView):
    serializer_class = BudgetGoalSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return BudgetGoal.objects.filter(user=self.request.user)


class BudgetGoalDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return BudgetGoal.objects.filter(user=self.request.user)
