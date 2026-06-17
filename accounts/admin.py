from django.contrib import admin
from .models import CyberProfile, Achievement, UserAchievement, LoginLog


import openpyxl
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from django.contrib.auth.models import User
from .models import CyberProfile, Achievement, UserAchievement, LoginLog

# Excel faylni yuklash uchun forma
class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(label="Excel (.xlsx) faylini tanlang")

@admin.register(CyberProfile)
class CyberProfileAdmin(admin.ModelAdmin):
    # Faqat bazangda aniq bor bo'lgan fieldlarni qoldiramiz
    list_display = ('user', 'level', 'xp')  
    list_filter = ('level',)  # streak olib tashlandi (vergul oxirida turishi shart!)
    search_fields = ('user__username', 'user__email')
    ordering = ('-xp',)
    
    # Qolgan actions va excel import kodlari o'zgarishsiz qoladi...
    # ⚡ ADMIN ACTIONS: Tanlangan xakerlarga srazu Level-Up berish
    actions = ['give_level_up', 'reset_stats']

    @admin.action(description="🚀 Tanlangan xakerlarni 1 daraja yuqorilatish (Level Up)")
    def give_level_up(self, request, queryset):
        for profile in queryset:
            profile.level += 1
            profile.save()
        self.message_user(request, f"{queryset.count()} ta xaker darajasi oshirildi!", messages.SUCCESS)

    @admin.action(description="⚠️ Tanlangan xakerlar statlarini nollash")
    def reset_stats(self, request, queryset):
        queryset.update(xp=0, level=1, streak=1, accuracy=0)
        self.message_user(request, "Tanlangan xakerlar ko'rsatkichlari boshlang'ich holatga qaytarildi.", messages.WARNING)

    # 📈 EXCEL IMPORT TIZIMI
    change_list_template = "admin/accounts_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/', self.admin_site.admin_view(self.import_excel), name='import-excel'),
        ]
        return custom_urls + urls

    def import_excel(self, request):
        if request.method == "POST":
            form = ExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES["excel_file"]
                try:
                    wb = openpyxl.load_workbook(excel_file)
                    worksheet = wb.active
                    
                    created_count = 0
                    # Excel qatorlarini o'qish (1-qator sarlavha deb hisoblanadi: username, email, password, level, xp)
                    for row in worksheet.iter_rows(min_row=2, values_only=True):
                        if not row[0]:  # Username bo'sh bo'lsa o'tkazib yuborish
                            continue
                        username, email, password, level, xp = row[0], row[1], row[2], row[3], row[4]
                        
                        # User yaratish yoki tekshirish
                        user, created = User.objects.get_or_create(username=username, email=email)
                        if created:
                            user.set_password(str(password))
                            user.save()
                        
                        # Profilni yangilash yoki ochish
                        profile, _ = CyberProfile.objects.get_or_create(user=user)
                        profile.level = int(level) if level else 1
                        profile.xp = int(xp) if xp else 0
                        profile.save()
                        created_count += 1
                        
                    self.message_user(request, f"Excel'dan {created_count} ta foydalanuvchi muvaffaqiyatli import qilindi!", messages.SUCCESS)
                    return redirect("..")
                except Exception as e:
                    self.message_user(request, f"Xatolik yuz berdi: {str(e)}", messages.ERROR)
                    return redirect("..")
        
        form = ExcelImportForm()
        payload = {"form": form, "title": "Excel'dan Xakerlarni Import Qilish"}
        return render(request, "admin/excel_import.html", payload)

# Qolgan modellarni admin panelga standart ulash


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'condition_type', 'condition_value', 'xp_reward']
    list_filter = ['condition_type']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['earned_at']
    search_fields = ['user__username']


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'success', 'timestamp']
    list_filter = ['success', 'timestamp']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'success', 'timestamp']