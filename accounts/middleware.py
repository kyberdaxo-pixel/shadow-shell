import logging
import time

logger = logging.getLogger('accounts')


class SecurityHeadersMiddleware:
    """Xavfsizlik headerlari"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "frame-src https://js.stripe.com; "
        )

        return response


class RateLimitMiddleware:
    """So'rovlar cheklash"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}

    def __call__(self, request):
        ip = self.get_client_ip(request)
        current_time = time.time()

        if ip not in self.request_counts:
            self.request_counts[ip] = []

        self.request_counts[ip] = [
            t for t in self.request_counts[ip]
            if current_time - t < 60
        ]

        if len(self.request_counts[ip]) > 200:
            logger.warning(f'Rate limit exceeded for IP: {ip}')
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Too many requests. Please try again later.'},
                status=429
            )

        self.request_counts[ip].append(current_time)

        # Memory tozalash
        if len(self.request_counts) > 10000:
            cutoff = current_time - 120
            self.request_counts = {
                k: [t for t in v if t > cutoff]
                for k, v in self.request_counts.items()
                if any(t > cutoff for t in v)
            }

        response = self.get_response(request)
        return response

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')