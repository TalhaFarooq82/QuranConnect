from django.urls import path
from . import views

urlpatterns = [
    path('job/<int:job_id>/release-escrow/', views.release_escrow, name='release_escrow'),
    path('stripe/checkout/', views.stripe_checkout, name='stripe_checkout'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/', views.stripe_cancel, name='stripe_cancel'),
]