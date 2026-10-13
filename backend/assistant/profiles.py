from dataclasses import dataclass, replace

from backend.config import HAIKU, SONNET


@dataclass(frozen=True)
class Profile:
    name: str
    model: str
    thinking: dict
    effort: str
    max_tokens: int = 500
    # O prompt da v1: os perfis medidos o mantêm, para a comparação ficar justa.
    prompt: str = "v2"
    cache: bool = False
    router: str | None = None
    tools: str = "local"


# Cada perfil liga uma coisa nova em cima do anterior, para a eval medir o efeito de cada uma.
# O "disabled" dá erro 400 no Sonnet 5.5; o between_tools é o ajuste mais baixo.
BASE = Profile("base", SONNET, {"type": "between_tools"}, "low")
CACHE = replace(BASE, name="cache", cache=True)
ROTA = replace(CACHE, name="rota", router="haiku")
# O Haiku 5.5 recusa o between_tools: pensa no modo adaptive, na medida do effort. O pensamento conta no
# max_tokens, e com 500 o Sonnet já ficou sem espaço para responder depois de muitas tools.
HAIKU_LOW = replace(ROTA, name="haiku-low", model=HAIKU, thinking={"type": "adaptive"}, effort="low", max_tokens=1500)
HAIKU_MEDIUM = replace(HAIKU_LOW, name="haiku-medium", effort="medium")
HAIKU_HIGH = replace(HAIKU_LOW, name="haiku-high", effort="high")
# O melhor da etapa 4 com as tools rodando num servidor MCP separado, em vez de dentro do app.
MCP = replace(HAIKU_LOW, name="mcp", tools="mcp")
# Com o agente no Haiku, o separador quase não economiza e soma 1,2 s em toda mensagem: este perfil mede o agente sozinho.
HAIKU_DIRETO = replace(HAIKU_LOW, name="haiku-direto", router=None)
# Depois das medidas, o prompt v3 corrige o que a eval e a tela mostraram no Haiku: ids, listas e o "lista tudo".
HAIKU_V3 = replace(HAIKU_DIRETO, name="haiku-v3", prompt="v3")

PROFILES = {
    profile.name: profile
    for profile in [BASE, CACHE, ROTA, HAIKU_LOW, HAIKU_MEDIUM, HAIKU_HIGH, MCP, HAIKU_DIRETO, HAIKU_V3]
}

# O perfil da v2: o haiku-direto, que é o mais rápido e 47 vezes mais barato que a v1, com o prompt v3.
ACTIVE_PROFILE = "haiku-v3"


def active_profile() -> Profile:
    return PROFILES[ACTIVE_PROFILE]
