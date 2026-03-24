from ui import gui_runner

if __name__ == "__main__":
    """
    Ponto de entrada da aplicação.

    Esse bloco garante que a interface gráfica seja inicializada apenas
    quando o script for executado diretamente, evitando execução automática
    em casos de importação como módulo.

    Fluxo:
    - Cria a instância principal da aplicação Tkinter via `gui_runner`
    - Inicia o loop principal (`mainloop`), responsável por:
        - Gerenciar eventos da interface
        - Atualizar componentes visuais
        - Manter a aplicação ativa até o encerramento

    Observação:
    O `mainloop` é essencial no Tkinter, pois mantém a aplicação em execução
    contínua, respondendo às interações do usuário.
    """

    app = gui_runner()
    app.mainloop()
