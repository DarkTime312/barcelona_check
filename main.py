import requests
from datetime import datetime
from zoneinfo import ZoneInfo

IRAN_TZ = ZoneInfo('Asia/Tehran')
dt_no = datetime.now(IRAN_TZ)
msg = f"Hello -> {dt_no.strftime("%H:%M")}"
response = requests.post("https://ntfy.sh/nattagh",
                         data=msg.encode(encoding='utf-8'))

response.raise_for_status()
