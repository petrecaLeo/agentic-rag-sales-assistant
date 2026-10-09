import random

from data.generator.common import draw_price, draw_stock

# Na ordem dos tipos em KINDS.
MODELS = {
    "Pulse": ["Buds", "Buds ANC", "Run", "Bone", "Max", "Wave", "Fold", "Lite", "Arena", "Flex", "Kids", "Studio"],
    "Sonora": ["Air", "Air Pro", "Sprint", "Osso", "Silence", "Home", "City", "Fio", "Clash", "Neck", "Mini", "Monitor"],
    "Bassi": ["Drop", "Drop NC", "Fit", "Open", "Deep", "Groove", "Street", "Basic", "Raid", "Loop", "Junior", "Mix"],
    "Ondah": ["Go", "Go Pro", "Trail", "Livre", "Calm", "Waves", "Pocket", "Cabo", "Squad", "Band", "Turma", "Lab"],
    "Vibra": ["One", "One NC", "Gym", "Bone Air", "Quiet", "Bass", "Daily", "Wire", "Battle", "Sport", "Pequeno", "Pro Studio"],
}

KINDS = {
    "tws": (99, 249),
    "tws_anc": (299, 899),
    "sport": (149, 399),
    "bone": (349, 899),
    "over_anc": (699, 2499),
    "over": (199, 499),
    "on_ear": (129, 299),
    "wired": (39, 99),
    "gamer": (199, 799),
    "neckband": (99, 199),
    "kids": (99, 179),
    "studio": (399, 1299),
}

EARBUDS = "pontas de silicone em 3 tamanhos"


def attributes(rng: random.Random, kind: str) -> dict[str, str]:
    case_hours = f"{rng.choice([5, 6, 7])} h (até {rng.choice([20, 24, 28])} h com o estojo)"
    match kind:
        case "tws":
            return {"tipo": "intra-auricular sem fio", "conexão": "Bluetooth 5.3", "cancelamento de ruído": "não",
                    "bateria": case_hours, "resistência": "IPX4 (suor e respingos)", "encaixe": EARBUDS,
                    "microfone": "sim, para chamadas"}
        case "tws_anc":
            return {"tipo": "intra-auricular sem fio", "conexão": "Bluetooth 5.3",
                    "cancelamento de ruído": "ativo, com modo ambiente", "bateria": case_hours,
                    "resistência": "IPX4 (suor e respingos)", "encaixe": EARBUDS, "microfone": "sim, para chamadas"}
        case "sport":
            return {"tipo": "intra-auricular esportivo sem fio", "conexão": "Bluetooth 5.3",
                    "bateria": f"{rng.randint(8, 10)} h", "resistência": "IP55 (suor e chuva)",
                    "encaixe": "ganchos de orelha que seguram o fone no lugar", "microfone": "sim"}
        case "bone":
            return {"tipo": "condução óssea sem fio", "conexão": "Bluetooth 5.3", "bateria": f"{rng.randint(8, 10)} h",
                    "resistência": "IP67 (suor, chuva e mergulho rápido)",
                    "encaixe": "arco atrás da nuca, deixa o ouvido livre para ouvir a rua"}
        case "over_anc":
            return {"tipo": "over-ear sem fio", "conexão": "Bluetooth 5.3",
                    "cancelamento de ruído": "ativo, com 3 níveis", "bateria": f"{rng.choice([30, 40, 50, 60])} h",
                    "encaixe": "almofadas de espuma com memória", "dobrável": "sim, com estojo de viagem"}
        case "over":
            return {"tipo": "over-ear sem fio", "conexão": "Bluetooth 5.3", "cancelamento de ruído": "não",
                    "bateria": f"{rng.choice([40, 50, 70])} h", "graves": "reforçados"}
        case "on_ear":
            return {"tipo": "on-ear sem fio", "conexão": "Bluetooth 5.3", "bateria": f"{rng.choice([25, 30, 40])} h",
                    "dobrável": "sim", "peso": f"{rng.choice([150, 160, 170])} g"}
        case "wired":
            return {"tipo": "intra-auricular com fio", "conexão": rng.choice(["P2 3,5 mm", "USB-C"]),
                    "encaixe": EARBUDS, "microfone": "sim, com botão de atender", "cabo": "1,2 m"}
        case "gamer":
            return {"tipo": "headset gamer over-ear",
                    "conexão": rng.choice(["sem fio 2,4 GHz e Bluetooth", "USB com fio"]),
                    "som": "surround 7.1 virtual", "microfone": "removível, com redução de ruído",
                    "iluminação": "RGB"}
        case "neckband":
            return {"tipo": "sem fio com cordão no pescoço", "conexão": "Bluetooth 5.3",
                    "bateria": f"{rng.randint(15, 20)} h", "resistência": "IPX5 (suor)",
                    "encaixe": "fones magnéticos que se prendem um no outro"}
        case "kids":
            return {"tipo": "on-ear infantil com fio", "conexão": "P2 3,5 mm",
                    "volume": "limitado a 85 dB para proteger a audição", "material": "silicone flexível e resistente"}
        case "studio":
            return {"tipo": "over-ear de estúdio com fio", "conexão": "P2 3,5 mm com adaptador P10",
                    "som": "resposta plana, para mixagem e gravação", "cabo": "3 m"}
    raise ValueError(kind)


def draw_headphones(rng: random.Random) -> list[dict]:
    headphones = []
    for brand, models in MODELS.items():
        for model, (kind, price_range) in zip(models, KINDS.items()):
            prefix = "Headset" if kind == "gamer" else "Fone"
            headphones.append({
                "nome": f"{prefix} {brand} {model}",
                "categoria": "fones",
                "marca": brand,
                "preco": draw_price(rng, *price_range),
                "estoque": draw_stock(rng),
                "atributos": attributes(rng, kind),
            })
    return headphones
