import bleach
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CyberProfile


class ShadowRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'email@example.com',
            'autocomplete': 'email',
        })
    )
    username = forms.CharField(
        min_length=3,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'shadow_hacker',
            'autocomplete': 'username',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••••',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••••',
            'autocomplete': 'new-password',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        username = bleach.clean(username, tags=[], strip=True)
        if not username.replace('_', '').replace('-', '').isalnum():
            raise ValidationError('Username faqat harflar, raqamlar, _ va - dan iborat bo\'lishi kerak.')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Bu username allaqachon mavjud.')
        return username.lower()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email = bleach.clean(email, tags=[], strip=True)
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Bu email allaqachon ro\'yxatdan o\'tgan.')
        return email.lower()


class ShadowLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username yoki Email',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': '••••••••••',
            'autocomplete': 'current-password',
        })
    )


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CyberProfile
        fields = ['bio', 'github_url', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'maxlength': 500,
                'placeholder': 'Kiber bio yozing...',
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://github.com/username',
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/png,image/jpeg,image/webp',
            }),
        }

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '')
        return bleach.clean(bio, tags=[], strip=True)

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 2 * 1024 * 1024:
                raise ValidationError('Avatar hajmi 2MB dan kichik bo\'lishi kerak.')
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if avatar.content_type not in allowed_types:
                raise ValidationError('Faqat JPEG, PNG yoki WebP formatlar qabul qilinadi.')
        return avatar