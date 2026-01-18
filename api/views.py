from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Sum

from .models import Category, Transaction, BudgetGoal
from .serializers import CategorySerializer, TransactionSerializer, BudgetGoalSerializer


# =====================================================
# Category
# =====================================================

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().order_by("-created_at")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class CategoryCreateView(generics.CreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "id"


class CategoryUpdateView(generics.UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "id"


class CategoryDeleteView(generics.DestroyAPIView):
    queryset = Category.objects.all()
    permission_classes = [AllowAny]
    lookup_field = "id"


# =====================================================
# Transaction
# =====================================================

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Transaction.objects.select_related("category").all().order_by("-date", "-created_at")

        tx_type = self.request.query_params.get("type")          # income/expense
        category = self.request.query_params.get("category")     # category id
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
            qs = qs.filter(note__icontains=search) | qs.filter(category__name__icontains=search)

        return qs


class TransactionCreateView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]


class TransactionDetailView(generics.RetrieveAPIView):
    queryset = Transaction.objects.select_related("category").all()
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"


class TransactionUpdateView(generics.UpdateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"


class TransactionDeleteView(generics.DestroyAPIView):
    queryset = Transaction.objects.all()
    permission_classes = [AllowAny]
    lookup_field = "id"


class TransactionSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Transaction.objects.all()

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
            qs = qs.filter(note__icontains=search) | qs.filter(category__name__icontains=search)

        income = qs.filter(type="income").aggregate(total=Sum("amount"))["total"] or 0
        expense = qs.filter(type="expense").aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "count": qs.count()
        })


# =====================================================
# BudgetGoal (Upsert by month)
# =====================================================

class BudgetGoalListView(generics.ListAPIView):
    queryset = BudgetGoal.objects.all().order_by("-month")
    serializer_class = BudgetGoalSerializer
    permission_classes = [AllowAny]


class BudgetGoalUpsertView(APIView):
    """
    POST /goals/
    body: { "month": "2026-01-01", "target_amount": 1000, "gold_amount": 300 }
    -> month ကို day=1 အနေနဲ့ထားပြီး update_or_create လုပ်ပေးမယ်
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BudgetGoalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        month = serializer.validated_data["month"].replace(day=1)

        obj, _ = BudgetGoal.objects.update_or_create(
            month=month,
            defaults={
                "target_amount": serializer.validated_data["target_amount"],
                "gold_amount": serializer.validated_data["gold_amount"],
            }
        )

        return Response(BudgetGoalSerializer(obj).data, status=status.HTTP_201_CREATED)


class BudgetGoalDetailView(generics.RetrieveAPIView):
    queryset = BudgetGoal.objects.all()
    serializer_class = BudgetGoalSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"


class BudgetGoalDeleteView(generics.DestroyAPIView):
    queryset = BudgetGoal.objects.all()
    permission_classes = [AllowAny]
    lookup_field = "id"
