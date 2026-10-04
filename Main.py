
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
    def mundo_para_tela(self, x, y):
        centro_x = self.largura_real / 2
        centro_y = self.altura_real / 2

        x_tela = centro_x + (x - self.camera_x) * self.zoom
        y_tela = centro_y - (y - self.camera_y) * self.zoom

        return round(x_tela), round(y_tela)

    # ==========================================
    # CONVERTER TELA PARA MUNDO
    # ==========================================
    def tela_para_mundo(self, x, y):
        centro_x = self.largura_real / 2
        centro_y = self.altura_real / 2

        x_mundo = (x - centro_x) / self.zoom + self.camera_x
        y_mundo = (centro_y - y) / self.zoom + self.camera_y

        return x_mundo, y_mundo

    # ==========================================
    # CONTROLES DA CAMERA
    # ==========================================
    def mover_camera(self, dx, dy):
        self.camera_x += dx
        self.camera_y += dy

    def definir_zoom(self, fator):
        if fator <= 0:
            raise ValueError("O zoom deve ser maior que zero")
        self.zoom = fator

    # ==========================================
    # RECORTE DE LINHAS - COHEN-SUTHERLAND
    # ==========================================
    def recortar_linha(self, x1, y1, x2, y2):
        meia_largura = self.largura_real / (2 * self.zoom)
        meia_altura = self.altura_real / (2 * self.zoom)

        xmin = self.camera_x - meia_largura
        xmax = self.camera_x + meia_largura
        ymin = self.camera_y - meia_altura
        ymax = self.camera_y + meia_altura

        ESQUERDA = 1
        DIREITA = 2
        ABAIXO = 4
        ACIMA = 8

        def codigo_regiao(x, y):
            codigo = 0
            if x < xmin:
                codigo |= ESQUERDA
            elif x > xmax:
                codigo |= DIREITA
            if y < ymin:
                codigo |= ABAIXO
            elif y > ymax:
                codigo |= ACIMA
            return codigo

        codigo1 = codigo_regiao(x1, y1)
        codigo2 = codigo_regiao(x2, y2)

        while True:
            if codigo1 == 0 and codigo2 == 0:
                return x1, y1, x2, y2
            if codigo1 & codigo2:
                return None

            codigo_fora = codigo1 if codigo1 != 0 else codigo2

            if codigo_fora & ACIMA:
                if y2 == y1:
                    return None
                x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1)
                y = ymax
            elif codigo_fora & ABAIXO:
                if y2 == y1:
                    return None
                x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1)
                y = ymin
            elif codigo_fora & DIREITA:
                if x2 == x1:
                    return None
                y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1)
                x = xmax
            else:
                if x2 == x1:
                    return None
                y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1)
                x = xmin

            if codigo_fora == codigo1:
                x1, y1 = x, y
                codigo1 = codigo_regiao(x1, y1)
            else:
                x2, y2 = x, y
                codigo2 = codigo_regiao(x2, y2)

    # ==========================================
    # RECORTE DE POLIGONOS - SUTHERLAND-HODGMAN
    # ==========================================
    def recortar_poligono(self, vertices):
        if len(vertices) < 3:
            return []

        meia_largura = self.largura_real / (2 * self.zoom)
        meia_altura = self.altura_real / (2 * self.zoom)
        xmin = self.camera_x - meia_largura
        xmax = self.camera_x + meia_largura
        ymin = self.camera_y - meia_altura
        ymax = self.camera_y + meia_altura

        def recortar_borda(pontos, dentro, intersecao):
            if not pontos:
                return []
            resultado = []
            anterior = pontos[-1]
            anterior_dentro = dentro(anterior)

            for atual in pontos:
                atual_dentro = dentro(atual)
                if atual_dentro:
                    if not anterior_dentro:
                        resultado.append(intersecao(anterior, atual))
                    resultado.append(atual)
                elif anterior_dentro:
                    resultado.append(intersecao(anterior, atual))
                anterior = atual
                anterior_dentro = atual_dentro
            return resultado

        # Esquerda
        vertices = recortar_borda(
            vertices, lambda p: p[0] >= xmin,
            lambda a, b: (xmin, a[1] + (b[1] - a[1]) *
                          (xmin - a[0]) / (b[0] - a[0]))
        )
        # Direita
        vertices = recortar_borda(
            vertices, lambda p: p[0] <= xmax,
            lambda a, b: (xmax, a[1] + (b[1] - a[1]) *
                          (xmax - a[0]) / (b[0] - a[0]))
        )
        # Inferior
        vertices = recortar_borda(
            vertices, lambda p: p[1] >= ymin,
            lambda a, b: (a[0] + (b[0] - a[0]) *
                          (ymin - a[1]) / (b[1] - a[1]), ymin)
        )
        # Superior
        vertices = recortar_borda(
            vertices, lambda p: p[1] <= ymax,
            lambda a, b: (a[0] + (b[0] - a[0]) *
                          (ymax - a[1]) / (b[1] - a[1]), ymax)
        )
        return vertices

    # ==========================================
    # LIMPAR A SUPERFICIE
    # ==========================================
    def limpar(self, r=0, g=0, b=0):
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("RGB deve estar entre 0 e 255")
        cor = sdl2.SDL_MapRGB(
            self.surface.contents.format, r, g, b
        )
        if sdl2.SDL_FillRect(self.surface, None, cor) != 0:
            erro = sdl2.SDL_GetError().decode("utf-8")
            raise RuntimeError(erro)

    def linha(self, x1, y1, x2, y2, r, g, b):
        # Converter as coordenadas cartesianas para tela
        # Recortar a linha antes de converter para pixels
        resultado = self.recortar_linha(x1, y1, x2, y2)
        if resultado is None:
            return
        x1, y1, x2, y2 = resultado

        # Converter as coordenadas do mundo para a tela
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
        # Recortar a linha antes de converter para pixels
        resultado = self.recortar_linha(x1, y1, x2, y2)
        if resultado is None:
            return
        x1, y1, x2, y2 = resultado

        # Converter as coordenadas do mundo para a tela
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
    
    def preencher_poligono(self, vertices, r, g, b):
        if len(vertices) < 3:
            raise ValueError("Um polígono precisa de pelo menos 3 vértices.")

        vertices = self.recortar_poligono(vertices)
        if len(vertices) < 3:
            return

        # Encontrar os limites verticais
        y_min = min(y for x, y in vertices)
        y_max = max(y for x, y in vertices)

        # Percorrer cada linha horizontal do polígono
        for y in range(ceil(y_min), floor(y_max) + 1):
            intersecoes = []

            # Verificar a interseção da linha com cada aresta
            for i in range(len(vertices)):
                x1, y1 = vertices[i]
                x2, y2 = vertices[(i + 1) % len(vertices)]

                # Ignorar arestas horizontais e evitar
                # contar duas vezes os vértices compartilhados
                if min(y1, y2) <= y < max(y1, y2):
                    x_intersecao = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                    intersecoes.append(x_intersecao)

            # Ordenar as interseções da esquerda para a direita
            intersecoes.sort()

            # Preencher entre cada par de interseções
            for i in range(0, len(intersecoes) - 1, 2):
                x_inicio = ceil(intersecoes[i])
                x_fim = floor(intersecoes[i + 1])

                for x in range(x_inicio, x_fim + 1):
                    tela_x, tela_y = self.mundo_para_tela(x, y)
                    self.pixel(tela_x, tela_y, r, g, b)
        
    def retangulo_preenchido(self, x, y, largura, altura, r, g, b):
        vertices = [
            (x, y),
            (x + largura, y),
            (x + largura, y - altura),
            (x, y - altura)
        ]

        vertices = self.recortar_poligono(vertices)
        if len(vertices) < 3:
            return
        self.preencher_poligono(vertices, r, g, b)
        self.poligono(vertices, r, g, b)


    def triangulo_preenchido(self, x1, y1, x2, y2, x3, y3, r, g, b):
        vertices = [
            (x1, y1),
            (x2, y2),
            (x3, y3)
        ]

        vertices = self.recortar_poligono(vertices)
        if len(vertices) < 3:
            return
        self.preencher_poligono(vertices, r, g, b)
        self.poligono(vertices, r, g, b)


    def poligono_preenchido(self, vertices, r, g, b):
        vertices = self.recortar_poligono(vertices)
        if len(vertices) < 3:
            return
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
# PROGRAMA PRINCIPAL
# ==========================================

if __name__ == "__main__":
    canvas = Canvas(800, 600)

    # Poligono parcialmente fora da janela
    vertices = [
        (-500, -200),
        (100, -200),
        (500, 100),
        (100, 400),
        (-500, 300)
    ]

    # Obter e exibir os vertices resultantes do recorte
    vertices_recortados = canvas.recortar_poligono(vertices)
    print("Vertices originais:", vertices)
    print("Vertices recortados:", vertices_recortados)

    # Desenhar o poligono recortado e preenchido
    canvas.limpar(20, 20, 30)
    canvas.poligono_preenchido(vertices, 100, 180, 255)

    # ------------------------------------------
    # ATUALIZAR E EXIBIR
    # ------------------------------------------
    canvas.atualizar()
    canvas.executar()