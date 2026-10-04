
import ctypes
import sys
import sdl2
from math import ceil, floor

class Canvas:
    def __init__(self, largura, altura, titulo="Minha Biblioteca 2D"):
        self.largura = largura
        self.altura = altura

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

        x_tela = round(centro_x + x)
        y_tela = round(centro_y - y)

        return x_tela, y_tela

    # ==========================================
    # CONVERTER TELA PARA MUNDO
    # ==========================================
    def tela_para_mundo(self, x, y):
        centro_x = self.largura_real / 2
        centro_y = self.altura_real / 2

        x_mundo = x - centro_x
        y_mundo = centro_y - y

        return x_mundo, y_mundo

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
    
    def preencher_poligono(self, vertices, r, g, b):
        if len(vertices) < 3:
            raise ValueError("Um polígono precisa de pelo menos 3 vértices.")

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

    # Retângulo vermelho preenchido
    canvas.retangulo_preenchido(
        -350, 200, 180, 120,
        255, 0, 0
    )

    # Triângulo verde preenchido
    canvas.triangulo_preenchido(
        -100, 50,
        50, 50,
        -25, 200,
        0, 255, 0
    )

    # Pentágono azul preenchido
    canvas.poligono_preenchido(
        [
            (150, 150),
            (250, 200),
            (300, 100),
            (250, 0),
            (150, 50)
        ],
        0, 100, 255
    )

    # Hexágono amarelo preenchido
    canvas.poligono_preenchido(
        [
            (-300, -50),
            (-250, -100),
            (-180, -100),
            (-130, -50),
            (-180, 0),
            (-250, 0)
        ],
        255, 255, 0
    )
    
    # ------------------------------------------
    # ATUALIZAR E EXIBIR
    # ------------------------------------------
    canvas.atualizar()
    canvas.executar()