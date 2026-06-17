import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone

from courses.models import Quest, QuestProgress, Course
from accounts.views import check_achievements
from .models import ExecutionLog
from .sandbox import execute_in_sandbox
from .validator import validate_quest_result

logger = logging.getLogger('terminal')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def lab_view(request, course_slug, quest_slug):
    """Interaktiv terminal laboratoriya sahifasi"""
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    quest = get_object_or_404(Quest, slug=quest_slug, course=course, is_published=True)
    profile = request.user.cyber_profile

    if course.requires_premium and not profile.is_premium_active:
        return redirect('billing:pricing')

    progress, _ = QuestProgress.objects.get_or_create(
        user=request.user, quest=quest
    )

    next_quest = Quest.objects.filter(
        course=course, order__gt=quest.order, is_published=True
    ).order_by('order').first()

    return render(request, 'terminal/lab.html', {
        'course': course,
        'quest': quest,
        'progress': progress,
        'next_quest': next_quest,
        'profile': profile,
    })


@login_required
@require_POST
@csrf_protect
def execute_code_view(request):
    """Kod bajarish API"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Noto\'g\'ri so\'rov formati.'}, status=400)

    code = data.get('code', '').strip()
    quest_id = data.get('quest_id', '')

    if not code:
        return JsonResponse({'error': 'Kod bo\'sh.'}, status=400)

    if len(code) > 10000:
        return JsonResponse({'error': 'Kod juda uzun.'}, status=400)

    quest = None
    if quest_id:
        try:
            quest = Quest.objects.get(id=quest_id)
        except Quest.DoesNotExist:
            pass

    # Kodni bajarish
    setup_script = quest.setup_script if quest else ''
    timeout = quest.time_limit if quest else 30

    result = execute_in_sandbox(code, setup_script, timeout)

    # Natijani tekshirish
    is_correct = False
    validation_result = None

    if quest and result['status'] == 'success':
        validation_result = validate_quest_result(quest, result)
        is_correct = validation_result['is_correct']

        if is_correct:
            # Progressni yangilash
            progress, _ = QuestProgress.objects.get_or_create(
                user=request.user, quest=quest
            )
            if not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = timezone.now()
                progress.save()

                # XP qo'shish
                profile = request.user.cyber_profile
                profile.add_xp(quest.xp_reward)
                profile.quests_completed += 1
                profile.correct_scripts += 1
                profile.scripts_written += 1
                profile.save()

                # Yutuqlarni tekshirish
                check_achievements(request.user)
            else:
                progress.attempts += 1
                progress.save()
        else:
            progress, _ = QuestProgress.objects.get_or_create(
                user=request.user, quest=quest
            )
            progress.attempts += 1
            progress.last_code = code[:5000]
            progress.save()

            profile = request.user.cyber_profile
            profile.scripts_written += 1
            profile.save()

    # Log saqlash
    ExecutionLog.objects.create(
        user=request.user,
        quest=quest,
        code=code[:5000],
        output=result['output'][:5000],
        error_output=result.get('error', '')[:2000],
        status=result['status'],
        execution_time=result['execution_time'],
        is_correct=is_correct,
        ip_address=get_client_ip(request),
    )

    response_data = {
        'output': result['output'],
        'error': result.get('error', ''),
        'status': result['status'],
        'execution_time': result['execution_time'],
        'is_correct': is_correct,
    }

    if validation_result:
        response_data['validation_message'] = validation_result['message']
        response_data['validation_details'] = validation_result.get('details', '')

    return JsonResponse(response_data)



@login_required
@require_POST
def verify_quest_command(request):
    quest_id = request.POST.get('quest_id')
    submitted_command = request.POST.get('command', '').strip()
    
    quest = get_object_or_404(Quest, id=quest_id)
    progress = get_object_or_404(QuestProgress, user=request.user, quest=quest)
    
    # Agar kiritilgan buyruq topshiriq triggeriga mos kelsa
    if submitted_command == quest.command_trigger and not progress.is_completed:
        progress.is_completed = True
        progress.save()
        
        # Foydalanuvchiga EXP ochkolarini qo'shish
        profile = request.user.cyber_profile
        profile.xp += quest.xp_reward
        profile.save()
        
        return JsonResponse({'status': 'success', 'message': f'🎉 To\'g\'ri! +{quest.xp_reward} EXP yutib oldingiz.'})
        
    return JsonResponse({'status': 'wrong', 'message': 'Buyruq xato yoki topshiriq sharti bajarilmadi.'})