from django.urls import path
from . import views
from . import webhooks

app_name = 'billing'

urlpatterns = [
    path('pricing/', views.pricing_view, name='pricing'),
    path('checkout/<slug:plan_slug>/', views.checkout_view, name='checkout'),
    path('process/sandbox/', views.process_sandbox_payment, name='sandbox_payment'),
    path('process/stripe/', views.create_stripe_session, name='stripe_payment'),
    path('success/', views.payment_success_view, name='success'),

    # Webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe_webhook'),
    path('webhooks/payme/', webhooks.payme_webhook, name='payme_webhook'),
    path('webhooks/click/', webhooks.click_webhook, name='click_webhook'),
]