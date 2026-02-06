from datetime import datetime, timedelta

TOOL_DESC = "Calcula uma data e hora futura com base em dias e horas adicionais a partir de agora."

def run(input_str):
    # Espera algo como "days=3, hours=12"
    try:
        params = dict(item.split("=") for item in input_str.split(","))
        days = int(params.get("days", 0))
        hours = int(params.get("hours", 0))
        
        future_date = datetime.now() + timedelta(days=days, hours=hours)
        return future_date.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return f"Erro no cálculo: {str(e)}"
