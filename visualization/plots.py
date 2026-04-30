from tkinter import ttk

from matplotlib import pyplot as plt, ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.models import ExperimentResult, AggregatedStats
from core.stats import aggregate_results
from ui.components import clear_frame


def draw_graphs(
        frame: ttk.Frame,
        data: list[ExperimentResult],
        show_markers: bool = True,
) -> None:
    """
    Renderiza todos os gráficos a partir dos resultados do experimento.

    Essa função atua como ponto central da visualização, sendo responsável por:
    - Limpar o container de gráficos anterior
    - Agregar os resultados (média e desvio padrão)
    - Gerar múltiplos gráficos complementares

    Gráficos gerados:
    - Gráfico combinado (tempo + satisfazibilidade)
    - Gráfico de satisfazibilidade
    - Gráfico de tempo médio
    - Gráfico de tempo com desvio padrão

    Parâmetros:
    - frame: container onde os gráficos serão renderizados
    - data: lista de resultados individuais do experimento
    - show_markers: exibe marcadores nos pontos dos gráficos (default: True)

    Observação:
    Caso não haja dados, a função não realiza nenhuma ação.
    """
    if not data:
        return

    clear_frame(frame)
    stats = aggregate_results(data)

    create_combined_chart(frame, stats, show_markers)
    create_satisfiability_chart(frame, stats, show_markers)
    create_time_chart(frame, stats, show_markers)
    create_time_std_chart(frame, stats, show_markers)


def create_combined_chart(
        frame: ttk.Frame,
        stats: list[AggregatedStats],
        show_markers: bool = True,
) -> None:
    """
    Cria um gráfico combinado com dois eixos Y:
    - Satisfazibilidade (%) no eixo esquerdo
    - Tempo médio (s) no eixo direito

    Esse gráfico permite analisar simultaneamente:
    - A transição de fase (queda na satisfazibilidade)
    - O crescimento do custo computacional (tempo)

    Características:
    - Dois eixos Y independentes (twinx)
    - Legenda combinada
    - Formatação percentual no eixo de satisfazibilidade

    Parâmetros:
    - frame: container de renderização
    - stats: estatísticas agregadas por M
    - show_markers: exibe marcadores nos pontos
    """
    marker = "o" if show_markers else None
    m_values, avg_times, _, avg_sat, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax1 = plt.subplots(figsize=(7, 4))

    ax1.set_title("Satisfazibilidade e Tempo de resolução")
    ax1.set_xlabel("Número de cláusulas (M)")
    ax1.set_ylabel("Satisfazibilidade (%)", color="blue")
    ax1.plot(m_values, avg_sat, color="blue", marker=marker, markersize=3, label="Satisfazibilidade")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax1.set_xlim(x_left, x_right)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Tempo médio (s)", color="orange")
    ax2.plot(m_values, avg_times, color="orange", marker=marker, markersize=3, label="Tempo")
    ax2.tick_params(axis="y", labelcolor="orange")

    lines = ax1.get_lines() + ax2.get_lines()
    labels = [str(line.get_label()) for line in lines]

    fig.legend(lines, labels, loc="upper center", ncol=2)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.9))

    render_plot(frame, fig)


def create_time_chart(
        frame: ttk.Frame,
        stats: list[AggregatedStats],
        show_markers: bool = True,
) -> None:
    """
    Cria o gráfico de tempo médio de resolução.

    Esse gráfico evidencia o crescimento do custo computacional
    conforme o número de cláusulas aumenta.

    Características:
    - Linha com marcadores (melhor visualização dos pontos)
    - Eixo Y exclusivo para tempo
    - Limites ajustados automaticamente

    Parâmetros:
    - frame: container de renderização
    - stats: estatísticas agregadas
    - show_markers: exibe marcadores nos pontos
    """
    m_values, avg_times, _, _, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Tempo de resolução")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Tempo médio (s)", color="orange")
    ax.plot(
        m_values,
        avg_times,
        color="orange",
        marker="o" if show_markers else None,
        markersize=3,
        label="Tempo médio",
    )
    ax.tick_params(axis="y", labelcolor="orange")
    ax.set_xlim(x_left, x_right)
    ax.legend()

    fig.tight_layout()
    render_plot(frame, fig)


