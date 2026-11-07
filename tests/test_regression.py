import json
import unittest
from pathlib import Path

try:
    from . import support  # noqa: F401
except ImportError:
    import support  # noqa: F401

import main


BASELINE_DIR = Path(__file__).parent / 'baseline'
SEQUENCIAS = {
    'seq1': 'Bm,G,D,A',
    'seq2': 'C,G,Am,F',
    'seq3': 'Gm,F',
    'seq4': 'C,C7,F,Fm',
    'seq5': 'Em,G',
    'seq6': 'C,A7,Dm,G7',
}


class RegressaoSequenciasTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        main.app.config['TESTING'] = True
        cls.client = main.app.test_client()

    def buscar(self, parametros):
        musicas = set()
        pagina = 1
        while pagina <= 1000:
            query = dict(parametros)
            query['pagina'] = str(pagina)
            resposta = self.client.get('/similares', query_string=query)
            self.assertEqual(resposta.status_code, 200)
            dados = json.loads(resposta.data)
            if not dados:
                return musicas
            musicas.update(m['id_unico_musica'] for m in dados)
            pagina += 1
        self.fail('paginação não terminou para %r' % (parametros,))

    def baseline(self, nome):
        with open(BASELINE_DIR / ('%s.json' % nome)) as arquivo:
            return set(json.load(arquivo))

    def test_parametro_legado_reproduz_baseline(self):
        for nome, sequencia in SEQUENCIAS.items():
            with self.subTest(sequencia=sequencia):
                self.assertEqual(
                    self.buscar({'sequencia': sequencia}),
                    self.baseline(nome),
                )

    def test_sequencia_id_reproduz_baseline(self):
        resposta = self.client.get('/sequencias')
        self.assertEqual(resposta.status_code, 200)
        catalogo = {
            tuple(item['acordes']): item['id']
            for item in json.loads(resposta.data)
        }

        for nome, sequencia in SEQUENCIAS.items():
            with self.subTest(sequencia=sequencia):
                acordes = tuple(sequencia.split(','))
                self.assertIn(acordes, catalogo)
                self.assertEqual(
                    self.buscar({'sequencia_id': str(catalogo[acordes])}),
                    self.baseline(nome),
                )


if __name__ == '__main__':
    unittest.main()
