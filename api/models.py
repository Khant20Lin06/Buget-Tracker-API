from django.db import models
from django.conf import settings
import uuid

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="categories",db_index=True,null=True,blank=True)
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=80, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user})"

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="transactions",db_index=True,null=True,blank=True)
    TX_CHOICES = [("income", "Income"), ("expense", "Expense")]

    type = models.CharField(max_length=10, choices=TX_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f" {self.type}Transaction {self.category} for {self.amount}"

class BudgetGoal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="goals",db_index=True,null=True,blank=True)
    month = models.DateField() 
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    gold_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.month} target={self.target_amount} gold={self.gold_amount}"
