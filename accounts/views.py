import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db.models import F, Q
from django.utils import timezone

from .forms import ShadowRegisterForm, ShadowLoginForm, ProfileEditForm
from .models import CyberProfile, Achievement, UserAchievement, LoginLog, PlatformUpdate, UserNotification
from courses.models import Course, QuestProgress

logger = logging.getLogger('accounts')
User = get_user_model()

# --- YORDAMCHI FUNKSIYALAR ---
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def check_achievements(user):
    """Yutuqlarni tekshirish"""
    profile = user.cyber_profile
    all_achievements = Achievement.objects.all()
    earned_ids = set(
        UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
    )

    for achievement in all_achievements:
        if achievement.id in earned_ids:
            continue

        earned = False
        if achievement.condition_type == 'quests_completed':
            earned = profile.quests_completed >= achievement.condition_value
        elif achievement.condition_type == 'xp_earned':
            earned = profile.xp >= achievement.condition_value
        elif achievement.condition_type == 'streak_days':
            earned = profile.streak_days >= achievement.condition_value
        elif achievement.condition_type == 'scripts_written':
            earned = profile.scripts_written >= achievement.condition_value
        elif achievement.condition_type == 'level_reached':
            earned = profile.level >= achievement.condition_value

        if earned:
            UserAchievement.objects.create(user=user, achievement=achievement)
            profile.add_xp(achievement.xp_reward)


# --- AUTHENTICATION VIEWS ---
@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = ShadowRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f'New user registered: {user.username} from {get_client_ip(request)}')
            messages.success(request, f'🎉 Xush kelibsiz, {user.username}! ShadowShell dunyosiga kirish ochildi.')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Formada xatoliklar bor. Iltimos, tekshiring.')
    else:
        form = ShadowRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = ShadowLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            LoginLog.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                success=True,
            )

            user.cyber_profile.update_streak()
            logger.info(f'User logged in: {user.username}')
            messages.success(request, f'🔓 Kirish muvaffaqiyatli, {user.username}!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, '❌ Username/Email yoki parol noto\'g\'ri.')
    else:
        form = ShadowLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def custom_lockout_response(request, credentials, *args, **kwargs):
    messages.error(request, '🔒 Juda ko\'p muvaffaqiyatsiz urinish. 1 soatdan keyin qayta urinib ko\'ring.')
    return redirect('accounts:login')


@login_required
def logout_view(request):
    logger.info(f'User logged out: {request.user.username}')
    logout(request)
    messages.info(request, '👋 Tizimdan chiqdingiz.')
    return redirect('accounts:login')


