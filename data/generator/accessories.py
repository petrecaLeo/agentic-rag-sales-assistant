import random

from data.generator.common import draw_price, draw_stock

CHARGER_PRICES = {20: (59, 89), 30: (79, 119), 45: (129, 179), 65: (179, 249), 100: (249, 349), 140: (349, 449)}
CABLE_POWER = {"USB-C para USB-C": "100 W", "USB-C para Lightning": "27 W", "USB-A para USB-C": "15 W"}
CASE_PHONES = [
    "Aurora X", "Aurora X Pro", "Aurora Neo", "Nimbus 7", "Nimbus 8", "Nimbus Ultra",
    "Kora A5", "Kora Flip", "Vetta Mini", "Vetta Pro", "Orbi Note", "Orbi Edge",
]
CASE_MATERIALS = [
    ("de silicone", "silicone macio", "protege contra riscos"),
    ("antiimpacto", "policarbonato transparente", "quinas reforçadas, aguenta quedas de até 2 m"),
    ("carteira", "couro sintético com porta-cartões", "tampa que protege a tela"),
]
KEYBOARDS = [
    ("K1", "mecânico com fio", "RGB", "switch azul, com clique marcado"),
    ("K1 Silent", "mecânico com fio", "branca", "switch vermelho, silencioso"),
    ("K2 Air", "mecânico sem fio", "RGB", "switch marrom, bateria de 40 h"),
    ("Slim", "membrana sem fio", "sem iluminação", "teclas baixas e silenciosas"),
    ("Mini 60", "mecânico compacto 60%", "RGB", "ocupa pouco espaço na mesa"),
    ("Ergo", "membrana ergonômico dividido", "sem iluminação", "apoio de pulso acolchoado"),
    ("Office", "membrana com fio", "sem iluminação", "teclado numérico completo"),
    ("Duo", "membrana sem fio", "sem iluminação", "alterna entre 3 aparelhos com um botão"),
    ("TKL Pro", "mecânico sem teclado numérico", "RGB", "switch vermelho, cabo removível"),
    ("Travel", "dobrável sem fio", "sem iluminação", "dobra ao meio e cabe na mochila"),
]
MICE = [
    ("Tecla", "M1", "sem fio", "1.600 DPI", "cliques silenciosos", (49, 89)),
    ("Tecla", "M2 Ergo", "sem fio, vertical", "2.400 DPI", "formato vertical que alivia o punho", (129, 199)),
    ("Tecla", "Travel", "sem fio, compacto", "1.200 DPI", "pequeno, para levar na mochila", (59, 99)),
    ("Tecla", "Office", "com fio", "1.000 DPI", "simples e durável", (29, 49)),
    ("Tecla", "Duo", "sem fio, Bluetooth", "2.400 DPI", "alterna entre 2 aparelhos", (99, 149)),
    ("Tecla", "Pad", "sem fio, com mousepad", "1.600 DPI", "kit com mousepad de tecido", (79, 129)),
    ("Arena", "Strike", "gamer com fio", "16.000 DPI", "8 botões programáveis", (149, 249)),
    ("Arena", "Strike Air", "gamer sem fio", "26.000 DPI", "ultraleve, 59 g", (299, 449)),
    ("Arena", "Raio", "gamer com fio", "12.000 DPI", "iluminação RGB", (129, 199)),
    ("Arena", "MMO", "gamer com fio", "16.000 DPI", "12 botões laterais", (199, 299)),
    ("Arena", "Lite", "gamer com fio", "6.400 DPI", "bom para começar", (69, 119)),
    ("Arena", "Pro Air", "gamer sem fio", "30.000 DPI", "base de carregamento sem fio", (399, 599)),
]
WATCH_BRANDS = ["Aurora Watch", "Kora Watch", "Pulse Fit"]
WATCH_MODELS = {
    "Lite": ((249, 399), 10, False, "IP68 (chuva e respingos)", False),
    "2": ((499, 799), 7, False, "5 ATM, pode nadar", True),
    "Sport": ((799, 1299), 14, True, "5 ATM, pode nadar", False),
    "Pro": ((1499, 2499), 4, True, "5 ATM, pode nadar", True),
}


