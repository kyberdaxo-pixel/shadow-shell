import json
import logging
import uuid
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from .models import Plan, Payment

logger = logging.getLogger('billing')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def pricing_view(request):
    plans = Plan.objects.filter(is_active=True).order_by('order')
    profile = request.user.cyber_profile

    return render(request, 'billing/pricing.html', {
        'plans': plans,
        'profile': profile,
        'stripe_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
def checkout_view(request, plan_slug):
    plan = get_object_or_404(Plan, slug=plan_slug, is_active=True)
    profile = request.user.cyber_profile

    if profile.is_premium_active:
        messages.info(request, '✅ Siz allaqachon Premium obunachisiz!')
        return redirect('accounts:dashboard')

    return render(request, 'billing/checkout.html', {
        'plan': plan,
        'profile': profile,
        'stripe_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
@require_POST
@csrf_protect
def process_sandbox_payment(request):
    """Sandbox (test) to'lov"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Noto\'g\'ri format.'}, status=400)

    plan_id = data.get('plan_id')
    card_number = data.get('card_number', '')

    if not plan_id:
        return JsonResponse({'error': 'Reja tanlanmagan.'}, status=400)

    try:
        plan = Plan.objects.get(id=plan_id, is_active=True)
    except Plan.DoesNotExist:
        return JsonResponse({'error': 'Reja topilmadi.'}, status=404)

    # Sandbox test kartalarni tekshirish
    test_cards = [
        '4242424242424242',
        '4000056655665556',
        '5555555555554444',
        '8600000000000000',
        '9860000000000000',
    ]

    card_clean = card_number.replace(' ', '').replace('-', '')

    if card_clean not in test_cards:
        return JsonResponse({
            'error': 'Test karta raqami noto\'g\'ri. 4242 4242 4242 4242 ishlating.',
        }, status=400)

    # To'lovni saqlash
    payment = Payment.objects.create(
        user=request.user,
        plan=plan,
        amount=plan.price_usd,
        currency='USD',
        provider='sandbox',
        provider_payment_id=f'sandbox_{uuid.uuid4().hex[:16]}',
        status='completed',
        ip_address=get_client_ip(request),
        metadata={
            'card_last4': card_clean[-4:],
            'sandbox_mode': True,
        },
    )

    # Premium statusni yangilash
    profile = request.user.cyber_profile
    profile.is_premium = True
    profile.premium_until = timezone.now() + timedelta(days=plan.duration_days)
    profile.save()

    logger.info(f'Sandbox payment completed: {request.user.username} - Plan: {plan.name}')

    return JsonResponse({
        'success': True,
        'message': f'✅ To\'lov muvaffaqiyatli! {plan.name} rejasi aktivlashtirildi.',
        'redirect': '/billing/success/',
    })


@login_required
@require_POST
@csrf_protect
def create_stripe_session(request):
    """Stripe Checkout sessiya yaratish"""
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        data = json.loads(request.body)
        plan_id = data.get('plan_id')

        plan = Plan.objects.get(id=plan_id, is_active=True)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'ShadowShell {plan.name}',
                        'description': plan.description,
                    },
                    'unit_amount': int(plan.price_usd * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/billing/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/billing/pricing/'),
            client_reference_id=str(request.user.id),
            metadata={
                'plan_id': str(plan.id),
                'user_id': str(request.user.id),
            },
        )

        Payment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price_usd,
            currency='USD',
            provider='stripe',
            provider_payment_id=checkout_session.id,
            status='pending',
            ip_address=get_client_ip(request),
        )

        return JsonResponse({'checkout_url': checkout_session.url})

    except Exception as e:
        logger.error(f'Stripe session error: {e}')
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def payment_success_view(request):
    profile = request.user.cyber_profile
    recent_payment = Payment.objects.filter(
        user=request.user, status='completed'
    ).order_by('-created_at').first()

    return render(request, 'billing/success.html', {
        'profile': profile,
        'payment': recent_payment,
    })