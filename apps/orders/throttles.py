from rest_framework.throttling import UserRateThrottle


class OrderCreateThrottle(UserRateThrottle):
    scope = "order_create"
