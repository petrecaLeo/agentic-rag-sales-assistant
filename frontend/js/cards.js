import { t } from "./i18n.js";

const MAX_CARDS = 4;
const PRODUCT_FIELDS = ["nome", "preco", "estoque", "disponivel"];

// Os cards saem só do resultado das tools, nunca do texto do modelo: preço e estoque vêm do servidor.
export function createCardCollector() {
  const products = new Map();
  const shown = [];

  const remember = (data) => {
    const product = products.get(data.id) ?? { id: data.id, coupons: [] };
    for (const field of PRODUCT_FIELDS) {
      if (data[field] !== undefined) product[field] = data[field];
    }
    products.set(data.id, product);
    return product;
  };
  const show = (id) => {
    if (!shown.includes(id)) shown.push(id);
  };

  return {
    add(name, data) {
      if (name === "buscar_produtos") {
        data.produtos?.forEach(remember);
      } else if (name === "consultar_produto" || name === "consultar_estoque") {
        remember(data);
        show(data.id);
      } else if (name === "validar_cupom") {
        const product = remember({ id: data.produto_id, nome: data.produto });
        product.preco ??= data.preco_original;
        product.coupons.push(data);
        show(data.produto_id);
      }
    },
    cards: () => shown.slice(0, MAX_CARDS).map((id) => products.get(id)),
  };
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function stockBadge(product) {
  if (product.disponivel === undefined) return null;
  return product.disponivel
    ? element("span", "badge in-stock", t("cards.inStock").replace("{n}", product.estoque))
    : element("span", "badge out-of-stock", t("cards.outOfStock"));
}

function couponLine(coupon) {
  const line = element("div", `coupon ${coupon.valido ? "valid" : "invalid"}`);
  line.append(element("span", "coupon-code", coupon.cupom));
  if (coupon.valido) {
    line.append(element("s", "coupon-from", coupon.preco_original), element("strong", "coupon-to", coupon.preco_final));
  } else {
    line.append(element("span", "coupon-reason", t(`coupons.${coupon.motivo}`)));
  }
  return line;
}

export function renderCards(products) {
  const grid = element("div", "cards");
  for (const product of products) {
    const card = element("article", "card");
    const row = element("div", "card-row");
    if (product.preco) row.append(element("span", "card-price", product.preco));
    const badge = stockBadge(product);
    if (badge) row.append(badge);
    card.append(element("h3", "card-name", product.nome ?? `#${product.id}`), row, ...product.coupons.map(couponLine));
    grid.append(card);
  }
  return grid;
}
