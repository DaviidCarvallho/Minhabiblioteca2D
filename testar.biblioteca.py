
import unittest
from math import isclose

from Main import Canvas


class TestesBiblioteca2D(unittest.TestCase):

    def setUp(self):
        # Cria o Canvas sem inicializar a janela SDL2.
        self.canvas = Canvas.__new__(Canvas)

        self.canvas.largura = 100
        self.canvas.altura = 80
        self.canvas.largura_real = 100
        self.canvas.altura_real = 80

        self.canvas.camera_x = 0
        self.canvas.camera_y = 0
        self.canvas.zoom = 1.0

        # Registra os pixels que seriam desenhados.
        self.pixels = []

        self.canvas.pixel = (
            lambda x, y, r, g, b:
            self.pixels.append((x, y, r, g, b))
        )

    # ------------------------------------------
    # SISTEMA DE COORDENADAS
    # ------------------------------------------

    def test_mundo_para_tela_origem(self):
        resultado = self.canvas.mundo_para_tela(0, 0)
        self.assertEqual(resultado, (50, 40))

    def test_mundo_para_tela_pontos(self):
        self.assertEqual(
            self.canvas.mundo_para_tela(10, 10),
            (60, 30)
        )

    def test_tela_para_mundo(self):
        x, y = self.canvas.tela_para_mundo(60, 30)

        self.assertAlmostEqual(x, 10)
        self.assertAlmostEqual(y, 10)

    def test_conversao_ida_e_volta(self):
        pontos = [(0, 0), (10, 15), (-20, 5), (30, -10)]

        for x, y in pontos:
            tela_x, tela_y = self.canvas.mundo_para_tela(x, y)
            mundo_x, mundo_y = self.canvas.tela_para_mundo(
                tela_x, tela_y
            )

            self.assertAlmostEqual(mundo_x, x)
            self.assertAlmostEqual(mundo_y, y)

    # ------------------------------------------
    # CÂMERA E ZOOM
    # ------------------------------------------

    def test_mover_camera(self):
        self.canvas.mover_camera(10, -5)

        self.assertEqual(self.canvas.camera_x, 10)
        self.assertEqual(self.canvas.camera_y, -5)

    def test_zoom(self):
        self.canvas.definir_zoom(2)

        self.assertEqual(self.canvas.zoom, 2)

        x, y = self.canvas.mundo_para_tela(10, 10)
        self.assertEqual((x, y), (70, 20))

    def test_zoom_invalido(self):
        for fator in (0, -1, -0.5):
            with self.assertRaises(ValueError):
                self.canvas.definir_zoom(fator)

    def test_camera_altera_conversao(self):
        self.canvas.mover_camera(10, 5)

        self.assertEqual(
            self.canvas.mundo_para_tela(10, 5),
            (50, 40)
        )

    # ------------------------------------------
    # RECORTE DE LINHAS
    # ------------------------------------------

    def test_linha_interna_nao_e_recortada(self):
        resultado = self.canvas.recortar_linha(
            -10, 0, 10, 0
        )

        self.assertEqual(resultado, (-10, 0, 10, 0))

    def test_linha_externa_e_descartada(self):
        resultado = self.canvas.recortar_linha(
            -100, 0, -80, 10
        )

        self.assertIsNone(resultado)

    def test_linha_horizontal_cortada(self):
        resultado = self.canvas.recortar_linha(
            -100, 0, 100, 0
        )

        self.assertIsNotNone(resultado)

        x1, y1, x2, y2 = resultado

        self.assertAlmostEqual(x1, -50)
        self.assertAlmostEqual(y1, 0)
        self.assertAlmostEqual(x2, 50)
        self.assertAlmostEqual(y2, 0)

    def test_linha_vertical_cortada(self):
        resultado = self.canvas.recortar_linha(
            0, -100, 0, 100
        )

        self.assertIsNotNone(resultado)

        x1, y1, x2, y2 = resultado

        self.assertAlmostEqual(x1, 0)
        self.assertAlmostEqual(y1, -40)
        self.assertAlmostEqual(x2, 0)
        self.assertAlmostEqual(y2, 40)

    def test_linha_com_zoom(self):
        self.canvas.definir_zoom(2)

        resultado = self.canvas.recortar_linha(
            -100, 0, 100, 0
        )

        self.assertIsNotNone(resultado)
        self.assertAlmostEqual(resultado[0], -25)
        self.assertAlmostEqual(resultado[2], 25)

    # ------------------------------------------
    # RECORTE DE POLÍGONOS
    # ------------------------------------------

    def test_poligono_interno(self):
        vertices = [
            (-10, -10),
            (10, -10),
            (10, 10),
            (-10, 10)
        ]

        resultado = self.canvas.recortar_poligono(vertices)

        self.assertEqual(len(resultado), 4)
        self.assertEqual(resultado, vertices)

    def test_poligono_externo(self):
        vertices = [
            (100, 100),
            (120, 100),
            (120, 120),
            (100, 120)
        ]

        resultado = self.canvas.recortar_poligono(vertices)

        self.assertEqual(resultado, [])

    def test_poligono_parcialmente_visivel(self):
        vertices = [
            (-100, -20),
            (0, -20),
            (0, 20),
            (-100, 20)
        ]

        resultado = self.canvas.recortar_poligono(vertices)

        self.assertGreaterEqual(len(resultado), 3)

        for x, y in resultado:
            self.assertGreaterEqual(x, -50)
            self.assertLessEqual(x, 50)
            self.assertGreaterEqual(y, -40)
            self.assertLessEqual(y, 40)

    def test_poligono_com_menos_de_tres_vertices(self):
        self.assertEqual(
            self.canvas.recortar_poligono([(0, 0), (1, 1)]),
            []
        )

    # ------------------------------------------
    # TRANSLAÇÃO, ESCALA E ROTAÇÃO
    # ------------------------------------------

    def test_transladar_ponto(self):
        resultado = self.canvas.transformar_ponto(
            2, 3, 5, -1
        )

        self.assertEqual(resultado, (7, 2))

    def test_transladar_poligono(self):
        vertices = [(0, 0), (2, 0), (2, 2)]

        resultado = self.canvas.transladar_poligono(
            vertices, 3, 4
        )

        self.assertEqual(
            resultado,
            [(3, 4), (5, 4), (5, 6)]
        )

    def test_escalar_ponto(self):
        resultado = self.canvas.escalar_ponto(
            3, 4, 2, 3
        )

        self.assertEqual(resultado, (6, 12))

    def test_escalar_poligono(self):
        vertices = [(1, 1), (2, 2)]

        resultado = self.canvas.escalar_poligono(
            vertices, 2, 3
        )

        self.assertEqual(resultado, [(2, 3), (4, 6)])

    def test_rotacao_90_graus(self):
        x, y = self.canvas.rotacionar_ponto(1, 0, 90)

        self.assertAlmostEqual(x, 0, places=7)
        self.assertAlmostEqual(y, 1, places=7)

    def test_rotacao_180_graus(self):
        x, y = self.canvas.rotacionar_ponto(1, 0, 180)

        self.assertAlmostEqual(x, -1, places=7)
        self.assertAlmostEqual(y, 0, places=7)

    # ------------------------------------------
    # MATRIZES
    # ------------------------------------------

    def test_matriz_translacao(self):
        matriz = self.canvas.matriz_translacao(5, 3)

        resultado = self.canvas.aplicar_matriz(
            matriz, 2, 4
        )

        self.assertEqual(resultado, (7, 7))

    def test_matriz_escala(self):
        matriz = self.canvas.matriz_escala(2, 3)

        resultado = self.canvas.aplicar_matriz(
            matriz, 2, 4
        )

        self.assertEqual(resultado, (4, 12))

    def test_matriz_rotacao_90(self):
        matriz = self.canvas.matriz_rotacao(90)

        x, y = self.canvas.aplicar_matriz(
            matriz, 1, 0
        )

        self.assertAlmostEqual(x, 0, places=7)
        self.assertAlmostEqual(y, 1, places=7)

    def test_multiplicacao_matrizes(self):
        A = [
            [1, 2],
            [3, 4]
        ]

        B = [
            [5, 6],
            [7, 8]
        ]

        resultado = self.canvas.multiplicar_matrizes(A, B)

        self.assertEqual(
            resultado,
            [[19, 22], [43, 50]]
        )

    def test_compor_transformacoes(self):
        escala = self.canvas.matriz_escala(2, 2)
        translacao = self.canvas.matriz_translacao(5, 3)

        matriz = self.canvas.compor_transformacoes(
            translacao, escala
        )

        resultado = self.canvas.aplicar_matriz(
            matriz, 1, 1
        )

        self.assertEqual(resultado, (7, 5))

    def test_composicao_vazia_retorna_identidade(self):
        matriz = self.canvas.compor_transformacoes()

        self.assertEqual(
            matriz,
            [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1]
            ]
        )

    # ------------------------------------------
    # DESENHO DE LINHAS E FORMAS
    # ------------------------------------------

    def test_linha_horizontal_desenha_pixels(self):
        self.canvas.linha_bresenham(
            -5, 0, 5, 0, 255, 0, 0
        )

        self.assertGreater(len(self.pixels), 0)

        # Os pontos devem estar dentro da superfície.
        for x, y, r, g, b in self.pixels:
            self.assertTrue(0 <= x < 100)
            self.assertTrue(0 <= y < 80)
            self.assertEqual((r, g, b), (255, 0, 0))

    def test_linha_fora_da_janela_nao_desenha(self):
        ...

    def test_linha_com_ponto_unico(self):
        self.canvas.linha_bresenham(
            0, 0, 0, 0, 255, 255, 255
        )

        self.assertEqual(len(self.pixels), 1)

    def test_dda_desenha_linha(self):
        self.canvas.linha(
            -5, 0, 5, 0, 0, 255, 0
        )

        self.assertGreater(len(self.pixels), 0)

    def test_retangulo_desenha_bordas(self):
        self.canvas.retangulo(
            -10, 10, 20, 20, 255, 255, 0
        )

        self.assertGreater(len(self.pixels), 0)

    def test_triangulo_desenha_bordas(self):
        self.canvas.triangulo(
            -10, -10, 10, -10, 0, 10,
            255, 255, 255
        )

        self.assertGreater(len(self.pixels), 0)

    def test_poligono_invalido_gera_erro(self):
        with self.assertRaises(ValueError):
            self.canvas.poligono(
                [(0, 0), (1, 1)], 255, 0, 0
            )

    def test_preenchimento_poligono(self):
        vertices = [
            (-10, -10),
            (10, -10),
            (10, 10),
            (-10, 10)
        ]

        self.canvas.preencher_poligono(
            vertices, 0, 255, 255
        )

        self.assertGreater(len(self.pixels), 0)

    def test_poligono_preenchido(self):
        vertices = [
            (-10, -10),
            (10, -10),
            (10, 10),
            (-10, 10)
        ]

        self.canvas.poligono_preenchido(
            vertices, 100, 150, 200
        )

        self.assertGreater(len(self.pixels), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
