COLOR_MAP = {
    "WHITE": 0,
    "RED": 1,
    "GREEN": 2,
    "BLUE": 3,
    "YELLOW": 4,
    "CYAN": 5,
    "PURPLE": 6,
}


def color_to_int(name: str) -> int:
    return COLOR_MAP.get(name, 0)
