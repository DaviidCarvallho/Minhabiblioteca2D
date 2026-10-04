
import ctypes
import sys
import sdl2
from math import ceil, floor, sin, cos, radians

class Canvas:
    def __init__(self, largura, altura, titulo="Minha Biblioteca 2D"):
        self.largura = largura
        self.altura = altura
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # Inicializar SDL2
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            raise RuntimeError(
                sdl2.SDL_GetError().decode("utf-8")
            )

        # Criar janela
        self.window = sdl2.SDL_CreateWindow(
            titulo.encode("utf-8"),
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            largura,
            altura,
            sdl2.SDL_WINDOW_SHOWN
        )

        if not self.window:
            erro = sdl2.SDL_GetError().decode("utf-8")
            sdl2.SDL_Quit()
            raise RuntimeError(erro)

        # Obter a superfície da janela
        self.surface = sdl2.SDL_GetWindowSurface(self.window)

        if not self.surface:
            erro = sdl2.SDL_GetError().decode("utf-8")
            sdl2.SDL_DestroyWindow(self.window)
            sdl2.SDL_Quit()
            raise RuntimeError(erro)

        # Consultar propriedades da superfície
        self.largura_real = self.surface.contents.w
        self.altura_real = self.surface.contents.h
        self.pitch = self.surface.contents.pitch

        self.bytes_por_pixel = (
            self.surface.contents.format.contents.BytesPerPixel
        )

        print("Largura:", self.largura_real)
        print("Altura:", self.altura_real)
        print("Pitch:", self.pitch)
        print("Bytes por pixel:", self.bytes_por_pixel)

    # ==========================================
    # DESENHAR UM PIXEL
    # ==========================================
    def pixel(self, x, y, r, g, b):
        # Validar coordenadas
        if not (0 <= x < self.largura_real):
            return

        if not (0 <= y < self.altura_real):
            return

        # Validar componentes RGB
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("RGB deve estar entre 0 e 255")

        # Garantir coordenadas inteiras
        x = int(x)
        y = int(y)

        # Calcular posição do pixel na memória
        offset = (
            y * self.pitch +
            x * self.bytes_por_pixel
        )

        # Bloquear a superfície
        if sdl2.SDL_LockSurface(self.surface) != 0:
            erro = sdl2.SDL_GetError().decode("utf-8")
            raise RuntimeError(erro)

        try:
            # Converter RGB para o formato da superfície
            formato = self.surface.contents.format

            cor_mapeada = sdl2.SDL_MapRGB(
                formato, r, g, b
            )

            # Transformar a cor em bytes
            bytes_cor = cor_mapeada.to_bytes(
                self.bytes_por_pixel,
                byteorder=sys.byteorder
            )

            # Obter endereço da memória
            endereco_base = ctypes.cast(
                self.surface.contents.pixels,
                ctypes.c_void_p
            ).value

            # Encontrar endereço do pixel
            endereco_pixel = endereco_base + offset

            # Escrever os bytes diretamente
            ctypes.memmove(
                endereco_pixel,
                bytes_cor,
                self.bytes_por_pixel
            )

        finally:
            # Liberar a superfície
            sdl2.SDL_UnlockSurface(self.surface)
    
    # ==========================================
    # CONVERTER MUNDO PARA TELA
    # ==========================================
    # ALTERAÇÃO: agora considera posição da câmera e zoom.
    def mundo_para_tela(self, x, y):
        centro_x = self.largura_real / 2
        centro_y = self.altura_real / 2

        x_tela = centro_x + (x - self.camera_x) * self.zoom
        y_tela = centro_y - (y - self.camera_y) * self.zoom

        return round(x_tela), round(y_tela)

    # ==========================================
    # CONVERTER TELA PARA MUNDO
    # ==========================================
    # ALTERAÇÃO: conversão inversa considerando câmera e zoom.
    def tela_para_mundo(self, x, y):
        centro_x = self.largura_real / 2
        centro_y = self.altura_real / 2

        x_mundo = (x - centro_x) / self.zoom + self.camera_x
        y_mundo = (centro_y - y) / self.zoom + self.camera_y

        return x_mundo, y_mundo

    # NOVO: deslocar o ponto do mundo que fica no centro da tela.
    def mover_camera(self, dx, dy):
        self.camera_x += dx
        self.camera_y += dy

    # NOVO: definir a escala de visualização.
    def definir_zoom(self, fator):
        if fator <= 0:
            raise ValueError("O zoom deve ser maior que zero")
        self.zoom = fator

    # NOVO: limpar a superfície com uma cor de fundo (preto por padrão).
    def limpar(self, r=0, g=0, b=0):
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("RGB deve estar entre 0 e 255")
        formato = self.surface.contents.format
        cor = sdl2.SDL_MapRGB(formato, r, g, b)
        if sdl2.SDL_FillRect(self.surface, None, cor) != 0:
            erro = sdl2.SDL_GetError().decode("utf-8")
            raise RuntimeError(erro)

    def linha(self, x1, y1, x2, y2, r, g, b):
        # Converter as coordenadas cartesianas para tela
        x1, y1 = self.mundo_para_tela(x1, y1)
        x2, y2 = self.mundo_para_tela(x2, y2)

        # Calcular as diferenças entre os pontos
        dx = x2 - x1
        dy = y2 - y1

        # Determinar a quantidade de passos
        passos = max(abs(dx), abs(dy))

        # Caso seja uma linha de apenas um ponto
        if passos == 0:
            self.pixel(x1, y1, r, g, b)
            return

        # Calcular os incrementos por passo
        x_incremento = dx / passos
        y_incremento = dy / passos

        # Iniciar no primeiro ponto
        x = x1
        y = y1

        # Desenhar cada pixel da linha
        for _ in range(passos + 1):
            self.pixel(round(x), round(y), r, g, b)

            x += x_incremento
            y += y_incremento


    def linha_bresenham(self, x1, y1, x2, y2, r, g, b):
        # Converter coordenadas cartesianas para tela
        x1, y1 = self.mundo_para_tela(x1, y1)
        x2, y2 = self.mundo_para_tela(x2, y2)

        # Diferenças absolutas
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        # Definir a direção do movimento
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        # Erro inicial
        erro = dx - dy

        # Percorrer os pixels até alcançar o ponto final
        while True:
            # Desenhar o pixel atual
            self.pixel(x1, y1, r, g, b)

            # Parar quando chegar ao ponto final
            if x1 == x2 and y1 == y2:
                break

            # Dobrar o erro para tomar as decisões
            erro_dobrado = 2 * erro

            # Decidir se avança no eixo X
            if erro_dobrado > -dy:
                erro -= dy
                x1 += sx

            # Decidir se avança no eixo Y
            if erro_dobrado < dx:
                erro += dx
                y1 += sy   
            
    def retangulo(self, x, y, largura, altura, r, g, b):
        x1, y1 = x, y
        x2, y2 = x + largura, y
        x3, y3 = x + largura, y - altura
        x4, y4 = x, y - altura

        self.linha_bresenham(x1, y1, x2, y2, r, g, b)
        self.linha_bresenham(x2, y2, x3, y3, r, g, b)
        self.linha_bresenham(x3, y3, x4, y4, r, g, b)
        self.linha_bresenham(x4, y4, x1, y1, r, g, b)


    def triangulo(self, x1, y1, x2, y2, x3, y3, r, g, b):
        self.linha_bresenham(x1, y1, x2, y2, r, g, b)
        self.linha_bresenham(x2, y2, x3, y3, r, g, b)
        self.linha_bresenham(x3, y3, x1, y1, r, g, b)


    def poligono(self, vertices, r, g, b):
        if len(vertices) < 3:
            raise ValueError("Um polígono precisa de pelo menos 3 vértices.")

        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]

            self.linha_bresenham(x1, y1, x2, y2, r, g, b)
    
    # ALTERAÇÃO: rasteriza o preenchimento em coordenadas de tela.
    # Isso mantém o interior contínuo também quando o zoom é diferente de 1.
    def preencher_poligono(self, vertices, r, g, b):
        if len(vertices) < 3:
            raise ValueError("Um polígono precisa de pelo menos 3 vértices.")

        vertices_tela = [self.mundo_para_tela(x, y) for x, y in vertices]
        y_min = min(y for x, y in vertices_tela)
        y_max = max(y for x, y in vertices_tela)

        for y in range(max(0, y_min), min(self.altura_real - 1, y_max) + 1):
            intersecoes = []
            for i in range(len(vertices_tela)):
                x1, y1 = vertices_tela[i]
                x2, y2 = vertices_tela[(i + 1) % len(vertices_tela)]

                if min(y1, y2) <= y < max(y1, y2):
                    x_intersecao = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                    intersecoes.append(x_intersecao)

            intersecoes.sort()
            for i in range(0, len(intersecoes) - 1, 2):
                x_inicio = max(0, ceil(intersecoes[i]))
                x_fim = min(self.largura_real - 1, floor(intersecoes[i + 1]))
                for x in range(x_inicio, x_fim + 1):
                    self.pixel(x, y, r, g, b)

    def retangulo_preenchido(self, x, y, largura, altura, r, g, b):
        vertices = [
            (x, y),
            (x + largura, y),
            (x + largura, y - altura),
            (x, y - altura)
        ]

        self.preencher_poligono(vertices, r, g, b)
        self.poligono(vertices, r, g, b)


    def triangulo_preenchido(self, x1, y1, x2, y2, x3, y3, r, g, b):
        vertices = [
            (x1, y1),
            (x2, y2),
            (x3, y3)
        ]

        self.preencher_poligono(vertices, r, g, b)
        self.poligono(vertices, r, g, b)


    def poligono_preenchido(self, vertices, r, g, b):
        self.preencher_poligono(vertices, r, g, b)
        self.poligono(vertices, r, g, b)
    

    def transformar_ponto(self, x, y, tx=0, ty=0):
        novo_x = x + tx
        novo_y = y + ty
        return novo_x, novo_y

    def transladar_poligono(self, vertices, tx, ty):
        novos_vertices = []

        for x, y in vertices:
            novo_x, novo_y = self.transformar_ponto(x, y, tx, ty)
            novos_vertices.append((novo_x, novo_y))

        return novos_vertices
    
    def escalar_ponto(self, x, y, sx=1, sy=1):
        novo_x = x * sx
        novo_y = y * sy

        return novo_x, novo_y

    def escalar_poligono(self, vertices, sx, sy):
        novos_vertices = []

        for x, y in vertices:
            novo_x, novo_y = self.escalar_ponto(x, y, sx, sy)
            novos_vertices.append((novo_x, novo_y))

        return novos_vertices
    

    def rotacionar_ponto(self, x, y, angulo):
        # Converter graus para radianos
        theta = radians(angulo)

        # Calcular seno e cosseno
        cos_theta = cos(theta)
        sin_theta = sin(theta)

        # Aplicar as fórmulas da rotação
        novo_x = x * cos_theta - y * sin_theta
        novo_y = x * sin_theta + y * cos_theta

        return novo_x, novo_y


    def rotacionar_poligono(self, vertices, angulo):
        novos_vertices = []

        for x, y in vertices:
            novo_x, novo_y = self.rotacionar_ponto(
                x, y, angulo
            )

            novos_vertices.append((novo_x, novo_y))

        return novos_vertices


    
    def matriz_translacao(self, tx, ty):
        return [
            [1, 0, tx],
            [0, 1, ty],
            [0, 0, 1]
        ]

    def matriz_escala(self, sx, sy):
        return [
            [sx, 0, 0],
            [0, sy, 0],
            [0, 0, 1]
        ]

    def matriz_rotacao(self, angulo):
        theta = radians(angulo)

        c = cos(theta)
        s = sin(theta)

        return [
            [c, -s, 0],
            [s,  c, 0],
            [0,  0, 1]
        ]


    
    def multiplicar_matrizes(self, A, B):
        linhas_A = len(A)
        colunas_A = len(A[0])
        colunas_B = len(B[0])

        resultado = [
            [0 for _ in range(colunas_B)]
            for _ in range(linhas_A)
        ]

        for i in range(linhas_A):
            for j in range(colunas_B):
                for k in range(colunas_A):
                    resultado[i][j] += A[i][k] * B[k][j]

        return resultado

    
    def aplicar_matriz(self, matriz, x, y):
        ponto = [x, y, 1]

        resultado = [0, 0, 0]

        for i in range(3):
            for j in range(3):
                resultado[i] += matriz[i][j] * ponto[j]

        return resultado[0], resultado[1]

    
    def transformar_poligono_matriz(self, vertices, matriz):
        novos_vertices = []

        for x, y in vertices:
            novo_x, novo_y = self.aplicar_matriz(
                matriz, x, y
            )

            novos_vertices.append((novo_x, novo_y))

        return novos_vertices

    
    def compor_transformacoes(self, *matrizes):
        if not matrizes:
            return [
                [1, 0, 0],
                [0, 1, 0],
                [0, 0, 1]
            ]

        resultado = matrizes[0]

        for matriz in matrizes[1:]:
            resultado = self.multiplicar_matrizes(
                resultado, matriz
            )

        return resultado
    
    # ==========================================
    # ATUALIZAR JANELA
    # ==========================================
    def atualizar(self):
        if sdl2.SDL_UpdateWindowSurface(self.window) != 0:
            erro = sdl2.SDL_GetError().decode("utf-8")
            raise RuntimeError(erro)

    # ==========================================
    # MANTER JANELA ABERTA
    # ==========================================
    def executar(self):
        evento = sdl2.SDL_Event()
        rodando = True

        try:
            while rodando:
                while sdl2.SDL_PollEvent(
                    ctypes.byref(evento)
                ):
                    if evento.type == sdl2.SDL_QUIT:
                        rodando = False

                sdl2.SDL_Delay(16)

        finally:
            sdl2.SDL_DestroyWindow(self.window)
            sdl2.SDL_Quit()


