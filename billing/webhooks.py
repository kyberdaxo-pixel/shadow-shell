import json
import logging
from datetime import timedelta

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Payment

logger = logging.getLogger('billing')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Stripe webhook handler"""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error('Stripe webhook: Invalid payload')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error('Stripe webhook: Invalid signature')
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_stripe_payment_success(session)

    return HttpResponse(status=200)


def handle_stripe_payment_success(session):
    """Stripe to'lov muvaffaqiyatini qayta ishlash"""
    try:
        payment = Payment.objects.get(provider_payment_id=session['id'])
        payment.status = 'completed'
        payment.save()

        user = payment.user
        profile = user.cyber_profile
        if payment.plan:
            profile.is_premium = True
            profile.premium_until = timezone.now() + timedelta(days=payment.plan.duration_days)
            profile.save()

        logger.info(f'Stripe payment completed for user: {user.username}')

    except Payment.DoesNotExist:
        logger.error(f'Payment not found for session: {session["id"]}')
    except Exception as e:
        logger.error(f'Stripe webhook error: {e}')


@csrf_exempt
@require_POST
def payme_webhook(request):
    """Payme webhook handler (sandbox)"""
    try:
        data = json.loads(request.body)
        method = data.get('method')

        if method == 'CheckPerformTransaction':
            return JsonResponse({
                'result': {'allow': True}
            })
        elif method == 'CreateTransaction':
            return JsonResponse({
                'result': {
                    'create_time': int(timezone.now().timestamp() * 1000),
                    'transaction': data.get('params', {}).get('id', ''),
                    'state': 1,
                }
            })
        elif method == 'PerformTransaction':
            account = data.get('params', {}).get('account', {})
            user_id = account.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    profile = user.cyber_profile
                    profile.is_premium = True
                    profile.premium_until = timezone.now() + timedelta(days=30)
                    profile.save()
                except User.DoesNotExist:
                    pass

            return JsonResponse({
                'result': {
                    'perform_time': int(timezone.now().timestamp() * 1000),
                    'transaction': data.get('params', {}).get('id', ''),
                    'state': 2,
                }
            })

        return JsonResponse({'error': {'code': -32601, 'message': 'Method not found'}})

    except Exception as e:
        logger.error(f'Payme webhook error: {e}')
        return JsonResponse({'error': {'code': -31001, 'message': str(e)}})


@csrf_exempt
@require_POST
def click_webhook(request):
    """Click webhook handler (sandbox)"""
    try:
        action = request.POST.get('action')
        user_id = request.POST.get('merchant_trans_id')

        if action == '0':  # Prepare
            return JsonResponse({
                'click_trans_id': request.POST.get('click_trans_id'),
                'merchant_trans_id': user_id,
                'merchant_prepare_id': user_id,
                'error': 0,
                'error_note': 'Success',
            })

        elif action == '1':  # Complete
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    profile = user.cyber_profile
                    profile.is_premium = True
                    profile.premium_until = timezone.now() + timedelta(days=30)
                    profile.save()
                except User.DoesNotExist:
                    pass

            return JsonResponse({
                'click_trans_id': request.POST.get('click_trans_id'),
                'merchant_trans_id': user_id,
                'error': 0,
                'error_note': 'Success',
            })

        return JsonResponse({'error': -1, 'error_note': 'Unknown action'})

    except Exception as e:
        logger.error(f'Click webhook error: {e}')
        return JsonResponse({'error': -1, 'error_note': str(e)})