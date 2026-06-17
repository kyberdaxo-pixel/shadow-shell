import logging
import re

logger = logging.getLogger('terminal')


def validate_quest_result(quest, execution_result):
    """Topshiriq natijasini tekshirish"""

    if execution_result['status'] in ('error', 'timeout'):
        return {
            'is_correct': False,
            'message': execution_result['error'],
            'details': 'Kod bajarilishida xatolik yuz berdi.',
        }

    output = execution_result['output'].strip()
    validation_type = quest.validation_type

    if validation_type == 'output_match':
        return validate_output_match(output, quest.expected_output.strip())
    elif validation_type == 'file_exists':
        return validate_file_exists(output, quest.expected_output.strip())
    elif validation_type == 'file_content':
        return validate_file_content(output, quest.expected_output.strip())
    elif validation_type == 'custom_script':
        return validate_custom(output, quest.validation_script, quest.expected_output.strip())
    else:
        return validate_output_match(output, quest.expected_output.strip())


def validate_output_match(actual, expected):
    """Natijani taqqoslash"""
    # Bo'sh joylar va yangi qatorlarni normallashtirish
    actual_normalized = re.sub(r'\s+', ' ', actual).strip()
    expected_normalized = re.sub(r'\s+', ' ', expected).strip()

    if actual_normalized == expected_normalized:
        return {
            'is_correct': True,
            'message': '✅ ACCESS GRANTED! Natija to\'g\'ri!',
            'details': 'Sizning natijangiz kutilgan natija bilan mos keldi.',
        }

    # Qisman moslik tekshirish
    if expected_normalized in actual_normalized:
        return {
            'is_correct': True,
            'message': '✅ ACCESS GRANTED! Natija to\'g\'ri!',
            'details': 'Kutilgan natija topildi.',
        }

    return {
        'is_correct': False,
        'message': '❌ ACCESS DENIED! Natija noto\'g\'ri.',
        'details': f'Kutilgan: {expected[:200]}\nOlingan: {actual[:200]}',
    }


def validate_file_exists(output, expected_files):
    """Fayl mavjudligini tekshirish"""
    expected_list = [f.strip() for f in expected_files.split('\n') if f.strip()]

    for expected_file in expected_list:
        if expected_file not in output:
            return {
                'is_correct': False,
                'message': f'❌ Fayl topilmadi: {expected_file}',
                'details': f'Kutilgan fayl: {expected_file}',
            }

    return {
        'is_correct': True,
        'message': '✅ ACCESS GRANTED! Barcha fayllar mavjud!',
        'details': 'Barcha kerakli fayllar topildi.',
    }


def validate_file_content(output, expected_content):
    """Fayl tarkibini tekshirish"""
    expected_lines = [line.strip() for line in expected_content.split('\n') if line.strip()]

    for line in expected_lines:
        if line not in output:
            return {
                'is_correct': False,
                'message': '❌ Fayl tarkibi noto\'g\'ri.',
                'details': f'Topilmagan satr: {line[:100]}',
            }

    return {
        'is_correct': True,
        'message': '✅ ACCESS GRANTED! Fayl tarkibi to\'g\'ri!',
        'details': 'Barcha kutilgan kontentlar topildi.',
    }


def validate_custom(output, validation_script, expected):
    """Maxsus tekshirish skripti"""
    try:
        local_vars = {
            'output': output,
            'expected': expected,
            'result': False,
            'message': '',
        }
        exec(validation_script, {'__builtins__': {}}, local_vars)

        return {
            'is_correct': local_vars.get('result', False),
            'message': local_vars.get('message', ''),
            'details': '',
        }
    except Exception as e:
        logger.error(f'Custom validation error: {e}')
        return {
            'is_correct': False,
            'message': 'Tekshirish skriptida xatolik.',
            'details': str(e),
        }