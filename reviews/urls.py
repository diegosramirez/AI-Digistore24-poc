from django.urls import path
from . import views

urlpatterns = [
    path('', views.claim_next, name='claim_next'),
    path('review/<int:pk>/', views.review_prediction, name='review_prediction'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/predictions/', views.ingest_prediction, name='ingest_prediction'),
]
