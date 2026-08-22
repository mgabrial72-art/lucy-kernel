import json
from datetime import datetime
from threading import Lock
from pathlib import Path
import sys


def get_base_dir() -> Path:
    # CORREÇÃO: Retorna o diretório do próprio arquivo (services/mark_l)
    # Isso faz MEMORY_PATH apontar para services/mark_l/memory/long_term.json
    return Path(__file__).resolve().parent


BASE_DIR         = get_base_dir()
MEMORY_PATH      = BASE_DIR / "memory" / "long_term.json"
_lock            = Lock()
MAX_VALUE_LENGTH = 380
MEMORY_MAX_CHARS = 2200

def _empty_memory() -> dict:
    return {
        "identity":      {},
        "preferences":   {},
        "projects":      {},
        "relationships": {},
        "wishes":        {},
        "notes":         {},
    }

def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for key in base:
                    if key not in data:
                        data[key] = {}
                return data
            return _empty_memory()
        except Exception as e:
            print(f"[Memory] ⚠️ Load error: {e}")
            return _empty_memory()

def _all_entries(memory: dict) -> list[tuple]:
    entries = []
    for cat, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            if isinstance(entry, dict) and "value" in entry:
                entries.append((cat, key, entry))
    return entries


def _trim_to_limit(memory: dict) -> dict:
    if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
        return memory
    entries = _all_entries(memory)
    entries.sort(key=lambda t: t[2].get("updated", "0000-00-00"))
    for cat, key, _ in entries:
        if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
            break
        del memory[cat][key]
        print(f"[Memory] 🗑️  Trimmed {cat}/{key}")
    return memory

def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    memory = _trim_to_limit(memory)
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _truncate_value(val: str) -> str:
    if isinstance(val, str) and len(val) > MAX_VALUE_LENGTH:
        return val[:MAX_VALUE_LENGTH].rstrip() + "…"
    return val


def _recursive_update(target: dict, updates: dict) -> bool:
    changed = False
    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, dict) and "value" not in value:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
                changed = True
            if _recursive_update(target[key], value):
                changed = True
        else:
            new_val  = _truncate_value(str(value["value"] if isinstance(value, dict) else value))
            entry    = {"value": new_val, "updated": datetime.now().strftime("%Y-%m-%d")}
            existing = target.get(key, {})
            if not isinstance(existing, dict) or existing.get("value") != new_val:
                target[key] = entry
                changed = True
    return changed


def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()
    memory = load_memory()
    if _recursive_update(memory, memory_update):
        save_memory(memory)
        print(f"[Memory] 💾 Saved: {list(memory_update.keys())}")
    return memory

def format_memory_for_prompt(memory: dict | None) -> str:
    """Formata memória COMPACTA para o prompt (máx ~900 chars)."""
    if not memory:
        return ""

    def val(entry):
        if isinstance(entry, dict):
            return str(entry.get("value", ""))
        return str(entry)

    parts = []

    # Identidade (curta)
    ident = memory.get("identity", {})
    if ident:
        name = val(ident.get("name", ""))
        if name:
            parts.append(f"CAPITÃO: {name}.")

    # Família (o mais importante)
    rels = memory.get("relationships", {})
    if rels:
        fam = []
        for name, entry in list(rels.items())[:6]:
            desc = val(entry)
            if len(desc) > 90:
                desc = desc[:87] + "..."
            fam.append(f"{name}: {desc}")
        if fam:
            parts.append("FAMÍLIA: " + " | ".join(fam))

    # Projetos ativos (top 3)
    projs = memory.get("projects", {})
    if projs:
        act = [p for p, e in list(projs.items())[:5] if "ativo" in val(e).lower()]
        if act:
            parts.append("PROJETOS: " + ", ".join(act[:3]))

    # Preferências (top 3, curtas)
    prefs = memory.get("preferences", {})
    if prefs:
        pl = [f"{k}: {val(v)[:40]}" for k, v in list(prefs.items())[:3]]
        parts.append("PREFS: " + "; ".join(pl))

    result = "\n".join(parts)
    if len(result) > 900:
        result = result[:897] + "..."
    return result

# ── Session memory ─────────────────────────────────────────────────────────────

_SESSION_MAX = 3   # safety cap — in practice 0-1 entries after pop


