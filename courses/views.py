from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from .models import Course, Quest, QuestProgress

@login_required
def course_list_view(request):
    """Barcha dynamic kurslar ro'yxati va progresslar"""
    courses = Course.objects.filter(is_published=True).order_by('order')
    profile = request.user.cyber_profile

    course_data = []
    for course in courses:
        total = course.quests.filter(is_published=True).count()
        completed = QuestProgress.objects.filter(
            user=request.user,
            quest__course=course,
            is_completed=True,
        ).count()
        percent = round((completed / total) * 100) if total > 0 else 0

        # Agar bepul bo'lmasa va user premium bo'lmasa - blocklanadi
        locked = (not course.is_free) and (not profile.is_premium_active)

        course_data.append({
            'course': course,
            'total': total,
            'completed': completed,
            'percent': percent,
            'locked': locked,
        })

    return render(request, 'courses/course_list.html', {
        'course_data': course_data,
        'profile': profile,
    })


@login_required
def course_detail_view(request, slug):
    """Kurs ichidagi darslar (topshiriqlar) ro'yxati"""
    course = get_object_or_404(Course, slug=slug, is_published=True)
    profile = request.user.cyber_profile

    if (not course.is_free) and (not profile.is_premium_active):
        messages.warning(request, '🔒 Bu kurs Premium obuna talab qiladi!')
        return redirect('billing:pricing')

    quests = course.quests.filter(is_published=True).order_by('order')

    quest_data = []
    for quest in quests:
        progress = QuestProgress.objects.filter(
            user=request.user, quest=quest
        ).first()
        quest_data.append({
            'quest': quest,
            'progress': progress,
            'is_completed': progress.is_completed if progress else False,
        })

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'quest_data': quest_data,
        'profile': profile,
    })


@login_required
def quest_detail_view(request, course_slug, quest_slug):
    """Topshiriqning batafsil sahifasi (Nazariya, Video link, maslahatlar bilan)"""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    quest = get_object_or_404(Quest, slug=quest_slug, course=course, is_published=True)
    profile = request.user.cyber_profile

    if (not course.is_free) and (not profile.is_premium_active):
        messages.warning(request, '🔒 Bu topshiriq Premium obuna talab qiladi!')
        return redirect('billing:pricing')

    progress, created = QuestProgress.objects.get_or_create(
        user=request.user, quest=quest
    )

    # Keyingi va oldingi topshiriqlar navigatori
    next_quest = Quest.objects.filter(
        course=course, order__gt=quest.order, is_published=True
    ).order_by('order').first()

    prev_quest = Quest.objects.filter(
        course=course, order__lt=quest.order, is_published=True
    ).order_by('-order').first()

    return render(request, 'courses/quest_detail.html', {
        'course': course,
        'quest': quest,
        'progress': progress,
        'next_quest': next_quest,
        'prev_quest': prev_quest,
        'profile': profile,
    })


@login_required
@require_POST
def verify_command_api(request):
    """Terminaldan kelgan buyruqni tekshirib, EXP beruvchi AJAX API"""
    quest_id = request.POST.get('quest_id')
    command = request.POST.get('command', '').strip()

    quest = get_object_or_404(Quest, id=quest_id)
    progress, created = QuestProgress.objects.get_or_create(user=request.user, quest=quest)

    # Urinishlar sonini bittaga oshiramiz
    progress.attempts += 1
    progress.save()

    if progress.is_completed:
        return JsonResponse({
            'status': 'already_done', 
            'message': 'Bu topshiriqni allaqachon bajargansiz!'
        })

    # Terminal buyrug'i modeldagi triggerga to'g'ri kelsa
    if command == quest.command_trigger:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()

        # Profilga EXP qo'shish mantiqi
        profile = request.user.cyber_profile
        profile.xp += quest.xp_reward
        profile.save()

        return JsonResponse({
            'status': 'success',
            'message': f'🎉 To\'g\'ri! Topshiriq bajarildi. +{quest.xp_reward} EXP!'
        })
    
    return JsonResponse({
        'status': 'failed',
        'message': 'Xato buyruq yoki shart to\'liq bajarilmadi. Qayta urinib ko\'ring.'
    })


from django.contrib.auth.decorators import user_passes_test
from django.utils.text import slugify
from .models import Course, Quest

@user_passes_test(lambda u: u.is_staff)
def custom_admin_dashboard(request):
    if request.method == 'POST':
        # Mana shu yerda 'form_type' ni to'g'ri qabul qilib olamiz:
        action = request.POST.get('form_type')

        # --- COURSE CRUD ---
        if action == 'create_course':
            title = request.POST.get('title')
            description = request.POST.get('description')
            tier = request.POST.get('tier', 'junior')
            icon = request.POST.get('icon', '📁')
            is_free = request.POST.get('is_free') == 'on'
            
            Course.objects.create(
                title=title,
                slug=slugify(title),
                description=description,
                tier=tier,
                icon=icon,
                is_free=is_free
            )
            messages.success(request, "🚀 Yangi kurs muvaffaqiyatli bazaga qo'shildi!")

        elif action == 'update_course':
            c_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=c_id)
            course.title = request.POST.get('title')
            course.description = request.POST.get('description')
            course.icon = request.POST.get('icon')
            # Agar sizda formaga boshqa maydonlar ham qo'shilgan bo'lsa, ularni ham yangilash mumkin
            course.save()
            messages.info(request, "✅ Kurs ma'lumotlari muvaffaqiyatli yangilandi.")

        elif action == 'delete_course':
            c_id = request.POST.get('course_id')
            get_object_or_404(Course, id=c_id).delete()
            messages.error(request, "🗑️ Kurs butunlay o'chirib tashlandi.")

        # --- QUEST CRUD ---
        elif action == 'create_quest':
            course_id = request.POST.get('course_id')
            title = request.POST.get('title')
            description = request.POST.get('description')
            command_trigger = request.POST.get('command_trigger')
            xp_reward = request.POST.get('xp_reward', 100)
            difficulty = request.POST.get('difficulty', 'easy')
            
            course = get_object_or_404(Course, id=course_id)
            Quest.objects.create(
                course=course,
                title=title,
                slug=slugify(title),
                description=description,
                command_trigger=command_trigger,
                xp_reward=xp_reward,
                difficulty=difficulty
            )
            messages.success(request, f"🎯 '{title}' topshirig'i qo'shildi!")

        elif action == 'update_quest':
            q_id = request.POST.get('quest_id')
            quest = get_object_or_404(Quest, id=q_id)
            quest.title = request.POST.get('title')
            quest.command_trigger = request.POST.get('command_trigger')
            quest.xp_reward = request.POST.get('xp_reward')
            quest.description = request.POST.get('description')
            quest.save()
            messages.info(request, "🎯 Topshiriq muvaffaqiyatli tahrirlandi.")

        elif action == 'delete_quest':
            q_id = request.POST.get('quest_id')
            get_object_or_404(Quest, id=q_id).delete()
            messages.error(request, "🗑️ Topshiriq o'chirildi.")

        return redirect('courses:custom_admin')

    courses = Course.objects.prefetch_related('quests').all()
    return render(request, 'courses/admin.html', {'courses': courses})