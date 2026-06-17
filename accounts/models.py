import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator


class CyberProfile(models.Model):
    """Foydalanuvchining kiber profili"""

    RANK_CHOICES = [
        ('recruit', '🔰 Recruit'),
        ('script_kiddie', '👶 Script Kiddie'),
        ('hacker', '💻 Hacker'),
        ('elite_hacker', '🔥 Elite Hacker'),
        ('cyber_ninja', '🥷 Cyber Ninja'),
        ('shadow_master', '👑 Shadow Master'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cyber_profile')

    # Kiber statistikalar
    xp = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Tajriba ochkolari')
    level = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Daraja')
    rank = models.CharField(max_length=30, choices=RANK_CHOICES, default='recruit', verbose_name='Rang')

    # Statistika
    quests_completed = models.IntegerField(default=0, verbose_name='Bajarilgan topshiriqlar')
    scripts_written = models.IntegerField(default=0, verbose_name='Yozilgan skriptlar')
    correct_scripts = models.IntegerField(default=0, verbose_name='To\'g\'ri skriptlar')
    total_time_spent = models.IntegerField(default=0, verbose_name='Sarflangan vaqt (daqiqa)')
    streak_days = models.IntegerField(default=0, verbose_name='Ketma-ket kunlar')
    last_activity = models.DateTimeField(null=True, blank=True)

    # Premium status
    is_premium = models.BooleanField(default=False, verbose_name='Premium')
    premium_until = models.DateTimeField(null=True, blank=True, verbose_name='Premium muddati')

    # Avatar va bio
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, default='', verbose_name='Bio')
    github_url = models.URLField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kiber Profil'
        verbose_name_plural = 'Kiber Profillar'
        ordering = ['-xp']

    def __str__(self):
        return f"{self.user.username} - {self.get_rank_display()} (XP: {self.xp})"

    @property
    def accuracy_rate(self):
        if self.scripts_written == 0:
            return 0
        return round((self.correct_scripts / self.scripts_written) * 100, 1)

    @property
    def is_premium_active(self):
        if not self.is_premium:
            return False
        if self.premium_until and self.premium_until < timezone.now():
            return False
        return True

    @property
    def xp_for_next_level(self):
        return self.level * 150

    @property
    def xp_progress_percent(self):
        needed = self.xp_for_next_level
        current_level_xp = (self.level - 1) * 150
        progress = self.xp - current_level_xp
        if needed == 0:
            return 100
        return min(round((progress / 150) * 100, 1), 100)

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_for_next_level:
            self.level += 1
        self.update_rank()
        self.last_activity = timezone.now()
        self.save()

    def update_rank(self):
        if self.level >= 50:
            self.rank = 'shadow_master'
        elif self.level >= 35:
            self.rank = 'cyber_ninja'
        elif self.level >= 20:
            self.rank = 'elite_hacker'
        elif self.level >= 10:
            self.rank = 'hacker'
        elif self.level >= 5:
            self.rank = 'script_kiddie'
        else:
            self.rank = 'recruit'

    def update_streak(self):
        now = timezone.now()
        if self.last_activity:
            diff = (now.date() - self.last_activity.date()).days
            if diff == 1:
                self.streak_days += 1
            elif diff > 1:
                self.streak_days = 1
        else:
            self.streak_days = 1
        self.last_activity = now
        self.save()


class Achievement(models.Model):
    """Yutuqlar tizimi"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='Nomi')
    description = models.TextField(verbose_name='Tavsif')
    icon = models.CharField(max_length=10, default='🏆')
    xp_reward = models.IntegerField(default=50)
    condition_type = models.CharField(max_length=50, choices=[
        ('quests_completed', 'Topshiriqlar soni'),
        ('xp_earned', 'XP miqdori'),
        ('streak_days', 'Ketma-ket kunlar'),
        ('scripts_written', 'Yozilgan skriptlar'),
        ('level_reached', 'Daraja'),
    ])
    condition_value = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Yutuq'
        verbose_name_plural = 'Yutuqlar'
        ordering = ['condition_value']

    def __str__(self):
        return f"{self.icon} {self.name}"


class UserAchievement(models.Model):
    """Foydalanuvchi yutuqlari"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'achievement']
        verbose_name = 'Foydalanuvchi yutuqi'
        verbose_name_plural = 'Foydalanuvchi yutuqlari'

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class LoginLog(models.Model):
    """Kirish tarixi"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Kirish tarixi'
        verbose_name_plural = 'Kirish tarixi'

    def __str__(self):
        status = '✅' if self.success else '❌'
        return f"{status} {self.user.username} - {self.ip_address} - {self.timestamp}"



from django.db import models
from django.contrib.auth.models import User

class PlatformUpdate(models.Model):
    VERSION_CHOICES = [
        ('major', 'Major Update (Yirik)'),
        ('minor', 'Minor Update (Kichik)'),
        ('patch', 'Fix / Patch (Tuzatish)'),
    ]
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    version = models.CharField(max_length=20, default="v1.0.0", verbose_name="Versiya")
    update_type = models.CharField(max_length=10, choices=VERSION_CHOICES, default='minor')
    description = models.TextField(verbose_name="Tafsilotlar")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.version} - {self.title}"

class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    update = models.ForeignKey(PlatformUpdate, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)