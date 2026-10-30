// Tiny local keyed reconciler illustrating an abstraction layer.
// Not React, Vue, Svelte, or a representative sample of any framework.
export const ADAPTER = Object.freeze({id: "keyed", label: "Local keyed adapter", kind: "illustrative"});

export function createAdapter(root) {
  const nodes = new Map();
  return {
    render(rows) {
      const next = new Map();
      const ordered = [];
      for (const row of rows) {
        let node = nodes.get(row.id);
        if (!node) {
          node = document.createElement("li");
          node.dataset.id = row.id;
        }
        if (node.textContent !== row.label) node.textContent = row.label;
        ordered.push(node);
        next.set(row.id, node);
      }
      // Preserve existing node identities but set an explicit deterministic order.
      root.replaceChildren(...ordered);
      nodes.clear();
      for (const [id, node] of next) nodes.set(id, node);
    }
  };
}
