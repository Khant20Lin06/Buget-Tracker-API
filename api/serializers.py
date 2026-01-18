# app/serializers.py
from rest_framework import serializers
from .models import Category, Transaction, BudgetGoal


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "icon", "created_at"]
        read_only_fields = ["id", "created_at"]


class TransactionSerializer(serializers.ModelSerializer):
    # read for FE
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount",
            "date",
            "category",
            "category_name",
            "category_icon",
            "note",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class BudgetGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetGoal
        fields = ["id", "month", "target_amount", "gold_amount", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_month(self, value):
        # optional: always store first day of month
        return value.replace(day=1)
