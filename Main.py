
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

        # Obter superfície da janela
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

    def pixel(self, x, y, r, g, b):
        # Validar coordenadas
        if not (0 <= x < self.largura_real):
            return

        if not (0 <= y < self.altura_real):
            return

        # Validar componentes RGB
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise ValueError("RGB deve estar entre 0 e 255")

        # Calcular posição na memória
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

    def atualizar(self):
        if sdl2.SDL_UpdateWindowSurface(self.window) != 0:
            erro = sdl2.SDL_GetError().decode("utf-8")
            raise RuntimeError(erro)

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


if __name__ == "__main__":
    canvas = Canvas(800, 600)

    # Pixel vermelho no centro
    canvas.pixel(400, 300, 255, 0, 0)

    # Pixel verde no canto superior esquerdo
    canvas.pixel(0, 0, 0, 255, 0)

    # Pixel azul no canto inferior direito
    canvas.pixel(799, 599, 0, 0, 255)

    # Apresentar os pixels na janela
    canvas.atualizar()

    # Manter a janela aberta
    canvas.executar()