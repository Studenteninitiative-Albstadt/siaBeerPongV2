from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TournamentViewSet, health_check

router = DefaultRouter(trailing_slash=False)
router.register(r'tournaments', TournamentViewSet, basename='tournament')

urlpatterns = router.urls + [
    path('health', health_check, name='health'),
]
