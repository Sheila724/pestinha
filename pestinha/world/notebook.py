"""
NOTEBOOK - o notebook do pet (só o desenho e o arrastar).

Fica sempre na tela, junto com o pet, e pode ser arrastado com o botão esquerdo.
A posição é lembrada em memory/panels.json. A decisão de trabalhar fica em
pestinha/mind/mesa.py; aqui só mostramos se ele está trabalhando (borda acesa).

Com "computador": "rack" no pets/<pet>.json, no lugar do notebook aparece um rack de servidores
desenhado (sem imagem), com os LEDs piscando enquanto ele trabalha.
"""

import random

from PySide6.QtCore import QLineF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QLinearGradient, QPainter, QPen, QPixmap
from .arrastavel import FloatingWidget

NOTEBOOK_W, NOTEBOOK_H = 110, 70     # tamanho do desenho de reserva
SPRITE_W = 150                       # largura da foto notebook.png (do pet ou de assets/comum/), se existir
MARGEM_TELA = 24                     # px da borda da tela no primeiro uso
RACK_W, RACK_H = 116, 96             # tamanho do rack de servidores desenhado
PISCA_MS = 260                       # LEDs do rack: intervalo entre piscadas enquanto ele trabalha

VERDE, AMBAR, AZUL = "#39e27a", "#ffb547", "#4fb3ff"


def _default_position(size):
    """Canto inferior direito da tela, onde o notebook começa."""
    screen = QGuiApplication.primaryScreen().availableGeometry()
    return (screen.right() - size[0] - MARGEM_TELA, screen.bottom() - size[1] - MARGEM_TELA)


def load_notebook_sprite(path):
    """Foto do notebook já no tamanho do jogo. None se o arquivo não existir."""
    if not path.exists():
        return None
    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None
    return pixmap.scaledToWidth(SPRITE_W, Qt.SmoothTransformation)


