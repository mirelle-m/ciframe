import os
import sqlite3
import tempfile
import unittest

import sequencias_db


ORIGINAIS = [
    ['Bm', 'G', 'D', 'A'],
    ['C', 'G', 'Am', 'F'],
    ['Em', 'G'],
    ['C', 'A7', 'Dm', 'G7'],
    ['Gm', 'F'],
    ['C', 'C7', 'F', 'Fm'],
]


class MusicaFalsa:

    def __init__(self, id_unico_musica, cifra):
        self.id_unico_musica = id_unico_musica
        self.cifra = cifra


class BancoSequenciasTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, 'deciframe.db')
        self.musicas = [
            MusicaFalsa('m1', ['Bm', 'G', 'D', 'A']),
            MusicaFalsa('m2', ['C', 'G']),
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cria_esquema_na_versao_1(self):
        sequencias_db.init_db(self.db_path)
        with sqlite3.connect(self.db_path) as conexao:
            versao = conexao.execute('PRAGMA user_version').fetchone()[0]
            tabelas = {
                linha[0]
                for linha in conexao.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        self.assertEqual(versao, 1)
        self.assertTrue(
            {'sequencias', 'sequencia_matches', 'meta'} <= tabelas
        )

    def test_seed_idempotente_e_ordem_de_cadastro(self):
        primeiro = sequencias_db.inicializar(
            ORIGINAIS, self.musicas, db_path=self.db_path
        )
        segundo = sequencias_db.inicializar(
            ORIGINAIS, self.musicas, db_path=self.db_path
        )

        sequencias = sequencias_db.listar_sequencias(self.db_path)
        self.assertEqual(primeiro['semeadas'], 6)
        self.assertEqual(segundo['semeadas'], 0)
        self.assertEqual(segundo['total'], 6)
        self.assertEqual([s['id'] for s in sequencias], list(range(1, 7)))
        self.assertEqual(
            [s['acordes'] for s in sequencias],
            ORIGINAIS,
        )

    def test_seed_calcula_matches(self):
        sequencias_db.inicializar(ORIGINAIS, self.musicas, db_path=self.db_path)
        self.assertEqual(
            sequencias_db.obter_matches(1, self.db_path), {'m1'}
        )

    def test_duplicata_nao_cria_linha(self):
        sequencias_db.inicializar(ORIGINAIS, self.musicas, db_path=self.db_path)
        criada, nova = sequencias_db.criar_sequencia(
            ['Bm', 'G', 'D', 'A'], self.musicas, db_path=self.db_path
        )
        self.assertFalse(nova)
        self.assertEqual(criada['id'], 1)
        self.assertEqual(
            len(sequencias_db.listar_sequencias(self.db_path)), 6
        )

    def test_nova_sequencia_calcula_matches(self):
        sequencias_db.inicializar(ORIGINAIS, self.musicas, db_path=self.db_path)
        criada, nova = sequencias_db.criar_sequencia(
            ['C', 'G'], self.musicas, db_path=self.db_path
        )
        self.assertTrue(nova)
        self.assertEqual(
            sequencias_db.obter_matches(criada['id'], self.db_path), {'m2'}
        )

    def test_dataset_version_recalcula_matches(self):
        csv_path = os.path.join(self.temp_dir.name, 'dataset.csv')
        with open(csv_path, 'w') as arquivo:
            arquivo.write('a')

        sequencias_db.inicializar(
            ORIGINAIS,
            [MusicaFalsa('m1', ['Bm', 'G', 'D', 'A'])],
            caminho_csv=csv_path,
            db_path=self.db_path,
        )
        self.assertEqual(
            sequencias_db.obter_matches(1, self.db_path), {'m1'}
        )

        with open(csv_path, 'w') as arquivo:
            arquivo.write('conteudo maior')

        resultado = sequencias_db.inicializar(
            ORIGINAIS,
            [
                MusicaFalsa('m1', ['Bm', 'G', 'D', 'A']),
                MusicaFalsa('m3', ['Bm', 'G', 'D', 'A']),
            ],
            caminho_csv=csv_path,
            db_path=self.db_path,
        )
        self.assertEqual(resultado['recalculadas'], 6)
        self.assertEqual(
            sequencias_db.obter_matches(1, self.db_path), {'m1', 'm3'}
        )

    def test_meta_dataset_version(self):
        csv_path = os.path.join(self.temp_dir.name, 'dataset.csv')
        with open(csv_path, 'w') as arquivo:
            arquivo.write('a')

        sequencias_db.inicializar(
            ORIGINAIS, self.musicas, caminho_csv=csv_path, db_path=self.db_path
        )
        with sqlite3.connect(self.db_path) as conexao:
            valor = conexao.execute(
                "SELECT valor FROM meta WHERE chave = 'dataset_version'"
            ).fetchone()[0]
        self.assertEqual(
            valor,
            '%s:%s' % (
                os.stat(csv_path).st_size,
                os.stat(csv_path).st_mtime_ns,
            ),
        )


if __name__ == '__main__':
    unittest.main()
