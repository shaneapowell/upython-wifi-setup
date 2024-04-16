
STA_IF = 1
AP_IF = 2

STAT_CONNECTING = 100
STAT_GOT_IP = 101
STAT_WRONG_PASSWORD = 102
STAT_NO_AP_FOUND = 103

AUTH_OPEN=200

def WLAN(ifaceid: int): ...

def hostname(name: str): ...