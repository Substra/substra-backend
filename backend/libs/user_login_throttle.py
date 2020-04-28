from rest_framework.throttling import UserRateThrottle


class UserLoginThrottle(UserRateThrottle):
    scope = 'login'