def item(rng: random.Random, name: str, brand: str, price_range: tuple[float, float], attributes: dict) -> dict:
    return {
        "nome": name,
        "categoria": "acessorios",
        "marca": brand,
        "preco": draw_price(rng, *price_range),
        "estoque": draw_stock(rng),
        "atributos": attributes,
    }


def draw_chargers(rng: random.Random) -> list[dict]:
    chargers = []
    for brand in ["Volt", "Kora"]:
        for watts, price_range in CHARGER_PRICES.items():
            ports = "1 USB-C" if watts <= 30 else "2 USB-C" if watts <= 65 else "2 USB-C e 1 USB-A"
            chargers.append(item(rng, f"Carregador {brand} {watts}W", brand, price_range, {
                "tipo": "carregador de tomada",
                "potência": f"{watts} W",
                "portas": ports,
                "tecnologia": "GaN, menor e mais frio" if watts >= 45 else "convencional",
                "serve para": "celulares, fones e relógios" if watts <= 30 else "celulares, tablets e notebooks com USB-C",
            }))
    return chargers


def draw_cables(rng: random.Random) -> list[dict]:
    cables = []
    for brand, material, extra in [("Volt", "PVC reforçado", 0), ("Trama", "nylon trançado", 15)]:
        for connectors, power in CABLE_POWER.items():
            for length, step in [("1 m", 0), ("2 m", 20)]:
                low = 29 + step + extra
                cables.append(item(rng, f"Cabo {brand} {connectors} {length}", brand, (low, low + 30), {
                    "tipo": "cabo",
                    "conectores": connectors,
                    "comprimento": length,
                    "material": material,
                    "potência máxima": power,
                }))
    return cables


def draw_cases(rng: random.Random) -> list[dict]:
    cases = []
    for index, phone in enumerate(CASE_PHONES):
        label, material, protection = CASE_MATERIALS[index % len(CASE_MATERIALS)]
        cases.append(item(rng, f"Capa {label} para {phone}", "Trama", (49, 129), {
            "tipo": "capa de celular",
            "compatível com": f"{phone} (todas as versões de armazenamento)",
            "material": material,
            "proteção": protection,
        }))
    return cases


def draw_keyboards(rng: random.Random) -> list[dict]:
    keyboards = []
    for model, kind, lighting, highlight in KEYBOARDS:
        price_range = (199, 499) if "mecânico" in kind else (99, 249)
        keyboards.append(item(rng, f"Teclado Tecla {model}", "Tecla", price_range, {
            "tipo": "teclado",
            "modelo": kind,
            "layout": "ABNT2, com ç",
            "iluminação": lighting,
            "destaque": highlight,
        }))
    return keyboards


def draw_mice(rng: random.Random) -> list[dict]:
    return [
        item(rng, f"Mouse {brand} {model}", brand, price_range, {
            "tipo": "mouse", "conexão": connection, "sensor": dpi, "destaque": highlight,
        })
        for brand, model, connection, dpi, highlight, price_range in MICE
    ]


def draw_watches(rng: random.Random) -> list[dict]:
    watches = []
    for brand in WATCH_BRANDS:
        for model, (price_range, days, gps, resistance, calls) in WATCH_MODELS.items():
            sensors = "batimentos, oxigenação, sono" + (" e eletrocardiograma" if model == "Pro" else "")
            watches.append(item(rng, f"{brand} {model}", brand.split()[0], price_range, {
                "tipo": "smartwatch",
                "tela": f"AMOLED de {rng.choice(['1,3', '1,4', '1,5'])} polegada",
                "bateria": f"até {days} dias",
                "GPS": "sim, embutido" if gps else "não, usa o do celular",
                "resistência": resistance,
                "sensores": sensors,
                "chamadas": "sim, atende pelo relógio" if calls else "não",
            }))
    return watches


def draw_accessories(rng: random.Random) -> list[dict]:
    return [
        *draw_chargers(rng),
        *draw_cables(rng),
        *draw_cases(rng),
        *draw_keyboards(rng),
        *draw_mice(rng),
        *draw_watches(rng),
    ]