# --- CORE PLATFORM VIEWS ---
@login_required(login_url='accounts:login')
def dashboard_view(request):
    user = request.user
    user_profile, created = CyberProfile.objects.get_or_create(user=user)
    
    if user.is_superuser:
        user_profile.level = 99
        user_profile.xp = 999999
        user_profile.streak = 365
        user_profile.accuracy = 100
        user_profile.save()

    completed_tasks_count = QuestProgress.objects.filter(user=request.user, is_completed=True).count()
    user_achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
    active_courses = Course.objects.all()

    # O'qilmagan xabarnomalar borligini tekshirish
    has_unread_notifications = request.user.notifications.filter(is_read=False).exists() if hasattr(request.user, 'notifications') else False

    context = {
        'title': 'ShadowShell Admin Dashboard',
        'user': user,
        'user_profile': user_profile,
        'user_exp': user_profile.xp,
        'completed_tasks_count': completed_tasks_count,
        'user_achievements': user_achievements,
        'active_courses': active_courses,
        'has_unread_notifications': has_unread_notifications,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    profile = request.user.cyber_profile
    achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('achievement')

    login_logs = LoginLog.objects.filter(user=request.user)[:10]

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Profil yangilandi!')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=profile)

    context = {
        'profile': profile,
        'form': form,
        'achievements': achievements,
        'login_logs': login_logs,
    }
    return render(request, 'accounts/profile.html', context)


# 🟢 YANGI REYTING TIZIMI (Barcha userlarni dynamic noldan hisoblaydi)
@login_required(login_url='accounts:login')
def leaderboard_view(request):
    # Hamma userlarni bazadan sug'urib, EXP bo'yicha kamayish tartibida saralaymiz
    all_users = User.objects.all()
    
    # Har bir userning profilini tekshirib, dynamic Level beramiz
    for user in all_users:
        profile, created = CyberProfile.objects.get_or_create(user=user)
        if profile.xp is None:
            profile.xp = 0
            profile.save()
        
        # Noldan boshlangan dynamic daraja tizimi (Har 1000 XP bitta daraja)
        user.level = (profile.xp // 1000) + 1
        user.exp = profile.xp

    context = {
        'users': sorted(all_users, key=lambda u: u.exp, reverse=True),
        'current_user': request.user
    }
    return render(request, 'accounts/leaderboard.html', context)


# --- ADMISTRATION & SECURITY SANDBOX VIEWS ---
@user_passes_test(lambda u: u.is_superuser)
def shadow_admin_dashboard(request):
    tab = request.GET.get('tab', 'users')
    search_query = request.GET.get('search', '')
    filter_level = request.GET.get('level', '')

    # --- BULK ACTIONS ---
    if request.method == "POST" and "bulk_action" in request.POST:
        action = request.POST.get("action")
        selected_ids = request.POST.getlist("selected_items")
        
        if action == "delete":
            if tab == "users":
                User.objects.filter(id__in=selected_ids).delete()
            elif tab == "courses":
                Course.objects.filter(id__in=selected_ids).delete()
            elif tab == "updates":
                PlatformUpdate.objects.filter(id__in=selected_ids).delete()
        return redirect(f'/accounts/shadow-admin/?tab={tab}')

    # --- NEW UPDATE POST ---
    if request.method == "POST" and "add_update" in request.POST:
        title = request.POST.get("title")
        version = request.POST.get("version")
        u_type = request.POST.get("update_type")
        desc = request.POST.get("description")
        
        new_update = PlatformUpdate.objects.create(
            title=title, version=version, update_type=u_type, description=desc
        )
        all_users = User.objects.all()
        notifications = [UserNotification(user=u, update=new_update) for u in all_users]
        UserNotification.objects.bulk_create(notifications)
        return redirect('/accounts/shadow-admin/?tab=updates')

    # --- DATA FETCHING ---
    users_list = CyberProfile.objects.select_related('user').all()
    if search_query:
        users_list = users_list.filter(Q(user__username__icontains=search_query) | Q(user__email__icontains=search_query))
    if filter_level:
        users_list = users_list.filter(level=filter_level)

    courses_list = Course.objects.all()
    if search_query and tab == "courses":
        courses_list = courses_list.filter(title__icontains=search_query)

    updates_list = PlatformUpdate.objects.all().order_by('-created_at')

    context = {
        'tab': tab,
        'search_query': search_query,
        'filter_level': filter_level,
        'profiles': users_list,
        'courses': courses_list,
        'updates': updates_list,
        'total_users': User.objects.count(),
        'total_courses': Course.objects.count(),
        'total_updates': PlatformUpdate.objects.count(),
    }
    return render(request, 'accounts/admin_dashboard.html', context)



@login_required
def shadow_terminal_view(request):
    quest_id = request.GET.get('quest_id')
    active_quest = None
    
    if quest_id:
        # Agar URL'da topshiriq ID bo'lsa, uni yuklaymiz
        active_quest = get_object_or_404(Quest, id=quest_id)
        # Tekshiramiz, bajarilgan bo'lsa ko'rsatmaymiz
        progress, _ = QuestProgress.objects.get_or_create(user=request.user, quest=active_quest)
        if progress.is_completed:
            active_quest = None

    return render(request, 'accounts/terminal.html', {'active_quest': active_quest})