# ==========================================
# PROGRAMA PRINCIPAL — TESTE DE CÂMERA E ZOOM
# ==========================================

if __name__ == "__main__":
    canvas = Canvas(800, 600)

    # Triângulo original, definido em coordenadas do mundo.
    vertices = [
        (-50, 0),
        (50, 0),
        (0, 100)
    ]

    # Transformações geométricas por matrizes (mantidas da etapa anterior).
    escala = canvas.matriz_escala(1.5, 1.5)
    rotacao = canvas.matriz_rotacao(45)
    translacao = canvas.matriz_translacao(150, 50)

    # Com vetores-coluna, a ordem de aplicação é da direita para a esquerda:
    # escala, depois rotação e, por fim, translação.
    matriz_final = canvas.compor_transformacoes(
        translacao,
        rotacao,
        escala
    )
    novos_vertices = canvas.transformar_poligono_matriz(vertices, matriz_final)

    # Estado 1: triângulo original em vermelho.
    canvas.limpar(0, 0, 0)
    canvas.poligono(vertices, 255, 0, 0)
    canvas.atualizar()
    sdl2.SDL_Delay(1200)

    # Estado 2: polígono transformado em verde e visualização ampliada.
    canvas.limpar(0, 0, 0)
    canvas.definir_zoom(2.0)
    canvas.poligono(novos_vertices, 0, 255, 0)
    canvas.atualizar()
    sdl2.SDL_Delay(1200)

    # Estado 3: câmera deslocada no eixo X; o polígono aparece azul.
    canvas.limpar(0, 0, 0)
    canvas.mover_camera(50, 0)
    canvas.poligono(novos_vertices, 0, 0, 255)
    
    # ------------------------------------------
    # ATUALIZAR E EXIBIR
    # ------------------------------------------
    canvas.atualizar()
    canvas.executar()