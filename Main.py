
import ctypes
import sys
import sdl2


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

    # Eixo X
    for x in range(canvas.largura_real):
        canvas.pixel(x, 300, 100, 100, 100)

    # Eixo Y
    for y in range(canvas.altura_real):
        canvas.pixel(400, y, 100, 100, 100)

    # Linha diagonal crescente no plano cartesiano
    canvas.linha_bresenham(
        -150, -100,
        150, 100,
        255, 0, 0
    )

    # Linha com inclinação diferente
    canvas.linha_bresenham(
        -150, 0,
        150, 100,
        0, 255, 0
    )

    # Linha diagonal no sentido oposto
    canvas.linha_bresenham(
        -150, 100,
        150, -100,
        0, 100, 255
    )

    # Linha vertical
    canvas.linha_bresenham(
        100, -150,
        100, 150,
        255, 255, 0
    )

    # Linha horizontal
    canvas.linha_bresenham(
        -300, 50,
        300, 50,
        255, 0, 255
    )


    # ------------------------------------------
    # ATUALIZAR E EXIBIR
    # ------------------------------------------
    canvas.atualizar()
    canvas.executar()