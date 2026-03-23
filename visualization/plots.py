from tkinter import ttk

from matplotlib import pyplot as plt, ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.models import ExperimentResult, AggregatedStats
from core.stats import aggregate_results
from ui.components import clear_frame


def draw_graphs(frame: ttk.Frame, data: list[ExperimentResult]) -> None:
    """Limpa o container e desenha todos os gráficos a partir dos resultados."""
    if not data:
        return

    clear_frame(frame)
    stats = aggregate_results(data)

    create_combined_chart(frame, stats)
    create_satisfiability_chart(frame, stats)
    create_time_chart(frame, stats)
    create_time_std_chart(frame, stats)


def create_combined_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico combinado de satisfazibilidade e tempo médio."""
    m_values, avg_times, _, avg_sat, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax1 = plt.subplots(figsize=(7, 4))

    ax1.set_xlabel("Número de cláusulas (M)")
    ax1.set_ylabel("Satisfazibilidade (%)", color="blue")
    ax1.plot(m_values, avg_sat, color="blue", label="Satisfazibilidade")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax1.set_xlim(x_left, x_right)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Tempo médio (s)", color="orange")
    ax2.plot(m_values, avg_times, color="orange", label="Tempo")
    ax2.tick_params(axis="y", labelcolor="orange")

    lines = ax1.get_lines() + ax2.get_lines()
    labels = [str(line.get_label()) for line in lines]

    fig.legend(lines, labels, loc="upper center", ncol=2)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.9))

    render_plot(frame, fig)


def create_time_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico apenas de tempo médio."""
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
        marker="o",
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
    """Extrai listas prontas para plotagem a partir das estatísticas agregadas."""
    m_values = [item.M for item in stats]
    avg_times = [item.avg_time for item in stats]
    std_times = [item.std_time for item in stats]
    avg_sat = [item.avg_sat_percent for item in stats]
    std_sat = [item.std_sat_percent for item in stats]
    return m_values, avg_times, std_times, avg_sat, std_sat


def calculate_x_limits(m_values: list[int]) -> tuple[float, float]:
    """Calcula os limites do eixo X com padding."""
    x_min = min(m_values)
    x_max = max(m_values)
    padding_x = (x_max - x_min) * 0.05 if x_max > x_min else 1
    return x_min - padding_x, x_max + padding_x


def render_plot(frame: ttk.Frame, fig: plt.Figure) -> None:
    """Renderiza uma figura matplotlib dentro do frame informado."""
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)


def create_satisfiability_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico apenas de satisfazibilidade média."""
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
        marker="o",
        markersize=3,
        label="Satisfazibilidade",
    )
    ax.tick_params(axis="y", labelcolor="blue")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.set_xlim(x_left, x_right)
    ax.legend()

    fig.tight_layout()
    render_plot(frame, fig)


def create_time_std_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico de tempo médio com desvio padrão."""
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
        fmt="-o",
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
