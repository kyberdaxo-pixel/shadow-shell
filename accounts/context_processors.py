def global_context(request):
    context = {
        'platform_name': 'ShadowShell',
        'platform_version': '1.0.0',
    }
    if request.user.is_authenticated:
        try:
            context['user_profile'] = request.user.cyber_profile
        except Exception:
            context['user_profile'] = None
    return context