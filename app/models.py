from django.db import models
from django.db.models import UniqueConstraint,Q,CheckConstraint,Index, Func
from django.conf import settings


class OrderQuerySet(models.QuerySet):

    def unshipped(self):
        return self.filter(is_shipped=False)


class OrderManager(models.Manager):

    def create(self, *, products, **kwargs):
        order = super().create(**kwargs)
        return order


class Customer(models.Model):
    name = models.CharField(max_length=256)


class Product(models.Model):
    name = models.CharField(max_length=256)
    price = models.DecimalField(max_digits=5,decimal_places=3)


class Order(models.Model):
    customer = models.ForeignKey(Customer, models.CASCADE)
    created_at = models.DateTimeField()
    is_shipped = models.BooleanField()

    objects = OrderManager.from_queryset(OrderQuerySet)()

    class Meta:
        constraints = [
            UniqueConstraint(
                name='limit_pending_orders',
                fields=['customer', 'is_shipped'],
                condition=Q(is_shipped=False),
            ),
        ]
        indexes = [
            Index(
                name='unshipped_orders',
                fields=['is_shipped' ],
                condition=Q(is_shipped=False),
            )
        ]


class OrderLine(models.Model):
    order = models.ForeignKey(Order, models.CASCADE, related_query_name="lines", related_name="lines")
    product = models.ForeignKey(Product, models.CASCADE)
    gross_amount = models.DecimalField(max_digits=5,decimal_places=3)


class SalesTarget(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    target = models.DecimalField(max_digits=5,decimal_places=3)

    class Meta:
        unique_together = [('year', 'month'), ]
        CheckConstraint(
            check=Q(month__in=range(1, 13)),
            name='check_valid_month',
        )

class ConcatPair(Func):

    function = 'CONCAT'

    def as_mysql(self, compiler, connection, **extra_context):
        return super().as_sql(
            compiler, connection,
            function='CONCAT_WS',
            template="%(function)s('', %(expressions)s)",
            **extra_context
        )
qs.annotate(
  datetime=AsDateTime('date_field', 'time_field'),
)