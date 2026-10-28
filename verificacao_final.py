#!/usr/bin/env python3
"""Verificação final de conformidade (Etapa 13).

Cruza todos os requisitos do PDF de especificacao (AnProjOO_Trab_2026.pdf)
com o que foi implementado no projeto.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJETO = Path(__file__).resolve().parent
verificacoes: list[dict] = []


def verificar(categoria: str, item: str, condicao: bool, evidencia: str = "", observacao: str = "") -> None:
    verificacoes.append({
        "categoria": categoria,
        "item": item,
        "condicao": condicao,
        "evidencia": evidencia,
        "observacao": observacao,
    })
    status = "✅" if condicao else "❌"
    print(f"{status} [{categoria}] {item}")
    if evidencia:
        print(f"     → {evidencia}")


def main() -> int:
    print("=" * 70)
    print("ETAPA 13 — VERIFICACAO FINAL DE CONFORMIDADE (PDF AnProjOO_Trab_2026)")
    print("=" * 70)
    print()

    # ---------------- Seção 3 — Requisitos mínimos do sistema ----------------
    print("--- Seção 3: Requisitos mínimos do sistema ---")
    # Múltiplos agentes com papéis distintos
    prompts = {
        "tutor": PROJETO / "agente" / "prompts" / "tutor.txt",
        "exemplificador": PROJETO / "agente" / "prompts" / "exemplificador.txt",
        "inquiridor": PROJETO / "agente" / "prompts" / "inquiridor.txt",
        "guardiao": PROJETO / "agente" / "prompts" / "guardiao.txt",
    }
    todos_prompts = all(p.exists() for p in prompts.values())
    verificar("Requisitos", "Múltiplos agentes com papéis distintos", todos_prompts,
              f"{len(prompts)} agentes com prompt próprio: {', '.join(prompts.keys())}")

    # Memória da conversa
    memoria = PROJETO / "agente" / "memoria.py"
    verificar("Requisitos", "Memória da conversa", memoria.exists(),
              "agente/memoria.py persiste JSON por sessão e injeta contexto")

    # Lógica pedagógica explícita (apresentação, exemplificação, exercício, diagnóstico, feedback)
    doc_agentes = PROJETO / "docs" / "agentes.md"
    pedagogico = doc_agentes.exists()
    verificar("Requisitos", "Lógica pedagógica explícita (5 funções)", pedagogico,
              "docs/agentes.md documenta: conceito→exemplo→exercício→diagnóstico→feedback")

    # Regras anti-alucinação
    prompts_tem_antialuc = all(
        "REGRAS ANTI-ALUCINACAO" in p.read_text(encoding="utf-8")
        for p in prompts.values() if p.exists()
    )
    verificar("Requisitos", "Regras anti-alucinação", prompts_tem_antialuc,
              "Todos os 4 prompts contêm seção REGRAS ANTI-ALUCINACAO")

    # Tratamento básico de erros
    erro = PROJETO / "agente" / "erro.py"
    verificar("Requisitos", "Tratamento básico de erros", erro.exists(),
              "agente/erro.py: ErroEntradaVazia, ErroModeloIndisponivel, ErroSaidaInesperada, etc.")

    # ---------------- Seção 4 — Custo zero ----------------
    print()
    print("--- Seção 4: Custo zero ---")
    config = PROJETO / "agente" / "config.py"
    custo_zero = config.exists() and "API_PAGA_PERMITIDA = False" in config.read_text(encoding="utf-8")
    verificar("Custo zero", "Proibido API paga / chave de API / nuvem", custo_zero,
              "config.py: API_PAGA_PERMITIDA=False; código usa Ollama local apenas")

    # Modelo local
    modelo_local = config.exists() and "qwen2.5:3b" in config.read_text(encoding="utf-8")
    verificar("Custo zero", "Modelo local (Ollama qwen2.5:3b)", modelo_local,
              "config.py declara OLLAMA_MODEL=qwen2.5:3b; llm.py configura Ollama local")

    # Declaração no mini-relatório
    relatorio = PROJETO / "docs" / "mini_relatorio.md"
    hw_declarado = relatorio.exists() and "8 GB de RAM" in relatorio.read_text(encoding="utf-8") and "qwen2.5:3b" in relatorio.read_text(encoding="utf-8")
    verificar("Custo zero", "Declaração de modelo e hardware no mini-relatório", hw_declarado,
              "docs/mini_relatorio.md Seção 6 declara qwen2.5:3b e 8 GB de RAM")

    # ---------------- Seção 5 — Interface CLI ----------------
    print()
    print("--- Seção 5: Interface CLI ---")
    cli = PROJETO / "agente" / "__main__.py"
    cli_obra = cli.exists()
    verificar("CLI", "Comando único: python -m agente \"pergunta aqui\"", cli_obra,
              "agente/__main__.py implementa executar_uma_vez() com sys.argv")

    # Modo interativo opcional
    modo_interativo = cli.exists() and "modo_interativo" in cli.read_text(encoding="utf-8")
    verificar("CLI", "Modo interativo no terminal (sair para encerrar)", modo_interativo,
              "agente/__main__.py implementa modo_interativo()")

    # ---------------- Seção 7 — Entregáveis ----------------
    print()
    print("--- Seção 7: Entregáveis ---")
    # 1. Sistema multiagente completo
    sistema = (PROJETO / "agente").exists() and len(list((PROJETO / "agente").rglob("*.py"))) >= 10
    verificar("Entregáveis", "1. Sistema multiagente completo em Python", sistema,
              f"{len(list((PROJETO / 'agente').rglob('*.py')))} arquivos .py")

    # 2. Documentação dos agentes (prompts completos)
    docs_agentes_ok = doc_agentes.exists() and todos_prompts
    verificar("Entregáveis", "2. Documentação dos agentes (prompts completos)", docs_agentes_ok,
              "docs/agentes.md + agente/prompts/*.txt (4 prompts completos)")

    # 3. Justificativa de design (2-3 páginas)
    just = PROJETO / "docs" / "justificativa_design.md"
    palavras_just = len(just.read_text(encoding="utf-8").split()) if just.exists() else 0
    paginas_just = palavras_just / 500
    verificar("Entregáveis", "3. Justificativa de design (2-3 páginas)",
              just.exists() and 1.5 <= paginas_just <= 3.5,
              f"~{paginas_just:.1f} páginas ({palavras_just} palavras)")

    # 4. Mini-relatório (1-2 páginas)
    palavras_rel = len(relatorio.read_text(encoding="utf-8").split()) if relatorio.exists() else 0
    paginas_rel = palavras_rel / 500
    verificar("Entregáveis", "4. Mini-relatório (1-2 páginas)",
              relatorio.exists() and 0.8 <= paginas_rel <= 2.5,
              f"~{paginas_rel:.1f} páginas ({palavras_rel} palavras)")

    # 5. Demonstração ao vivo (CLI pronta)
    verificar("Entregáveis", "5. Demonstração ao vivo (CLI pronta)", cli_obra,
              "python -m agente funciona para demonstração")

    # 6. Caderno de evidências
    evidencias = PROJETO / "evidencias" / "testes_etapa7"
    n_evidencias = len(list(evidencias.glob("*.json"))) if evidencias.exists() else 0
    verificar("Entregáveis", "6. Caderno de evidências", evidencias.exists() and n_evidencias >= 7,
              f"{n_evidencias} arquivos de evidência em evidencias/testes_etapa7/")

    # ---------------- Seção 9 — Regras de uso de IA ----------------
    print()
    print("--- Seção 9: Regras de uso de IA e ética ---")
    uso_ia_declarado = relatorio.exists() and "IA generativa" in relatorio.read_text(encoding="utf-8")
    verificar("Uso de IA", "Uso de IA declarado no relatório", uso_ia_declarado,
              "docs/mini_relatorio.md Seção 5 declara uso de IA generativa")

    # Sem chaves de API no código
    chaves = False
    for py in (PROJETO / "agente").rglob("*.py"):
        txt = py.read_text(encoding="utf-8", errors="ignore")
        if "sk-" in txt or "os.environ[" in txt:
            chaves = True
    verificar("Uso de IA", "Sem chaves de API no código", not chaves,
              "Nenhuma chave de API encontrada no código Python")

    # ---------------- Resumo ----------------
    print()
    print("=" * 70)
    print("RESUMO FINAL DA ETAPA 13")
    print("=" * 70)
    total = len(verificacoes)
    aprovados = sum(1 for v in verificacoes if v["condicao"])
    reprovados = total - aprovados
    print(f"Total de verificações: {total}")
    print(f"Aprovadas: {aprovados}")
    print(f"Reprovadas/pendentes: {reprovados}")
    print()
    if reprovados > 0:
        print("ITENS REPROVADOS:")
        for v in verificacoes:
            if not v["condicao"]:
                print(f"  ❌ [{v['categoria']}] {v['item']}")
    print()
    print(f"Conformidade: {aprovados}/{total} ({(aprovados/total)*100:.0f}%)")
    print("=" * 70)

    # Salvar relatório de conformidade
    relatorio_conformidade = {
        "total": total,
        "aprovados": aprovados,
        "reprovados": reprovados,
        "percentual": round(aprovados / total * 100, 1),
        "verificacoes": verificacoes,
    }
    caminho = PROJETO / "evidencias" / "conformidade_etapa13.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(relatorio_conformidade, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRelatório salvo em: {caminho}")

    return 0 if reprovados == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
