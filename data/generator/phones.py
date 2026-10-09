import random

from data.generator.common import decimal, draw_price, draw_stock, thousands

# Posição na lista = faixa de preço, da linha de entrada (0) à mais cara (4).
LINES = {
    "Aurora": ["Neo", "X", "S", "X Pro", "Fold"],
    "Nimbus": ["7 Lite", "7", "8", "8 Max", "Ultra"],
    "Kora": ["Go", "A3", "A5", "A7", "Flip"],
    "Vetta": ["Mini", "One", "Play", "Prime", "Pro"],
    "Orbi": ["E1", "E2", "Note", "Note Plus", "Edge"],
}
TIER_PRICES = [(899, 1399), (1499, 2199), (2299, 3299), (3499, 4999), (5499, 7999)]
TIER_STORAGE = [(128, 256), (128, 256), (256, 512), (256, 512), (256, 512)]
TIER_CAMERA = [50, 50, 64, 108, 200]
TIER_CHARGING = [25, 33, 45, 67, 100]
TIER_RESISTANCE = ["IP54 (respingos)", "IP54 (respingos)", "IP67 (água e poeira)", "IP68 (água e poeira)", "IP68 (água e poeira)"]
STORAGE_STEP = {256: 30000, 512: 50000}

HIGHLIGHTS = {
    "Fold": "abre como um tablet de 7,6 polegadas",
    "Flip": "dobra ao meio e cabe em qualquer bolso",
    "Mini": "cabe numa mão só",
    "Play": "câmara de vapor que segura partidas longas sem esquentar",
    "8 Max": "bateria que aguenta dois dias de uso",
    "Note": "caneta stylus na caixa",
    "Note Plus": "caneta stylus na caixa",
    "Ultra": "zoom óptico de 5x",
    "Pro": "zoom óptico de 5x",
    "X Pro": "zoom óptico de 5x",
    "Edge": "tela curva nas bordas",
}


def screen(rng: random.Random, line: str, tier: int) -> str:
    size = 5.8 if line == "Mini" else round(rng.uniform(6.1, 6.8), 1)
    refresh = "144 Hz" if line == "Play" else "120 Hz" if tier >= 2 else "90 Hz"
    folding = ", dobrável" if line in {"Fold", "Flip"} else ""
    return f"{decimal(size)} polegadas, {refresh}{folding}"


def battery(rng: random.Random, line: str) -> int:
    if line in {"8 Max", "Note", "Note Plus"}:
        return 6000
    if line == "Mini":
        return 3800
    return rng.choice([4000, 4500, 5000])


def draw_phones(rng: random.Random) -> list[dict]:
    phones = []
    for brand, lines in LINES.items():
        for tier, line in enumerate(lines):
            base_price = draw_price(rng, *TIER_PRICES[tier])
            camera = f"{TIER_CAMERA[tier]} MP" + (", com modo noturno" if tier >= 3 else "")
            attributes = {
                "tela": screen(rng, line, tier),
                "bateria": f"{thousands(battery(rng, line))} mAh",
                "câmera principal": camera,
                "resistência": "IPX4 (respingos)" if line in {"Fold", "Flip"} else TIER_RESISTANCE[tier],
                "5G": "sim" if tier >= 1 else "não",
                "carregamento": f"{TIER_CHARGING[tier]} W",
            }
            if line in HIGHLIGHTS:
                attributes["destaque"] = HIGHLIGHTS[line]
            for index, storage in enumerate(TIER_STORAGE[tier]):
                price = base_price if index == 0 else base_price + STORAGE_STEP[storage]
                phones.append({
                    "nome": f"{brand} {line} {storage} GB",
                    "categoria": "celulares",
                    "marca": brand,
                    "preco": price,
                    "estoque": draw_stock(rng),
                    "atributos": {"armazenamento": f"{storage} GB", **attributes},
                })
    return phones
