"""CLI: python3 run.py <command> ...

Commands: index, search, ask, summarise, organise, demo.
Default provider is auto (Otari if credentials exist, else mock).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import NotesAgent
from .config import config_from_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="notevault", description="Local-first notes agent via Otari")
    parser.add_argument("--notes", default=None, help="Notes folder (default: notes/ or $NOTES_ROOT)")
    parser.add_argument("--provider", default=None, choices=["auto", "mock", "otari"])
    parser.add_argument("--model", default=None, help="Otari model, e.g. openai:gpt-4o-mini")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index", help="List indexed notes")
    p_search = sub.add_parser("search", help="Keyword search over notes")
    p_search.add_argument("query")
    p_ask = sub.add_parser("ask", help="Answer a question from your notes")
    p_ask.add_argument("question")
    p_sum = sub.add_parser("summarise", help="Summarise one note")
    p_sum.add_argument("note")
    p_org = sub.add_parser("organise", help="Print (and optionally write) a grouping plan")
    p_org.add_argument("--write", default=None, help="Write plan to this file (inside output/ recommended)")
    sub.add_parser("demo", help="Run a scripted demo over the sample notes")
    sub.add_parser("status", help="Show routing (gateway/model/fallback) + budget, no LLM call")
    p_serve = sub.add_parser("serve", help="Start the web UI (localhost only by default)")
    p_serve.add_argument("--host", default="127.0.0.1", help="Bind host (default 127.0.0.1; do not use 0.0.0.0 casually)")
    p_serve.add_argument("--port", type=int, default=8767)
    return parser


def _make_agent(args: argparse.Namespace) -> NotesAgent:
    config = config_from_env(Path(args.notes) if args.notes else None)
    if args.provider:
        config.provider = args.provider
    if args.model:
        config.model = args.model
    return NotesAgent(config)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        agent = _make_agent(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.command == "index":
        if not agent.notes:
            print("No notes found. Add .md/.txt files to the notes folder.")
            return 0
        for note in agent.notes:
            tags = ", ".join(f"#{t}" for t in note.tags) or "(no tags)"
            print(f"- {note.rel_path} — {note.title} [{tags}] ({note.word_count} words)")
        return 0

    if args.command == "search":
        hits = agent.search(args.query)
        if not hits:
            print("No matches.")
            return 0
        for note in hits:
            print(f"- {note.rel_path} — {note.title}")
        return 0

    if args.command == "ask":
        print(agent.ask(args.question))
        return 0

    if args.command == "summarise":
        try:
            print(agent.summarise(args.note))
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        return 0

    if args.command == "organise":
        plan = agent.organise_plan()
        print(plan)
        if args.write:
            Path(args.write).write_text(plan, encoding="utf-8")
            print(f"Plan written to {args.write} (no notes were moved or edited).")
        return 0

    if args.command == "status":
        status = agent.status_dict()
        print(f"Mode: {status['mode']} ({status['mode_label']})")
        print(f"Gateway: {status['gateway']}")
        print(f"Model: {status['model']}")
        print(f"Fallback model: {status['fallback_model'] or 'none configured'}")
        b = status["budget"]
        print(f"Budget: {b['used']} / {b['limit']} calls used, {b['remaining']} remaining")
        print("Gateway budget: see otari.ai dashboard (not visible from this app)")
        print(f"Notes indexed: {status['notes_count']}")
        return 0

    if args.command == "serve":
        from .web import serve

        return serve(agent, host=args.host, port=args.port)

    if args.command == "demo":
        print("== index ==")
        for note in agent.notes:
            print(f"- {note.rel_path} — {note.title}")
        print("\n== search: abhiverse ==")
        for note in agent.search("abhiverse"):
            print(f"- {note.rel_path} — {note.title}")
        print("\n== ask: What is Abhiverse for? ==")
        result = agent.ask_detailed("What is Abhiverse for?")
        print(result.answer)
        print(f"[routing] gateway={result.routing['gateway']} mode={result.mode} "
              f"chosen={result.routing['chosen']} fallback_used={result.routing['fallback_used']}")
        print(f"[budget] {result.budget['used']}/{result.budget['limit']} used, "
              f"{result.budget['remaining']} remaining (local session budget only)")
        print("\n== ask (refusal): quantum bananas ==")
        refused = agent.ask_detailed("quantum bananas")
        print(refused.answer)
        print(f"[routing] refused_before_routing={refused.routing['refused_before_routing']} "
              f"budget still {refused.budget['used']}/{refused.budget['limit']}")
        print("\n== organise (plan only) ==")
        print(agent.organise_plan())
        return 0

    return 2
