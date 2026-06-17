import logging
import time
import uuid
import subprocess
import os
import tempfile
import shlex

from django.conf import settings

logger = logging.getLogger('terminal')

DANGEROUS_PATTERNS = [
    'rm -rf /',
    'mkfs',
    ':(){ :|:& };:',
    'dd if=/dev/zero',
    'chmod -R 777 /',
    'wget http',
    'curl http',
    'nc -l',
    'python -c',
    'python3 -c',
    'perl -e',
    'ruby -e',
    '/dev/sda',
    '/dev/null',
    'shutdown',
    'reboot',
    'init 0',
    'init 6',
    'poweroff',
    'halt',
    '> /dev/sda',
    '/etc/passwd',
    '/etc/shadow',
    'sudo',
    'su -',
    'chroot',
    'mount',
    'umount',
    'insmod',
    'modprobe',
    'iptables',
    'nft ',
]

ALLOWED_COMMANDS = [
    'ls', 'cd', 'pwd', 'echo', 'cat', 'head', 'tail',
    'grep', 'awk', 'sed', 'sort', 'uniq', 'wc',
    'find', 'locate', 'which', 'whereis',
    'mkdir', 'rmdir', 'touch', 'cp', 'mv', 'rm',
    'chmod', 'chown', 'file', 'stat',
    'date', 'cal', 'whoami', 'hostname', 'uname',
    'ps', 'top', 'free', 'df', 'du',
    'ping', 'ifconfig', 'ip', 'netstat', 'ss', 'nmap',
    'tar', 'gzip', 'gunzip', 'zip', 'unzip',
    'diff', 'cmp', 'comm',
    'tree', 'less', 'more',
    'cut', 'paste', 'tr', 'tee',
    'bash', 'sh', 'test', 'expr',
    'sleep', 'true', 'false', 'seq',
    'env', 'export', 'set', 'read',
    'if', 'then', 'else', 'fi', 'for', 'do', 'done', 'while', 'case', 'esac',
]


def sanitize_code(code):
    """Xavfli kodlarni filtrlash"""
    if not code or not code.strip():
        return False, "Bo'sh kod yuborildi."

    if len(code) > 10000:
        return False, "Kod juda uzun (max 10000 belgi)."

    code_lower = code.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in code_lower:
            logger.warning(f'Dangerous pattern detected: {pattern}')
            return False, f"⛔ Xavfli buyruq aniqlandi: tizim xavfsizligi uchun blokland."

    return True, code


def execute_in_sandbox(code, setup_script='', timeout=30):
    """Kodni Docker containerda xavfsiz bajarish"""

    is_safe, result = sanitize_code(code)
    if not is_safe:
        return {
            'output': '',
            'error': result,
            'status': 'error',
            'execution_time': 0,
        }

    container_name = f'shadowshell-sandbox-{uuid.uuid4().hex[:12]}'
    start_time = time.time()

    try:
        # Docker mavjudligini tekshirish
        docker_check = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            timeout=5,
        )

        if docker_check.returncode != 0:
            # Docker mavjud emas, local subprocess bilan bajarish
            return execute_locally(code, setup_script, timeout)

        # Skript faylini yaratish
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            if setup_script:
                f.write(setup_script + '\n')
            f.write(code)
            script_path = f.name

        # Docker container bilan bajarish
        docker_cmd = [
            'docker', 'run',
            '--rm',
            '--name', container_name,
            '--network', 'none',
            '--memory', settings.SANDBOX_MEMORY_LIMIT,
            f'--cpus={settings.SANDBOX_CPU_LIMIT}',
            '--pids-limit', '50',
            '--read-only',
            '--tmpfs', '/tmp:size=10m',
            '--tmpfs', '/home/sandboxuser/workspace:size=10m',
            '--security-opt', 'no-new-privileges',
            '-v', f'{script_path}:/tmp/user_script.sh:ro',
            settings.DOCKER_SANDBOX_IMAGE,
            'bash', '/usr/local/bin/runner.sh',
        ]

        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )

        execution_time = round(time.time() - start_time, 2)

        # Temp faylni o'chirish
        os.unlink(script_path)

        if result.returncode == 124:
            return {
                'output': result.stdout,
                'error': '⏰ Vaqt limiti tugadi!',
                'status': 'timeout',
                'execution_time': execution_time,
            }

        return {
            'output': result.stdout[:5000],
            'error': result.stderr[:2000] if result.returncode != 0 else '',
            'status': 'success' if result.returncode == 0 else 'failed',
            'execution_time': execution_time,
        }

    except subprocess.TimeoutExpired:
        # Containerni o'chirish
        subprocess.run(['docker', 'kill', container_name], capture_output=True)
        subprocess.run(['docker', 'rm', '-f', container_name], capture_output=True)
        return {
            'output': '',
            'error': '⏰ Vaqt limiti tugadi!',
            'status': 'timeout',
            'execution_time': timeout,
        }
    except FileNotFoundError:
        return execute_locally(code, setup_script, timeout)
    except Exception as e:
        logger.error(f'Sandbox error: {str(e)}')
        return {
            'output': '',
            'error': f'Sandbox xatoligi: {str(e)}',
            'status': 'error',
            'execution_time': round(time.time() - start_time, 2),
        }


def execute_locally(code, setup_script='', timeout=30):
    """Docker mavjud bo'lmaganda local subprocess bilan bajarish"""
    start_time = time.time()

    try:
        full_script = ''
        if setup_script:
            full_script += setup_script + '\n'
        full_script += code

        # Xavfsizlik uchun cheklangan muhitda bajarish
        result = subprocess.run(
            ['bash', '-c', full_script],
            capture_output=True,
            text=True,
            timeout=min(timeout, 15),
            cwd='/tmp',
            env={
                'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
                'HOME': '/tmp',
                'USER': 'sandbox',
            },
        )

        execution_time = round(time.time() - start_time, 2)

        return {
            'output': result.stdout[:5000],
            'error': result.stderr[:2000] if result.returncode != 0 else '',
            'status': 'success' if result.returncode == 0 else 'failed',
            'execution_time': execution_time,
        }

    except subprocess.TimeoutExpired:
        return {
            'output': '',
            'error': '⏰ Vaqt limiti tugadi!',
            'status': 'timeout',
            'execution_time': timeout,
        }
    except Exception as e:
        return {
            'output': '',
            'error': str(e),
            'status': 'error',
            'execution_time': round(time.time() - start_time, 2),
        }