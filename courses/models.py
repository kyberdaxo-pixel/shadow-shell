import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class Course(models.Model):
    """Kurs modeli (Dynamic & Kiber-pank)"""

    TIER_CHOICES = [
        ('junior', '🟢 Junior'),
        ('middle', '🟡 Middle'),
        ('senior', '🔴 Senior'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name='Kurs nomi')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(verbose_name='Tavsif')
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='junior')
    icon = models.CharField(max_length=50, default='🛡️')
    order = models.IntegerField(default=0)
    is_free = models.BooleanField(default=True, verbose_name='Bepul')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering = ['order']

    def __str__(self):
        return f"{self.icon} {self.title} ({self.get_tier_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def quest_count(self):
        return self.quests.count()


class Quest(models.Model):
    """Topshiriq (Dars va CTF Laboratoriya) modeli"""

    DIFFICULTY_CHOICES = [
        ('easy', '🟢 Oson'),
        ('medium', '🟡 O\'rtacha'),
        ('hard', '🔴 Qiyin'),
        ('elite', '💀 Elite'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quests')
    title = models.CharField(max_length=200, verbose_name='Topshiriq nomi')
    slug = models.SlugField(max_length=200)
    order = models.IntegerField(default=0)

    # 📖 Dars kontenti va Yangi Kiber-shartlar
    description = models.TextField(verbose_name='Topshiriq sharti')
    hint_code = models.TextField(blank=True, null=True, verbose_name='Maslahat / Misol Kodlar')
    video_url = models.URLField(blank=True, null=True, verbose_name='Video Darslik Linki')
    
    # 📟 Terminal Simulyatsiyasi uchun kalit buyruq
    command_trigger = models.CharField(max_length=255, default='whoami', verbose_name='Kutilayotgan terminal buyrug\'i')

    # 🔬 Tekshirish va xavfsizlik skriptlari
    expected_output = models.TextField(blank=True, verbose_name='Kutilgan natija')
    validation_script = models.TextField(blank=True, verbose_name='Tekshirish skripti (Python)')
    validation_type = models.CharField(max_length=30, choices=[
        ('command_match', 'Terminal buyrug\'i mosligi'),
        ('output_match', 'Natija mos kelishi'),
        ('file_exists', 'Fayl mavjudligi'),
        ('file_content', 'Fayl tarkibi'),
        ('custom_script', 'Maxsus skript'),
    ], default='command_match')

    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='easy')
    xp_reward = models.IntegerField(default=100, verbose_name='Beriladigan EXP ochkosi')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Topshiriq'
        verbose_name_plural = 'Topshiriqlar'
        ordering = ['course', 'order']
        unique_together = ['course', 'slug']

    def __str__(self):
        return f"{self.course.icon} {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class QuestProgress(models.Model):
    """Foydalanuvchining topshiriqlar bo'yicha real progressi"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quest_progress')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'quest']
        verbose_name = 'Topshiriq progressi'
        verbose_name_plural = 'Topshiriq progresslari'

    def __str__(self):
        status = '✅' if self.is_completed else '⏳'
        return f"{status} {self.user.username} - {self.quest.title}"