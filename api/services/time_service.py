"""
Serviço de hora com fuso horário de São Paulo
"""
from datetime import datetime
import pytz

def get_sao_paulo_time() -> dict:
    """Retorna hora atual de São Paulo."""
    sp_tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(sp_tz)
    
    return {
        "datetime": now,
        "time": now.strftime("%H:%M"),
        "date": now.strftime("%d/%m/%Y"),
        "day_of_week": now.strftime("%A"),
        "full": now.strftime("%H:%M de %d/%m/%Y (%A)"),
        "iso": now.isoformat()
    }

def get_time_summary() -> str:
    """Retorna hora em texto."""
    time_data = get_sao_paulo_time()
    
    # Traduz dia da semana
    days_pt = {
        "Monday": "segunda-feira",
        "Tuesday": "terça-feira",
        "Wednesday": "quarta-feira",
        "Thursday": "quinta-feira",
        "Friday": "sexta-feira",
        "Saturday": "sábado",
        "Sunday": "domingo"
    }
    
    day_pt = days_pt.get(time_data["day_of_week"], time_data["day_of_week"])
    
    return f"São {time_data['time']} de {day_pt}, {time_data['date']} em São Paulo."

if __name__ == "__main__":
    print("Testando hora:")
    print(get_time_summary())
