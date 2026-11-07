import unittest

try:
    from . import support  # noqa: F401
except ImportError:
    import support  # noqa: F401

import main


ROTAS_ESPERADAS = {
    '/': {'GET'},
    '/acordes': {'GET'},
    '/generos': {'GET'},
    '/musica/<m_id>/': {'GET'},
    '/musicas': {'GET'},
    '/search': {'GET'},
    '/sequencias': {'GET', 'POST'},
    '/sequencias/<int:sequencia_id>': {'GET'},
    '/similares': {'GET'},
    '/static/<path:filename>': {'GET'},
}

VERBOS_NO_PATH = (
    '/cadastra',
    '/lista',
    '/remove',
    '/deleta',
    '/exclui',
    '/atualiza',
    '/edita',
)


class InventarioDeRotasTest(unittest.TestCase):

    def regras_relevantes(self):
        for regra in main.app.url_map.iter_rules():
            if regra.rule == '/<path:path>':
                continue
            metodos = set(regra.methods) - {'HEAD', 'OPTIONS'}
            yield regra, metodos

    def test_sem_verbos_no_path(self):
        for regra, _ in self.regras_relevantes():
            for verbo in VERBOS_NO_PATH:
                with self.subTest(rota=regra.rule):
                    self.assertNotIn(verbo, regra.rule)

    def test_sem_metodos_de_mutacao_inesperados(self):
        for regra, metodos in self.regras_relevantes():
            with self.subTest(rota=regra.rule):
                self.assertFalse(metodos & {'DELETE', 'PUT', 'PATCH'})
                self.assertTrue(metodos <= {'GET', 'POST'})

    def test_somente_rotas_e_metodos_esperados(self):
        rotas = {}
        for regra, metodos in self.regras_relevantes():
            rotas.setdefault(regra.rule, set()).update(metodos)
        self.assertEqual(rotas, ROTAS_ESPERADAS)

    def test_post_somente_no_catalogo(self):
        for regra, metodos in self.regras_relevantes():
            if 'POST' in metodos:
                with self.subTest(rota=regra.rule):
                    self.assertEqual(regra.rule, '/sequencias')


if __name__ == '__main__':
    unittest.main()