def extract_plot_series(stats: list[AggregatedStats]) -> tuple[
    list[int], list[float], list[float], list[float], list[float]]:
    """
    Extrai séries numéricas a partir das estatísticas agregadas.

    Essa função transforma objetos estruturados ('AggregatedStats')
    em listas simples, adequadas para uso direto em gráficos.

    Retorna:
    - m_values: valores de M (número de cláusulas)
    - avg_times: tempos médios
    - std_times: desvios padrão do tempo
    - avg_sat: satisfazibilidade média (%)
    - std_sat: desvio padrão da satisfazibilidade (%)

    Observação:
    Essa separação melhora a legibilidade e reutilização do código
    de plotagem.
    """
    m_values = [item.M for item in stats]
    avg_times = [item.avg_time for item in stats]
    std_times = [item.std_time for item in stats]
    avg_sat = [item.avg_sat_percent for item in stats]
    std_sat = [item.std_sat_percent for item in stats]
    return m_values, avg_times, std_times, avg_sat, std_sat


def calculate_x_limits(m_values: list[int]) -> tuple[float, float]:
    """
    Calcula os limites do eixo X com margem (padding).

    Essa função evita que os pontos do gráfico fiquem colados
    nas bordas, melhorando a legibilidade visual.

    Estratégia:
    - Adiciona 5% de margem em cada lado
    - Caso haja apenas um valor, aplica padding fixo

    Parâmetros:
    - m_values: lista de valores de M

    Retorno:
    - (x_min, x_max): limites ajustados do eixo X
    """
    x_min = min(m_values)
    x_max = max(m_values)
    padding_x = (x_max - x_min) * 0.05 if x_max > x_min else 1
    return x_min - padding_x, x_max + padding_x


def render_plot(frame: ttk.Frame, fig: plt.Figure) -> None:
    """
    Renderiza uma figura matplotlib num frame Tkinter.

    Essa função faz a ponte entre matplotlib e a interface gráfica,
    permitindo exibir gráficos dinamicamente na aplicação.

    Fluxo:
    - Cria um canvas Tkinter para a figura
    - Desenha o gráfico
    - Insere no layout com expansão automática

    Parâmetros:
    - frame: container onde o gráfico será inserido
    - fig: figura matplotlib a ser renderizada
    """
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)
    plt.close(fig)


def create_satisfiability_chart(
        frame: ttk.Frame,
        stats: list[AggregatedStats],
        show_markers: bool = True,
) -> None:
    """
    Cria o gráfico de satisfazibilidade média.

    Esse gráfico é fundamental para identificar a transição de fase,
    mostrando a variação da porcentagem de cláusulas satisfeitas
    conforme o aumento de M.

    Características:
    - Eixo Y em percentual
    - Linha com marcadores
    - Escala adaptativa

    Parâmetros:
    - frame: container de renderização
    - stats: estatísticas agregadas
    - show_markers: exibe marcadores nos pontos
    """
    m_values, _, _, avg_sat, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Satisfazibilidade")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Satisfazibilidade (%)", color="blue")
    ax.plot(
        m_values,
        avg_sat,
        color="blue",
        marker="o" if show_markers else None,
        markersize=3,
        label="Satisfazibilidade",
    )
    ax.tick_params(axis="y", labelcolor="blue")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.set_xlim(x_left, x_right)
    ax.legend()

    fig.tight_layout()
    render_plot(frame, fig)


def create_time_std_chart(
        frame: ttk.Frame,
        stats: list[AggregatedStats],
        show_markers: bool = True,
) -> None:
    """
    Cria o gráfico de tempo médio com desvio padrão.

    Esse gráfico permite analisar não apenas o tempo médio,
    mas também a variabilidade entre as execuções.

    Interpretação:
    - Barras de erro maiores indicam maior instabilidade
    - Regiões próximas à transição de fase tendem a apresentar maior variância

    Características:
    - Uso de error bars (matplotlib.errorbar)
    - Exibição de média ± desvio padrão
    - Destaque visual das incertezas

    Parâmetros:
    - frame: container de renderização
    - stats: estatísticas agregadas
    - show_markers: exibe marcadores nos pontos
    """
    m_values, avg_times, std_times, _, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Tempo médio com desvio padrão")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Tempo médio (s)", color="orange")
    ax.errorbar(
        m_values,
        avg_times,
        yerr=std_times,
        fmt="-o" if show_markers else "-",
        markersize=3,
        color="orange",
        ecolor="gray",
        elinewidth=1,
        capsize=3,
        label="Tempo médio ± desvio padrão",
    )
    ax.tick_params(axis="y", labelcolor="orange")
    ax.set_xlim(x_left, x_right)
    ax.legend()

    fig.tight_layout()
    render_plot(frame, fig)
