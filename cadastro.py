from abc import ABC, abstractmethod
from dataclasses import dataclass
import tkinter as tk
from tkinter import messagebox


# =============================
# Modelos e regras de negocio
# =============================

@dataclass(frozen=True)
class Produto:
    nome: str
    preco: float
    icone: str


class Plano(ABC):
    """Define como o valor da sessao sera calculado."""

    @property
    @abstractmethod
    def nome(self) -> str:
        pass

    @abstractmethod
    def aplicar_tarifa(self, valor_base: float) -> float:
        pass


class PlanoNormal(Plano):
    @property
    def nome(self) -> str:
        return "Normal"

    def aplicar_tarifa(self, valor_base: float) -> float:
        return valor_base


class PlanoVIP(Plano):
    @property
    def nome(self) -> str:
        return "VIP (-20%)"

    def aplicar_tarifa(self, valor_base: float) -> float:
        return valor_base * 0.80


class PlanoCorujao(Plano):
    @property
    def nome(self) -> str:
        return "Corujao (-35%)"

    def aplicar_tarifa(self, valor_base: float) -> float:
        return valor_base * 0.65


class Estacao(ABC):
    LIVRE = "LIVRE"
    OCUPADA = "OCUPADA"
    MANUTENCAO = "MANUTENCAO"

    def __init__(self, numero: int):
        self.numero = numero
        self.estado = self.LIVRE
        self.cliente = ""
        self.plano: Plano = PlanoNormal()
        self.segundos_restantes = 0
        self.valor_tempo = 0.0
        self.consumo: list[Produto] = []

    @property
    @abstractmethod
    def tipo(self) -> str:
        pass

    @abstractmethod
    def preco_por_segundo(self) -> float:
        pass

    @abstractmethod
    def acao_bloqueio(self) -> str:
        pass

    def iniciar_sessao(self, cliente: str, segundos: int, plano: Plano) -> None:
        if self.estado != self.LIVRE:
            raise ValueError("Esta estacao nao esta disponivel.")
        if segundos <= 0:
            raise ValueError("Informe um tempo maior que zero.")

        self.estado = self.OCUPADA
        self.cliente = cliente
        self.plano = plano
        self.segundos_restantes = segundos
        self.consumo.clear()

        valor_bruto = segundos * self.preco_por_segundo()
        self.valor_tempo = plano.aplicar_tarifa(valor_bruto)

    def adicionar_lanche(self, produto: Produto) -> None:
        if self.estado != self.OCUPADA:
            raise ValueError("So e possivel lancar consumo em maquinas ocupadas.")
        self.consumo.append(produto)

    def total_consumo(self) -> float:
        return sum(produto.preco for produto in self.consumo)

    def total_geral(self) -> float:
        return self.valor_tempo + self.total_consumo()

    def alternar_manutencao(self) -> None:
        if self.estado == self.OCUPADA:
            raise ValueError("Encerre a sessao antes de colocar em manutencao.")
        self.estado = (
            self.MANUTENCAO
            if self.estado == self.LIVRE
            else self.LIVRE
        )

    def tick(self) -> bool:
        if self.estado != self.OCUPADA or self.segundos_restantes <= 0:
            return False

        self.segundos_restantes -= 1
        return self.segundos_restantes == 0

    def finalizar(self) -> tuple[str, float]:
        nome_cliente = self.cliente
        total = self.total_geral()

        self.estado = self.LIVRE
        self.cliente = ""
        self.plano = PlanoNormal()
        self.segundos_restantes = 0
        self.valor_tempo = 0.0
        self.consumo.clear()

        return nome_cliente, total


class PCBasico(Estacao):
    @property
    def tipo(self) -> str:
        return "PC Basico"

    def preco_por_segundo(self) -> float:
        return 0.50

    def acao_bloqueio(self) -> str:
        return "Monitor desligado e sessao do Windows encerrada!"


class PCGamer(Estacao):
    @property
    def tipo(self) -> str:
        return "PC Gamer RTX"

    def preco_por_segundo(self) -> float:
        return 1.00

    def acao_bloqueio(self) -> str:
        return "Jogo fechado a forca, RGB apagado e tela bloqueada!"


