from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from rest_framework import status

from .filters import OrdersFilter
from .serializers import OrderSerializer

from product.models import Product
from rest_framework.pagination import PageNumberPagination

from .models import Order, OrderItem

# Create your views here.

#api to get all orders
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_orders(request):

    filterset = OrdersFilter(request.GET, queryset=Order.objects.all().order_by('id'))

    count = filterset.qs.count()

    #Pagination
    resPerPage = 1
    paginator = PageNumberPagination()
    paginator.page_size = resPerPage

    queryset = paginator.paginate_queryset(filterset.qs, request)

    serializer = OrderSerializer(queryset, many=True)

    return Response({
        "count": count,
        "resPerPage": resPerPage,
        'orders': serializer.data
        })


#api to get unique order
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order(request, pk):
    order = get_object_or_404(Order, id=pk)

    serializer = OrderSerializer(order, many=False)

    return Response({'order': serializer.data})


#api to place new order
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_order(request):

    user = request.user
    data = request.data

    order_items = data['orderItems']

    if order_items and len(order_items) == 0:
        return Response({ 'error': 'No Order Items. Please add atleast one product' }, status=status.HTTP_400_BAD_REQUEST)

    else:

        # Create order

        total_amount = sum(item['price'] * item['quantity'] for item in order_items)

        order = Order.objects.create(
            user=user,
            street=data['street'],
            city=data['city'],
            state=data['state'],
            zip_code=data['zip_code'],
            phone_no=data['phone_no'],
            country=data['country'],
            total_amount=total_amount
        )

        # Create order items and set order to order items 
        for i in order_items:
            product = Product.objects.get(id=i['product'])

            item = OrderItem.objects.create(
                product=product,
                order=order,
                name=product.name,
                quantity = i['quantity'],
                price = i['price']
            )

            # Update product stock
            product.stock -= item.quantity
            product.save()


        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)


#api to update or process order
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def process_order(request, pk):
    order = get_object_or_404(Order, id=pk)

    order.status = request.data['status']

    order.save()

    serializer = OrderSerializer(order, many=False)

    return Response({'order': serializer.data})


#api to delete a order
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_order(request, pk):
    order = get_object_or_404(Order, id=pk)

    order.delete()


    return Response({'details': 'Order is deleted.'})
