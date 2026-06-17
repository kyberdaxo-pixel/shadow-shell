import re
from django.core.exceptions import ValidationError


class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                'Parolda kamida bitta katta harf bo\'lishi kerak.',
                code='password_no_upper',
            )

    def get_help_text(self):
        return 'Parolda kamida bitta katta harf bo\'lishi kerak.'


class SpecialCharacterValidator:
    def validate(self, password, user=None):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                'Parolda kamida bitta maxsus belgi bo\'lishi kerak (!@#$%^&* va h.k.).',
                code='password_no_special',
            )

    def get_help_text(self):
        return 'Parolda kamida bitta maxsus belgi bo\'lishi kerak.'