import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import matching


DATABASE_PATH_PADRAO = os.path.join('instance', 'deciframe.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS sequencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    acordes TEXT NOT NULL,
    criada_em TEXT NOT NULL,
    UNIQUE(acordes)
);

CREATE TABLE IF NOT EXISTS sequencia_matches (
    sequencia_id INTEGER NOT NULL REFERENCES sequencias(id) ON DELETE CASCADE,
    id_unico_musica TEXT NOT NULL,
    PRIMARY KEY (sequencia_id, id_unico_musica)
);

CREATE INDEX IF NOT EXISTS idx_sequencia_matches_musica
    ON sequencia_matches(id_unico_musica);

CREATE TABLE IF NOT EXISTS meta (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
"""


def caminho_banco(db_path=None):
    return db_path or os.environ.get('DATABASE_PATH') or DATABASE_PATH_PADRAO


def conectar(db_path=None):
    caminho = caminho_banco(db_path)
    diretorio = os.path.dirname(os.path.abspath(caminho))
    os.makedirs(diretorio, exist_ok=True)

    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute('PRAGMA journal_mode=WAL')
    conexao.execute('PRAGMA busy_timeout=5000')
    conexao.execute('PRAGMA foreign_keys=ON')
    return conexao


@contextmanager
def abrir(db_path=None):
    conexao = conectar(db_path)
    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()


def init_db(db_path=None):
    with abrir(db_path) as conexao:
        conexao.executescript(SCHEMA)
        conexao.execute('PRAGMA user_version=1')


def _agora():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        '+00:00', 'Z')


def _para_dict(linha):
    return {
        'id': linha['id'],
        'acordes': json.loads(linha['acordes']),
        'criada_em': linha['criada_em'],
    }


def _meta_obter(conexao, chave):
    linha = conexao.execute(
        'SELECT valor FROM meta WHERE chave = ?', (chave,)
    ).fetchone()
    return linha['valor'] if linha else None


def _meta_definir(conexao, chave, valor):
    conexao.execute(
        'INSERT OR REPLACE INTO meta (chave, valor) VALUES (?, ?)',
        (chave, valor),
    )


def _inserir_matches(conexao, sequencia_id, acordes, musicas):
    ids = matching.calcular_matches(acordes, musicas)
    conexao.executemany(
        'INSERT OR IGNORE INTO sequencia_matches '
        '(sequencia_id, id_unico_musica) VALUES (?, ?)',
        [(sequencia_id, id_musica) for id_musica in ids],
    )
    return len(ids)


def _obter_ou_criar(conexao, acordes, musicas, calcular=True):
    canonica = matching.lista_canonica(acordes)
    linha = conexao.execute(
        'SELECT id, acordes, criada_em FROM sequencias WHERE acordes = ?',
        (canonica,),
    ).fetchone()
    if linha:
        return _para_dict(linha), False

    cursor = conexao.execute(
        'INSERT INTO sequencias (acordes, criada_em) VALUES (?, ?)',
        (canonica, _agora()),
    )
    sequencia_id = cursor.lastrowid
    if calcular:
        _inserir_matches(conexao, sequencia_id, acordes, musicas)
    return {
        'id': sequencia_id,
        'acordes': acordes,
        'criada_em': conexao.execute(
            'SELECT criada_em FROM sequencias WHERE id = ?', (sequencia_id,)
        ).fetchone()['criada_em'],
    }, True


def criar_sequencia(acordes, musicas, db_path=None):
    init_db(db_path)
    with abrir(db_path) as conexao:
        return _obter_ou_criar(conexao, acordes, musicas)


def listar_sequencias(db_path=None):
    init_db(db_path)
    with abrir(db_path) as conexao:
        linhas = conexao.execute(
            'SELECT id, acordes, criada_em FROM sequencias ORDER BY id'
        ).fetchall()
    return [_para_dict(linha) for linha in linhas]


def obter_sequencia(sequencia_id, db_path=None):
    with abrir(db_path) as conexao:
        linha = conexao.execute(
            'SELECT id, acordes, criada_em FROM sequencias WHERE id = ?',
            (sequencia_id,),
        ).fetchone()
    return _para_dict(linha) if linha else None


def buscar_por_acordes(acordes, db_path=None):
    canonica = matching.lista_canonica(acordes)
    with abrir(db_path) as conexao:
        linha = conexao.execute(
            'SELECT id, acordes, criada_em FROM sequencias WHERE acordes = ?',
            (canonica,),
        ).fetchone()
    return _para_dict(linha) if linha else None


def obter_matches(sequencia_id, db_path=None):
    with abrir(db_path) as conexao:
        linhas = conexao.execute(
            'SELECT id_unico_musica FROM sequencia_matches WHERE sequencia_id = ?',
            (sequencia_id,),
        ).fetchall()
    return {linha['id_unico_musica'] for linha in linhas}


def _recalcular_todos(conexao, musicas):
    conexao.execute('DELETE FROM sequencia_matches')
    linhas = conexao.execute(
        'SELECT id, acordes FROM sequencias ORDER BY id'
    ).fetchall()
    for linha in linhas:
        _inserir_matches(
            conexao, linha['id'], json.loads(linha['acordes']), musicas
        )
    return len(linhas)


def inicializar(originais, musicas, caminho_csv=None, db_path=None):
    init_db(db_path)
    versao = matching.dataset_version(caminho_csv) if caminho_csv else None
    criadas = 0
    recalculadas = 0

    with abrir(db_path) as conexao:
        versao_anterior = _meta_obter(conexao, 'dataset_version')
        reconstruir = versao is not None and versao != versao_anterior

        for acordes in originais:
            _, criada = _obter_ou_criar(
                conexao, acordes, musicas, calcular=not reconstruir
            )
            if criada:
                criadas += 1

        if reconstruir:
            recalculadas = _recalcular_todos(conexao, musicas)
            _meta_definir(conexao, 'dataset_version', versao)

        total = conexao.execute(
            'SELECT COUNT(*) AS total FROM sequencias'
        ).fetchone()['total']

    return {
        'total': total,
        'semeadas': criadas,
        'recalculadas': recalculadas,
        'dataset_version': versao,
    }
