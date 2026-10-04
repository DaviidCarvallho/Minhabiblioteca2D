
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

    # Linha horizontal (vermelha)
    canvas.linha(-300, 200, 300, 200, 255, 0, 0)

    # Linha vertical (verde)
    canvas.linha(0, -250, 0, 250, 0, 255, 0)

    # Linha diagonal crescente (azul)
    canvas.linha(-250, -150, 250, 150, 0, 100, 255)

    # Linha diagonal decrescente (amarela)
    canvas.linha(-250, 150, 250, -150, 255, 255, 0)

    # Linha curta e inclinada (branca)
    canvas.linha(-100, -50, 100, 20, 255, 255, 255)

    # ------------------------------------------
    # ATUALIZAR E EXIBIR
    # ------------------------------------------
    canvas.atualizar()
    canvas.executar()