class Notebook(FloatingWidget):
    """Notebook do pet: a foto se existir, senão o desenho de reserva."""

    def __init__(self, app):
        """Carrega a imagem do notebook (ou usa o desenho de reserva, ou o rack) e o põe na tela."""
        self.rack = getattr(app, "computador", "notebook") == "rack"
        self.sprite = None if self.rack else load_notebook_sprite(app.conteudo.notebook)
        if self.rack:
            size = (RACK_W, RACK_H)
        else:
            size = (self.sprite.width(), self.sprite.height()) if self.sprite else (NOTEBOOK_W, NOTEBOOK_H)
        titulo = f"Rack do {app.nome}" if self.rack else f"Notebook do {app.nome}"
        super().__init__(app, "notebook", titulo, size, size, _default_position(size))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.working = False
        self.leds = _leds_parados()
        self.pisca = QTimer(self)                      # só roda no rack, enquanto ele trabalha
        self.pisca.timeout.connect(self._piscar)

    def set_working(self, working):
        """Acende a borda quando você está trabalhando (o pet sentado); no rack, os LEDs piscam."""
        if working != self.working:
            self.working = working
            if self.rack:
                if working:
                    self.pisca.start(PISCA_MS)
                else:
                    self.pisca.stop()
                    self.leds = _leds_parados()
            self.update()

    def _piscar(self):
        """Sorteia quais LEDs de atividade estão acesos neste instante."""
        self.leds = _leds_trabalhando()
        self.update()

    def paintEvent(self, _event):
        """Desenha o rack, ou o notebook (a imagem, se houver, senão o desenho de reserva)."""
        if self.rack:
            self._paint_rack()
        elif self.sprite is not None:
            self._paint_sprite()
        else:
            self._paint_desenho()

    def _paint_sprite(self):
        """Desenha a imagem do notebook suavizada."""
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.drawPixmap(0, 0, self.sprite)
        if self.working:                                   # trabalhando: contorno verde
            p.setPen(QPen(QColor("#63e56f"), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 6, 6)
        p.end()

    def _paint_desenho(self):
        """Verso da tampa, como na foto de referência: cinza fosco, sem logo, base prateada embaixo."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        tampa = QRectF(4, 3, NOTEBOOK_W - 8, NOTEBOOK_H - 14)
        gradiente = QLinearGradient(tampa.topLeft(), tampa.bottomLeft())
        gradiente.setColorAt(0.0, QColor("#5d6165"))
        gradiente.setColorAt(1.0, QColor("#3b3e41"))
        borda = QColor("#63e56f") if self.working else QColor("#24272a")
        p.setPen(QPen(borda, 2.5 if self.working else 1.2))
        p.setBrush(gradiente)
        p.drawRoundedRect(tampa, 6, 6)
        base = QRectF(2, NOTEBOOK_H - 13, NOTEBOOK_W - 4, 9)
        prata = QLinearGradient(base.topLeft(), base.bottomLeft())
        prata.setColorAt(0.0, QColor("#d9dcdf"))
        prata.setColorAt(1.0, QColor("#959a9f"))
        p.setPen(QPen(QColor("#5a5e62"), 1))
        p.setBrush(prata)
        p.drawRoundedRect(base, 3, 3)
        p.end()

    def _paint_rack(self):
        """Rack de servidores visto de frente: dois servidores, um storage e um switch, com LEDs."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = RACK_W, RACK_H
        gabinete = QRectF(3, 2, w - 6, h - 9)
        corpo = QLinearGradient(gabinete.topLeft(), gabinete.topRight())
        corpo.setColorAt(0.0, QColor("#2b3035"))
        corpo.setColorAt(0.5, QColor("#3a4046"))
        corpo.setColorAt(1.0, QColor("#24282c"))
        borda = QColor("#63e56f") if self.working else QColor("#15181b")
        p.setPen(QPen(borda, 2.5 if self.working else 1.2))
        p.setBrush(corpo)
        p.drawRoundedRect(gabinete, 5, 5)
        # pés
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#15181b"))
        p.drawRect(QRectF(10, h - 8, 12, 6))
        p.drawRect(QRectF(w - 22, h - 8, 12, 6))
        # trilhos laterais com furinhos
        p.setBrush(QColor("#1b1e21"))
        for x in (8, w - 14):
            p.drawRect(QRectF(x, 7, 6, h - 19))
        p.setBrush(QColor("#4a5056"))
        for x in (10, w - 12):
            y = 10
            while y < h - 14:
                p.drawRect(QRectF(x, y, 2, 2))
                y += 6
        # equipamentos: (y, altura, tipo)
        unidades = [(9, 15, "servidor"), (26, 15, "servidor"), (43, 22, "storage"), (67, 12, "switch")]
        for i, (y, altura, tipo) in enumerate(unidades):
            caixa = QRectF(16, y, w - 32, altura)
            frente = QLinearGradient(caixa.topLeft(), caixa.bottomLeft())
            frente.setColorAt(0.0, QColor("#565d64"))
            frente.setColorAt(1.0, QColor("#3d4349"))
            p.setPen(QPen(QColor("#1d2023"), 1))
            p.setBrush(frente)
            p.drawRoundedRect(caixa, 2, 2)
            if tipo == "switch":
                self._portas(p, caixa, i)
            elif tipo == "storage":
                self._discos(p, caixa, i)
            else:
                self._servidor(p, caixa, i)
        p.end()

    def _led(self, p, x, y, cor, aceso, raio=1.6):
        """Um LED redondo: aceso brilha na cor, apagado fica escuro."""
        p.setPen(Qt.NoPen)
        if aceso:
            brilho = QColor(cor)
            brilho.setAlpha(70)
            p.setBrush(brilho)
            p.drawEllipse(QRectF(x - raio * 2, y - raio * 2, raio * 4, raio * 4))
            p.setBrush(QColor(cor))
        else:
            p.setBrush(QColor("#1f2a22"))
        p.drawEllipse(QRectF(x - raio, y - raio, raio * 2, raio * 2))

    def _servidor(self, p, caixa, i):
        """Servidor 1U: grade de ventilação, LED de energia e LEDs de atividade."""
        p.setPen(QPen(QColor("#2c3136"), 1))
        for k in range(7):
            x = caixa.left() + 5 + k * 4
            p.drawLine(QLineF(x, caixa.top() + 4, x, caixa.bottom() - 4))
        meio = caixa.center().y()
        self._led(p, caixa.right() - 8, meio, AZUL, True)                       # energia: sempre aceso
        self._led(p, caixa.right() - 16, meio, VERDE, self.leds[i][0])
        self._led(p, caixa.right() - 22, meio, AMBAR, self.leds[i][1])

    def _discos(self, p, caixa, i):
        """Storage: quatro gavetas de disco, cada uma com seu LED."""
        largura = (caixa.width() - 10) / 4
        for k in range(4):
            gaveta = QRectF(caixa.left() + 4 + k * (largura + 0.7), caixa.top() + 3, largura - 1.5, caixa.height() - 6)
            p.setPen(QPen(QColor("#24282c"), 1))
            p.setBrush(QColor("#2f3439"))
            p.drawRoundedRect(gaveta, 1.5, 1.5)
            self._led(p, gaveta.right() - 4, gaveta.bottom() - 4, VERDE, self.leds[i][k % len(self.leds[i])], 1.3)

    def _portas(self, p, caixa, i):
        """Switch: fileira de portas de rede com LED de link piscando."""
        n = 10
        passo = (caixa.width() - 8) / n
        for k in range(n):
            x = caixa.left() + 4 + k * passo
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#16191c"))
            p.drawRect(QRectF(x + 0.5, caixa.top() + 4, passo - 2, caixa.height() - 6))
            self._led(p, x + passo / 2 - 0.5, caixa.top() + 2.6, VERDE, self.leds[i][k % len(self.leds[i])], 1.0)


def _leds_parados():
    """Parado (ele não está trabalhando): LEDs de atividade acesos e quietos, como num rack ocioso."""
    return [[True, False, True, True] for _ in range(4)]


def _leds_trabalhando():
    """Trabalhando: cada LED pisca ao acaso, como tráfego de rede e disco."""
    return [[random.random() < 0.55 for _ in range(4)] for _ in range(4)]
