import random
import re

from data.generator.common import decimal, draw_price, draw_stock

PROFILES = {
    "estudo": {
        "price": (2499, 3199), "cpus": ["Intel Core i3", "AMD Ryzen 3"], "memory": (8, 8), "ssd": (256, 512),
        "gpus": ["integrada"], "weight": (1.6, 1.9), "battery": (7, 9), "highlight": "webcam HD e teclado numérico",
    },
    "trabalho": {
        "price": (3299, 4799), "cpus": ["Intel Core i5", "AMD Ryzen 5"], "memory": (8, 16), "ssd": (512, 512),
        "gpus": ["integrada"], "weight": (1.5, 1.8), "battery": (9, 12), "highlight": "leitor de digital e webcam Full HD",
    },
    "leve": {
        "price": (4499, 6499), "cpus": ["Intel Core i7", "AMD Ryzen 7"], "memory": (16, 16), "ssd": (512, 1024),
        "gpus": ["integrada"], "weight": (1.0, 1.3), "battery": (13, 16),
        "highlight": "carcaça de alumínio com menos de 1,5 cm de espessura",
    },
    "jogos": {
        "price": (5999, 8999), "cpus": ["Intel Core i7", "AMD Ryzen 7"], "memory": (16, 32), "ssd": (512, 1024),
        "gpus": ["NVIDIA RTX 4050", "NVIDIA RTX 4060"], "weight": (2.2, 2.6), "battery": (4, 6),
        "highlight": "tela de 165 Hz e teclado com iluminação RGB",
    },
    "criação": {
        "price": (7999, 11999), "cpus": ["Intel Core i9", "AMD Ryzen 9"], "memory": (32, 32), "ssd": (1024, 2048),
        "gpus": ["NVIDIA RTX 4060"], "weight": (1.8, 2.1), "battery": (8, 10),
        "highlight": "tela 2.5K com cores calibradas para foto e vídeo",
    },
}

# Na ordem dos perfis: estudo, trabalho, leve, jogos, criação.
LINES = {
    "Vetor": ["Book 14", "15", "Air 13", "G15", "Studio 16"],
    "Lumen": ["Edu 14", "Office 15", "Slim 14", "Blaze 16", "Creator 16"],
    "Arca": ["Start 15", "Pro 14", "Feather 13", "Titan 15", "Atelier 16"],
    "Prisma": ["Campus 14", "Work 15", "Zero 13", "Strike 16", "Vision 16"],
}
SCREENS = {"13": "13,3", "14": "14", "15": "15,6", "16": "16"}


def storage_label(gigabytes: int) -> str:
    return f"{gigabytes // 1024} TB" if gigabytes >= 1024 else f"{gigabytes} GB"


def draw_notebooks(rng: random.Random) -> list[dict]:
    notebooks = []
    for brand, lines in LINES.items():
        for line, (profile_name, profile) in zip(lines, PROFILES.items()):
            base_price = draw_price(rng, *profile["price"])
            inches = SCREENS[re.search(r"\d+$", line).group()]
            cpu = rng.choice(profile["cpus"])
            weight = decimal(rng.uniform(*profile["weight"]))
            battery = rng.randint(*profile["battery"])
            for index in range(2):
                memory, ssd = profile["memory"][index], profile["ssd"][index]
                price = base_price if index == 0 else round(base_price * 1.2 / 1000) * 1000 - 10
                notebooks.append({
                    "nome": f"{brand} {line} ({memory} GB, SSD {storage_label(ssd)})",
                    "categoria": "notebooks",
                    "marca": brand,
                    "preco": price,
                    "estoque": draw_stock(rng),
                    "atributos": {
                        "processador": cpu,
                        "memória": f"{memory} GB",
                        "armazenamento": f"SSD de {storage_label(ssd)}",
                        "placa de vídeo": profile["gpus"][index % len(profile["gpus"])],
                        "tela": f"{inches} polegadas",
                        "peso": f"{weight} kg",
                        "bateria": f"até {battery} horas",
                        "perfil": profile_name,
                        "destaque": profile["highlight"],
                    },
                })
    return notebooks
