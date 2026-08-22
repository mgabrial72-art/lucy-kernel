"""
Web Search Service — Busca na web via SearXNG local.
Retorna resultados formatados para o prompt da Lucy.
"""
import requests
from typing import List, Dict, Optional

SEARXNG_URL = "http://127.0.0.1:8080"

def search_web(query: str, max_results: int = 3, language: str = "pt-BR") -> Optional[Dict]:
    """
    Busca na web via SearXNG.
    
    Returns:
        Dict com resultados ou None se falhar
    """
    try:
        r = requests.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": query,
                "format": "json",
                "language": language,
                "categories": "general"
            },
            timeout=15,
            headers={"User-Agent": "LucyKernel/1.0"}
        )
        r.raise_for_status()
        data = r.json()
        
        results = data.get("results", [])[:max_results]
        
        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", ""),
                "snippet": r.get("content", r.get("body", ""))[:200],
                "url": r.get("url", "")
            })
        
        return {
            "success": True,
            "query": query,
            "results": formatted,
            "count": len(formatted)
        }
        
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "error": str(e)
        }

def format_for_prompt(search_result: Dict) -> str:
    """Formata resultados de busca para incluir no prompt."""
    if not search_result.get("success"):
        return ""
    
    results = search_result.get("results", [])
    if not results:
        return ""
    
    lines = [f"[BUSCA WEB: {search_result['query']}]"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}: {r['snippet']}")
    
    return "\n".join(lines)
