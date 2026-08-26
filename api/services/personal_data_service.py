"""
Carrega dados pessoais dos arquivos Markdown em personal/facts/
"""
from pathlib import Path

PERSONAL_DIR = Path(__file__).parent.parent.parent / "personal" / "facts"

def load_personal_facts() -> str:
    """Lê todos os .md da pasta personal/facts/ e retorna como texto único."""
    if not PERSONAL_DIR.exists():
        return ""
    
    parts = []
    for md_file in sorted(PERSONAL_DIR.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8").strip()
            if content:
                parts.append(content)
        except Exception:
            continue
    
    if not parts:
        return ""
    
    return "\n\n".join(parts)
