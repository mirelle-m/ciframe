import atexit
import os
import shutil
import tempfile

_PREFIXO = 'deciframe-tests-'
_caminho_atual = os.environ.get('DATABASE_PATH', '')

if not _caminho_atual or _PREFIXO not in _caminho_atual:
    _diretorio = tempfile.mkdtemp(prefix=_PREFIXO)
    os.environ['DATABASE_PATH'] = os.path.join(_diretorio, 'deciframe.db')
    atexit.register(shutil.rmtree, _diretorio, ignore_errors=True)
