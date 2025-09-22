
# from orders.models import Order


# def generate_order_id():
#     import random
#     import string

#     while True:
#         # Tạo mã vé 12 chữ số ngẫu nhiên
#         char = string.ascii_uppercase + string.digits
#         order_id = ''.join([str(random.choice(char)) for _ in range(12)])
#         if not Order.objects.filter(order_id=order_id).exists():
#             return order_id
