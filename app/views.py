from django.shortcuts import render, HttpResponse
from app.models import Order, Product, Customer, SalesTarget
from django.db import transaction
from django.db.models import F, OuterRef, Subquery, Exists, Sum, Count, Func, Window
from django.db.models.functions import ExtractMonth, ExtractDay, ExtractYear, Lag


# Create your views here.


def test_views(request):
    ################################################################
    order = Order.objects.select_related('customer').prefetch_related('lines')
    """.select_related('customer'):  single related object for each row in the database
    .prefetch_related('lines')multiple related objects for each row >> join in them in python rather than in the database"""
    ################################################################
    """Avoiding race conditions"""
    """lock th row"""
    with transaction.atomic():
        product = (
            Product.objects.select_for_update().get(id=1)
        )
        product.inventory -= 1
        product.save()

    #

    """without lock"""
    product = Product.objects.get(id=1)
    product.inventory = F('inventory') + 1
    product.save()

    #############################

    """Subqueries"""
    # 1
    customers = Customer.objects.annotate(
        latest_order_time=Subquery(
            Order.objects.filter(
                customer=OuterRef('pk'),
            ).order_by(
                '-created_at'
            ).values(
                'created_at'
            )[:1]
        )
    )

    # 2
    customers = Customer.objects.annotate(
        has_orders=Exists(
            Order.objects.filter(
                customer_id=OuterRef('pk'),
            )
        )
    ).filter(
        has_orders=True
    )
    # >>> customers.first().has_orders
    # True

    # 3
    budgets = SalesTarget.objects.annotate(
        gross_total_sales=Subquery(
            Order.objects.filter(
                created_at__year=OuterRef('year'),
                created_at__month=OuterRef('month'),
            ).values_list(
                ExtractYear('created_at'),
                ExtractMonth('created_at')
            ).annotate(
                gross_total=Sum('lines__gross_amount'),
            ).values_list(
                'gross_total',
            )
        ),
    )

    # 4 sum of weekend sale amount

    targets = SalesTarget.objects.annotate(
        weekend_revenue=Subquery(
            Order.objects.filter(
                created_at__year=OuterRef('year'),
                created_at__month=OuterRef('month'),
                created_at__week_day__in=[7, 1],
            ).values_list(
                Func(
                    'lines__gross_amount',
                    function='SUM',
                ),
            )
        ),
    )
    ############################

    orders = Order.objects.annotate(
        prev_order_id=Window(
            expression=Lag('id', 1),
            partition_by=[F('customer_id')],
            order_by=F('created_at').asc(),
        ),
    )

    return HttpResponse('ok')