class ConsoleVIP(Estacao):
    @property
    def tipo(self) -> str:
        return "PS5 / VIP"

    def preco_por_segundo(self) -> float:
        return 1.50

    def acao_bloqueio(self) -> str:
        return "Sinal HDMI cortado e controle desconectado!"


class LanHouse:
    def __init__(self):
        self.estacoes: list[Estacao] = [
            PCBasico(1),
            PCBasico(2),
            PCGamer(3),
            PCGamer(4),
            ConsoleVIP(5),
            ConsoleVIP(6),
        ]
        self.cardapio = [
            Produto("Refri", 5.00, "Refri"),
            Produto("Salgado", 7.00, "Salgado"),
            Produto("Energetico", 10.00, "Energetico"),
        ]
        self.caixa = 0.0
        self.gastos_clientes: dict[str, float] = {}

    def registrar_fechamento(self, estacao: Estacao) -> tuple[str, float]:
        cliente, total = estacao.finalizar()
        self.caixa += total
        self.gastos_clientes[cliente] = (
            self.gastos_clientes.get(cliente, 0.0) + total
        )
        return cliente, total

    def top_3_ranking(self) -> list[tuple[str, float]]:
        ranking = sorted(
            self.gastos_clientes.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        return ranking[:3]


# =============================
# Janelas auxiliares
# =============================

class JanelaTelaEstacao(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        titulo: str,
        cabecalho: str,
        mensagem: str,
        cor_fundo: str,
        cor_destaque: str,
    ):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("420x230")
        self.configure(bg=cor_fundo)
        self.attributes("-topmost", True)

        tk.Label(
            self,
            text=cabecalho,
            bg=cor_fundo,
            fg=cor_destaque,
            font=("Consolas", 15, "bold"),
        ).pack(pady=(25, 10))

        tk.Label(
            self,
            text=mensagem,
            bg=cor_fundo,
            fg="white",
            font=("Segoe UI", 11),
            wraplength=370,
        ).pack(pady=10)

        tk.Button(
            self,
            text="FECHAR AVISO",
            bg=cor_destaque,
            fg="#11111b",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=20,
            command=self.destroy,
        ).pack(pady=15)


# =============================
# Interface principal
# =============================

class AppLanHousePro(tk.Tk):
    COR_FUNDO = "#11111b"
    COR_CARD = "#1e1e2e"
    COR_TEXTO = "#cdd6f4"

    def __init__(self):
        super().__init__()
        self.lan = LanHouse()
        self.estacao_selecionada = 0
        self.botoes_estacoes: list[tk.Button] = []

        self.title("CyberArena Pro - Sistema Completo POO")
        self.geometry("980x580")
        self.configure(bg=self.COR_FUNDO)

        self._montar_interface()
        self._atualizar_tudo()
        self._loop_relogio()

    def _montar_interface(self) -> None:
        self._montar_sidebar()
        self._montar_area_principal()

    def _montar_sidebar(self) -> None:
        sidebar = tk.Frame(
            self,
            bg=self.COR_CARD,
            width=290,
            padx=16,
            pady=16,
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="CYBER ARENA",
            bg=self.COR_CARD,
            fg="#cba6f7",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")

        self.lbl_selecionada = tk.Label(
            sidebar,
            text="Selecionada: Maquina #01",
            bg=self.COR_CARD,
            fg="#89b4fa",
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_selecionada.pack(anchor="w", pady=(2, 12))

        self._montar_configuracao_sessao(sidebar)
        self._montar_bomboniere(sidebar)
        self._montar_chat_balcao(sidebar)
        self._montar_acoes_estacao(sidebar)

    def _montar_configuracao_sessao(self, sidebar: tk.Frame) -> None:
        tk.Label(
            sidebar,
            text="Nickname do Jogador:",
            bg=self.COR_CARD,
            fg=self.COR_TEXTO,
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        self.entry_cliente = tk.Entry(
            sidebar,
            bg="#11111b",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 10),
        )
        self.entry_cliente.pack(fill="x", ipady=4, pady=(2, 8))

        frame_config = tk.Frame(sidebar, bg=self.COR_CARD)
        frame_config.pack(fill="x", pady=(0, 8))

        tk.Label(
            frame_config,
            text="Segundos:",
            bg=self.COR_CARD,
            fg=self.COR_TEXTO,
            font=("Segoe UI", 9),
        ).grid(row=0, column=0, sticky="w")

        self.spin_tempo = tk.Spinbox(
            frame_config,
            from_=5,
            to=120,
            increment=5,
            width=6,
            bg="#11111b",
            fg="white",
            relief="flat",
        )
        self.spin_tempo.delete(0, tk.END)
        self.spin_tempo.insert(0, "15")
        self.spin_tempo.grid(row=1, column=0, ipady=3, padx=(0, 10))

        tk.Label(
            frame_config,
            text="Pacote / Plano:",
            bg=self.COR_CARD,
            fg=self.COR_TEXTO,
            font=("Segoe UI", 9),
        ).grid(row=0, column=1, sticky="w")

        self.plano_var = tk.StringVar(value="Normal")
        menu_plano = tk.OptionMenu(
            frame_config,
            self.plano_var,
            "Normal",
            "VIP (-20%)",
            "Corujao (-35%)",
        )
        menu_plano.config(
            bg="#313244",
            fg="white",
            highlightthickness=0,
            relief="flat",
        )
        menu_plano.grid(row=1, column=1, sticky="ew")

        tk.Button(
            sidebar,
            text="INICIAR SESSAO NA SELECIONADA",
            bg="#2e7d32",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            command=self._acao_iniciar,
        ).pack(fill="x", ipady=6, pady=(2, 12))

    def _montar_bomboniere(self, sidebar: tk.Frame) -> None:
        tk.Label(
            sidebar,
            text="BOMBONIERE (Lancar na maquina)",
            bg=self.COR_CARD,
            fg="#f9e2af",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        frame_lanches = tk.Frame(sidebar, bg=self.COR_CARD)
        frame_lanches.pack(fill="x", pady=(4, 12))

        for produto in self.lan.cardapio:
            tk.Button(
                frame_lanches,
                text=f"{produto.icone} {produto.nome}\nR$ {produto.preco:.0f}",
                bg="#313244",
                fg="white",
                font=("Segoe UI", 8, "bold"),
                relief="flat",
                cursor="hand2",
                command=lambda item=produto: self._acao_lanche(item),
            ).pack(side="left", expand=True, fill="x", padx=2, ipady=4)

    def _montar_chat_balcao(self, sidebar: tk.Frame) -> None:
        tk.Label(
            sidebar,
            text="CHAT DO BALCONISTA",
            bg=self.COR_CARD,
            fg="#f38ba8",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        self.entry_bronca = tk.Entry(
            sidebar,
            bg="#11111b",
            fg="white",
            insertbackground="white",
            relief="flat",
            font=("Segoe UI", 9),
        )
        self.entry_bronca.insert(0, "Sem gritar no microfone!")
        self.entry_bronca.pack(fill="x", ipady=4, pady=(3, 5))

        tk.Button(
            sidebar,
            text="MANDAR AVISO NA TELA",
            bg="#d97706",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            command=self._acao_bronca,
        ).pack(fill="x", ipady=5, pady=(0, 12))

    def _montar_acoes_estacao(self, sidebar: tk.Frame) -> None:
        frame_acoes = tk.Frame(sidebar, bg=self.COR_CARD)
        frame_acoes.pack(fill="x")

        tk.Button(
            frame_acoes,
            text="Manutencao",
            bg="#0284c7",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self._acao_manutencao,
        ).pack(side="left", expand=True, fill="x", padx=(0, 3), ipady=5)

        tk.Button(
            frame_acoes,
            text="Desligar PC",
            bg="#dc2626",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            command=self._acao_encerrar_manual,
        ).pack(side="right", expand=True, fill="x", padx=(3, 0), ipady=5)

    def _montar_area_principal(self) -> None:
        direita = tk.Frame(
            self,
            bg=self.COR_FUNDO,
            padx=20,
            pady=16,
        )
        direita.pack(side="right", fill="both", expand=True)

        tk.Label(
            direita,
            text="Clique em uma maquina para seleciona-la no painel ao lado",
            bg=self.COR_FUNDO,
            fg="#a6adc8",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 8))

        mapa = tk.Frame(direita, bg=self.COR_FUNDO)
        mapa.pack(expand=True, fill="both")

        for indice in range(len(self.lan.estacoes)):
            botao = tk.Button(
                mapa,
                width=22,
                height=7,
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
                command=lambda idx=indice: self._selecionar_estacao(idx),
            )
            botao.grid(
                row=indice // 3,
                column=indice % 3,
                padx=8,
                pady=8,
                sticky="nsew",
            )
            mapa.grid_columnconfigure(indice % 3, weight=1)
            mapa.grid_rowconfigure(indice // 3, weight=1)
            self.botoes_estacoes.append(botao)

        rodape = tk.Frame(
            direita,
            bg=self.COR_CARD,
            padx=15,
            pady=12,
        )
        rodape.pack(fill="x", pady=(10, 0))

        self.lbl_ranking = tk.Label(
            rodape,
            text="Top Jogadores: Nenhum registro ainda",
            bg=self.COR_CARD,
            fg="#f9e2af",
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_ranking.pack(side="left")

        self.lbl_caixa = tk.Label(
            rodape,
            text="Caixa: R$ 0.00",
            bg=self.COR_CARD,
            fg="#a6e3a1",
            font=("Segoe UI", 13, "bold"),
        )
        self.lbl_caixa.pack(side="right")

    def _selecionar_estacao(self, indice: int) -> None:
        self.estacao_selecionada = indice
        self._atualizar_tudo()

    def _obter_plano(self) -> Plano:
        escolha = self.plano_var.get()
        if escolha.startswith("VIP"):
            return PlanoVIP()
        if escolha.startswith("Corujao"):
            return PlanoCorujao()
        return PlanoNormal()

    def _acao_iniciar(self) -> None:
        estacao = self.estacao_atual
        cliente = self.entry_cliente.get().strip()
        if not cliente:
            messagebox.showwarning(
                "Atencao",
                "Digite o nickname do jogador!",
            )
            return

        try:
            segundos = int(self.spin_tempo.get())
            estacao.iniciar_sessao(
                cliente,
                segundos,
                self._obter_plano(),
            )
        except (TypeError, ValueError) as erro:
            messagebox.showwarning("Indisponivel", str(erro))
            return

        self.entry_cliente.delete(0, tk.END)
        self._atualizar_tudo()

    def _acao_lanche(self, produto: Produto) -> None:
        try:
            self.estacao_atual.adicionar_lanche(produto)
        except ValueError as erro:
            messagebox.showwarning("Atencao", str(erro))
            return
        self._atualizar_tudo()

    def _acao_bronca(self) -> None:
        estacao = self.estacao_atual
        if estacao.estado != Estacao.OCUPADA:
            messagebox.showinfo(
                "Aviso",
                "Selecione uma maquina ocupada para mandar mensagem.",
            )
            return

        mensagem = (
            self.entry_bronca.get().strip()
            or "Atencao no comportamento!"
        )
        JanelaTelaEstacao(
            self,
            f"Mensagem na Maquina #{estacao.numero:02d}",
            f"AVISO DO BALCAO ({estacao.cliente})",
            mensagem,
            "#2b1d0e",
            "#f59e0b",
        )

    def _acao_manutencao(self) -> None:
        try:
            self.estacao_atual.alternar_manutencao()
        except ValueError as erro:
            messagebox.showwarning("Atencao", str(erro))
            return
        self._atualizar_tudo()

    def _acao_encerrar_manual(self) -> None:
        estacao = self.estacao_atual
        if estacao.estado != Estacao.OCUPADA:
            return

        acao = estacao.acao_bloqueio()
        cliente, total = self.lan.registrar_fechamento(estacao)
        self._atualizar_tudo()

        JanelaTelaEstacao(
            self,
            f"Maquina #{estacao.numero:02d} Desligada",
            "SESSAO ENCERRADA",
            f"Jogador: {cliente}\n"
            f"Total pago: R$ {total:.2f}\n\n"
            f"{acao}",
            "#000000",
            "#ff3b30",
        )

    def _loop_relogio(self) -> None:
        alguma_sessao_atualizada = False

        for estacao in self.lan.estacoes:
            if estacao.estado != Estacao.OCUPADA:
                continue

            alguma_sessao_atualizada = True
            if estacao.tick():
                acao = estacao.acao_bloqueio()
                cliente, total = self.lan.registrar_fechamento(estacao)
                JanelaTelaEstacao(
                    self,
                    f"Maquina #{estacao.numero:02d} - Tempo Esgotado",
                    "TEMPO ESGOTADO",
                    f"Jogador: {cliente}\n"
                    f"Total da conta: R$ {total:.2f}\n\n"
                    f"{acao}",
                    "#000000",
                    "#ff3b30",
                )

        if alguma_sessao_atualizada:
            self._atualizar_tudo()

        self.after(1000, self._loop_relogio)

    def _atualizar_tudo(self) -> None:
        estacao_atual = self.estacao_atual
        self.lbl_selecionada.config(
            text=(
                f"Selecionada: Maquina "
                f"#{estacao_atual.numero:02d} ({estacao_atual.tipo})"
            )
        )

        for indice, estacao in enumerate(self.lan.estacoes):
            botao = self.botoes_estacoes[indice]
            icone = self._icone_estacao(estacao)
            selecionada = indice == self.estacao_selecionada
            borda = 3 if selecionada else 0

            if estacao.estado == Estacao.LIVRE:
                botao.config(
                    text=(
                        f"{icone} MAQUINA #{estacao.numero:02d}\n"
                        f"[{estacao.tipo}]\n\nLIVRE"
                    ),
                    bg="#2e7d32",
                    fg="white",
                    bd=borda,
                    relief="solid" if selecionada else "flat",
                )
            elif estacao.estado == Estacao.MANUTENCAO:
                botao.config(
                    text=(
                        f"{icone} MAQUINA #{estacao.numero:02d}\n"
                        f"[{estacao.tipo}]\n\nMANUTENCAO"
                    ),
                    bg="#0078d7",
                    fg="white",
                    bd=borda,
                    relief="solid" if selecionada else "flat",
                )
            else:
                cor = (
                    "#e65100"
                    if estacao.segundos_restantes <= 5
                    else "#c62828"
                )
                quantidade_lanches = len(estacao.consumo)
                texto_lanche = (
                    f" | Lanches: {quantidade_lanches}"
                    if quantidade_lanches > 0
                    else ""
                )
                botao.config(
                    text=(
                        f"{icone} MAQUINA #{estacao.numero:02d} "
                        f"[{estacao.plano.nome}]\n"
                        f"Jogador: {estacao.cliente}\n"
                        f"Tempo: {estacao.segundos_restantes}s"
                        f"{texto_lanche}\n"
                        f"Conta: R$ {estacao.total_geral():.2f}"
                    ),
                    bg=cor,
                    fg="white",
                    bd=borda,
                    relief="solid" if selecionada else "flat",
                )

        top_3 = self.lan.top_3_ranking()
        if top_3:
            ranking = "  |  ".join(
                f"{posicao}º {nome} (R$ {valor:.2f})"
                for posicao, (nome, valor) in enumerate(top_3, start=1)
            )
            self.lbl_ranking.config(text=f"Top: {ranking}")
        else:
            self.lbl_ranking.config(
                text="Top Jogadores: Nenhum registro ainda"
            )

        self.lbl_caixa.config(text=f"Caixa: R$ {self.lan.caixa:.2f}")

    @property
    def estacao_atual(self) -> Estacao:
        return self.lan.estacoes[self.estacao_selecionada]

    @staticmethod
    def _icone_estacao(estacao: Estacao) -> str:
        if isinstance(estacao, ConsoleVIP):
            return "VIP"
        if isinstance(estacao, PCGamer):
            return "GAMER"
        return "PC"


def main() -> None:
    app = AppLanHousePro()
    app.mainloop()


if __name__ == "__main__":
    main()
