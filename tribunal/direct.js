// Direct DOM replacement baseline. First-party code; not a third-party framework.
export const ADAPTER = Object.freeze({id: "direct", label: "Direct DOM", kind: "native"});

export function createAdapter(root) {
  return {
    render(rows) {
      const fragment = document.createDocumentFragment();
      for (const row of rows) {
        const node = document.createElement("li");
        node.dataset.id = row.id;
        node.textContent = row.label;
        fragment.appendChild(node);
      }
      root.replaceChildren(fragment);
    }
  };
}
