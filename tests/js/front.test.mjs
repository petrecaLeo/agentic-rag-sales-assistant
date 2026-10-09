import assert from "node:assert/strict";
import { test } from "node:test";

// O i18n lê o idioma do navegador ao ser importado.
globalThis.navigator = { language: "pt-BR" };
globalThis.localStorage = { getItem: () => null, setItem() {} };
globalThis.document = { documentElement: {}, querySelectorAll: () => [] };

const { createCardCollector } = await import("../../frontend/js/cards.js");
const { toolLabel } = await import("../../frontend/js/tools.js");

const search = { produtos: [{ id: 93, nome: "Fone Pulse Run", preco: "R$ 339,90" }, { id: 141, nome: "Fone Vibra Gym", preco: "R$ 229,90" }] };

test("uma busca sozinha não vira card", () => {
  const cards = createCardCollector();
  cards.add("buscar_produtos", search);
  assert.deepEqual(cards.cards(), []);
});

test("o card junta o preço da busca, o estoque e o cupom, sem repetir produto", () => {
  const cards = createCardCollector();
  cards.add("buscar_produtos", search);
  cards.add("consultar_estoque", { id: 93, nome: "Fone Pulse Run", estoque: 58, disponivel: true });
  cards.add("consultar_estoque", { id: 93, nome: "Fone Pulse Run", estoque: 58, disponivel: true });
  cards.add("validar_cupom", { cupom: "FONE15", produto_id: 93, produto: "Fone Pulse Run", valido: true, preco_original: "R$ 339,90" });
  const [card, ...rest] = cards.cards();
  assert.equal(rest.length, 0);
  assert.equal(card.preco, "R$ 339,90");
  assert.equal(card.estoque, 58);
  assert.equal(card.coupons[0].cupom, "FONE15");
});

test("produto que só apareceu no cupom usa o preço original dele", () => {
  const cards = createCardCollector();
  cards.add("validar_cupom", { cupom: "NOTE200", produto_id: 5, produto: "Aurora S 256 GB", valido: false, preco_original: "R$ 3.049,90" });
  assert.equal(cards.cards()[0].preco, "R$ 3.049,90");
});

test("no máximo 4 cards", () => {
  const cards = createCardCollector();
  for (const id of [1, 2, 3, 4, 5]) cards.add("consultar_estoque", { id, nome: `P${id}`, estoque: 1, disponivel: true });
  assert.deepEqual(cards.cards().map((c) => c.id), [1, 2, 3, 4]);
});

test("o passo mostra a busca, o filtro e o teto de preço", () => {
  assert.equal(
    toolLabel("buscar_produtos", { consulta: "notebook gamer", categoria: "notebooks", preco_max: 7000 }),
    "Buscando “notebook gamer” em notebooks, até R$ 7.000",
  );
  assert.equal(toolLabel("buscar_politica", { pergunta: "prazo de entrega" }), "Consultando a política: “prazo de entrega”");
  assert.equal(toolLabel("apagar_tudo", {}), "Consultando a loja");
});

test("texto longo vindo do modelo é cortado no passo", () => {
  assert.ok(toolLabel("buscar_produtos", { consulta: "x".repeat(500) }).length < 80);
});
