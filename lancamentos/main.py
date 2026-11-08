"""Orquestração: entrada -> configuração -> solicitação -> LLM -> resposta -> saída."""

import argparse
import logging
import sys
from typing import Callable, Optional

from .apresentacao import formatar_resultado
from .cliente_llm import chamar_llm
from .config import Configuracao, carregar_configuracao
from .entrada import capturar_entrada_terminal, ler_arquivo, validar_entrada
from .erros import ErroAplicacao
from .logs import configurar_logs
from .prompt import preparar_solicitacao
from .resposta import interpretar_resposta

log = logging.getLogger("lancamentos")


def executar(
    texto: str,
    config: Configuracao,
    chamar: Callable[[dict, Configuracao], str] = chamar_llm,
) -> str:
    """Fluxo principal depois que entrada e configuração já são válidas."""
    solicitacao = preparar_solicitacao(texto, config)
    texto_resposta = chamar(solicitacao, config)
    resultado = interpretar_resposta(texto_resposta)
    log.info(
        "execucao_ok entrada_chars=%s lancamentos=%s alertas=%s",
        len(texto),
        len(resultado.lancamentos),
        len(resultado.alertas),
    )
    return formatar_resultado(resultado)


def _argumentos(argv):
    parser = argparse.ArgumentParser(
        prog="python -m lancamentos",
        description="Gera sugestões de lançamentos contábeis (regime de competência) com apoio de LLM.",
    )
    origem = parser.add_mutually_exclusive_group()
    origem.add_argument("--arquivo", help="arquivo .txt (UTF-8) com a descrição do fato operacional")
    origem.add_argument("--texto", help="descrição do fato operacional (entre aspas)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _argumentos(argv)
    try:
        if args.arquivo:
            bruto = ler_arquivo(args.arquivo)
        elif args.texto is not None:
            bruto = args.texto
        else:
            bruto = capturar_entrada_terminal()
        texto = validar_entrada(bruto)  # antes de qualquer configuração ou chamada

        config = carregar_configuracao()
        configurar_logs(config)
        print(executar(texto, config, chamar_llm))
        return 0
    except ErroAplicacao as erro:
        log.warning("execucao_falhou tipo=%s", type(erro).__name__)
        print(f"Erro: {erro}", file=sys.stderr)
        return erro.codigo_saida
    except KeyboardInterrupt:
        print("\nExecução cancelada pelo usuário.", file=sys.stderr)
        return 130
    except Exception as exc:  # rede de segurança: nunca mostrar traceback com dados
        log.error("erro_inesperado tipo=%s", type(exc).__name__)
        print(
            f"Erro inesperado ({type(exc).__name__}). Consulte logs/execucao.log.",
            file=sys.stderr,
        )
        return ErroAplicacao.codigo_saida
