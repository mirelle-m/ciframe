import json
import unittest

try:
    from . import support  # noqa: F401
except ImportError:
    import support  # noqa: F401

import main


ORIGINAIS = [
    ['Bm', 'G', 'D', 'A'],
    ['C', 'G', 'Am', 'F'],
    ['Em', 'G'],
    ['C', 'A7', 'Dm', 'G7'],
    ['Gm', 'F'],
    ['C', 'C7', 'F', 'Fm'],
]


class ApiSequenciasTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        main.app.config['TESTING'] = True
        cls.client = main.app.test_client()

    def post(self, payload):
        return self.client.post('/sequencias', json=payload)

    def listar(self):
        resposta = self.client.get('/sequencias')
        self.assertEqual(resposta.status_code, 200)
        return json.loads(resposta.data)

    def test_lista_inicial_na_ordem_de_cadastro(self):
        sequencias = self.listar()
        self.assertGreaterEqual(len(sequencias), 6)
        self.assertEqual([s['acordes'] for s in sequencias[:6]], ORIGINAIS)
        ids = [s['id'] for s in sequencias]
        self.assertEqual(ids, sorted(ids))

    def test_cria_sequencia_com_string(self):
        resposta = self.post({'acordes': 'Dm, G, C'})
        self.assertEqual(resposta.status_code, 201)
        corpo = json.loads(resposta.data)
        self.assertEqual(corpo['acordes'], ['Dm', 'G', 'C'])
        self.assertEqual(
            resposta.headers['Location'], '/sequencias/%s' % corpo['id']
        )

        detalhe = self.client.get(resposta.headers['Location'])
        self.assertEqual(detalhe.status_code, 200)
        self.assertEqual(json.loads(detalhe.data), corpo)

    def test_cria_sequencia_com_lista(self):
        resposta = self.post({'acordes': ['A', 'E', 'F#m', 'D']})
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(
            json.loads(resposta.data)['acordes'], ['A', 'E', 'F#m', 'D']
        )

    def test_duplicata_devolve_a_existente(self):
        primeira = self.post({'acordes': 'E7, A7, D7, G7'})
        self.assertEqual(primeira.status_code, 201)
        id_criado = json.loads(primeira.data)['id']
        total_antes = len(self.listar())

        segunda = self.post({'acordes': 'E7, A7, D7, G7'})
        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(json.loads(segunda.data), json.loads(primeira.data))
        self.assertEqual(json.loads(segunda.data)['id'], id_criado)
        self.assertEqual(len(self.listar()), total_antes)
        self.assertNotIn('Location', segunda.headers)

    def test_entradas_invalidas(self):
        casos = [
            {},
            {'acordes': 'Bm'},
            {'acordes': 42},
            {'acordes': 'Bm,' + ('G,' * 600)},
        ]
        for payload in casos:
            with self.subTest(payload=payload):
                resposta = self.post(payload)
                self.assertEqual(resposta.status_code, 400)
                self.assertIn('erro', json.loads(resposta.data))

    def test_sequencia_id_inexistente(self):
        resposta = self.client.get(
            '/similares', query_string={'sequencia_id': '999999'}
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertIn('erro', json.loads(resposta.data))

    def test_sequencia_id_invalido(self):
        resposta = self.client.get(
            '/similares', query_string={'sequencia_id': 'abc'}
        )
        self.assertEqual(resposta.status_code, 404)

    def test_detalhe_inexistente(self):
        resposta = self.client.get('/sequencias/999999')
        self.assertEqual(resposta.status_code, 404)

    def test_legado_inexistente_retorna_lista_vazia(self):
        resposta = self.client.get(
            '/similares', query_string={'sequencia': 'Zz,Yy'}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(json.loads(resposta.data), [])

    def test_legado_aceita_ponto_e_virgula(self):
        com_virgula = self.client.get(
            '/similares', query_string={'sequencia': 'Bm,G,D,A'}
        )
        com_ponto_e_virgula = self.client.get(
            '/similares', query_string={'sequencia': 'Bm;G;D;A'}
        )
        self.assertEqual(com_virgula.status_code, 200)
        self.assertEqual(com_ponto_e_virgula.status_code, 200)
        self.assertEqual(
            json.loads(com_virgula.data), json.loads(com_ponto_e_virgula.data)
        )

    def test_respostas_continuam_text_html(self):
        resposta = self.client.get(
            '/similares', query_string={'sequencia': 'Bm,G,D,A'}
        )
        self.assertTrue(resposta.content_type.startswith('text/html'))


if __name__ == '__main__':
    unittest.main()
