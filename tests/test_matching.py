import json
import unittest
from pathlib import Path

try:
    from . import support  # noqa: F401
except ImportError:
    import support  # noqa: F401

import main
from matching import (
    calcular_matches,
    lista_canonica,
    normalizar_acordes,
    sequencia_aparece,
)


BASELINE_DIR = Path(__file__).parent / 'baseline'
SEQUENCIAS_BASELINE = {
    'seq1': ['Bm', 'G', 'D', 'A'],
    'seq2': ['C', 'G', 'Am', 'F'],
    'seq3': ['Gm', 'F'],
    'seq4': ['C', 'C7', 'F', 'Fm'],
    'seq5': ['Em', 'G'],
    'seq6': ['C', 'A7', 'Dm', 'G7'],
}


class NormalizacaoTest(unittest.TestCase):

    def test_string_com_virgula_e_ponto_e_virgula(self):
        self.assertEqual(
            normalizar_acordes(' Bm, G ; D ,A '),
            ['Bm', 'G', 'D', 'A'],
        )

    def test_lista_com_espacos_e_vazios(self):
        self.assertEqual(
            normalizar_acordes([' Bm', 'G ', '', '  ', 'A']),
            ['Bm', 'G', 'A'],
        )

    def test_lista_tambem_aceita_separadores(self):
        self.assertEqual(
            normalizar_acordes(['Bm;G', 'D,A']),
            ['Bm', 'G', 'D', 'A'],
        )

    def test_preserva_caixa(self):
        self.assertEqual(normalizar_acordes('7M,7m'), ['7M', '7m'])

    def test_lista_canonica(self):
        self.assertEqual(lista_canonica(['Bm', 'G']), '["Bm","G"]')


class RegraDeMatchingTest(unittest.TestCase):

    def test_bloco_contiguo_e_ordenado(self):
        self.assertTrue(
            sequencia_aparece(['Bm', 'G', 'D', 'A'], ['Bm', 'G', 'D', 'A'])
        )

    def test_bloco_em_outra_posicao(self):
        self.assertTrue(
            sequencia_aparece(
                ['D', 'Bm', 'G', 'D', 'A'], ['Bm', 'G', 'D', 'A']
            )
        )

    def test_ordem_diferente_nao_casa(self):
        self.assertFalse(
            sequencia_aparece(['G', 'Bm', 'D', 'A'], ['Bm', 'G', 'D', 'A'])
        )

    def test_acorde_fora_da_sequencia_nao_casa(self):
        self.assertFalse(
            sequencia_aparece(['Bm', 'G', 'D', 'A', 'E'], ['Bm', 'G', 'D', 'A'])
        )

    def test_musica_sem_cifra_nao_casa(self):
        self.assertFalse(sequencia_aparece([], ['Bm', 'G']))

    def test_caixa_preservada(self):
        self.assertFalse(sequencia_aparece(['C7M'], ['C7m']))
        self.assertTrue(sequencia_aparece(['C7M'], ['C7M']))

    def test_repeticao_antes_do_bloco_e_permitida(self):
        self.assertTrue(
            sequencia_aparece(
                ['Bm', 'Bm', 'G', 'D', 'A'], ['Bm', 'G', 'D', 'A']
            )
        )

    def test_repeticao_dentro_do_bloco_quebra(self):
        self.assertFalse(
            sequencia_aparece(
                ['Bm', 'G', 'G', 'D', 'A'], ['Bm', 'G', 'D', 'A']
            )
        )

    def test_repeticao_fora_do_bloco_e_permitida(self):
        self.assertTrue(
            sequencia_aparece(
                ['Bm', 'G', 'D', 'A', 'Bm'], ['Bm', 'G', 'D', 'A']
            )
        )

    def test_sequencia_com_repeticao_exige_bloco_repetido(self):
        self.assertFalse(
            sequencia_aparece(['Bm', 'G', 'D', 'A'], ['Bm', 'Bm', 'G', 'D', 'A'])
        )
        self.assertTrue(
            sequencia_aparece(
                ['Bm', 'Bm', 'G', 'D', 'A'], ['Bm', 'Bm', 'G', 'D', 'A']
            )
        )


class RegressaoDoAlgoritmoTest(unittest.TestCase):

    def test_as_seis_sequencias_reproduzem_o_baseline(self):
        for nome, acordes in SEQUENCIAS_BASELINE.items():
            with self.subTest(sequencia=acordes):
                with open(BASELINE_DIR / ('%s.json' % nome)) as arquivo:
                    esperado = set(json.load(arquivo))
                obtido = set(calcular_matches(acordes, main.musicas.values()))
                self.assertEqual(obtido, esperado)


if __name__ == '__main__':
    unittest.main()
