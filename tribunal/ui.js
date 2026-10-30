import {compare, makeReceipt, downloadReceipt, validateConfig} from "./bench.js";
import {PHASES} from "./core.js";

const el = id => document.getElementById(id);
const fmt = number => Number.isFinite(number) ? number.toFixed(4) : "—";
let lastReceipt = null;
let running = false;

export function mountTribunal() {
  if (!el("tribunal")) return;
  const run = el("tribunal-run");
  const exportButton = el("tribunal-export");
  const status = el("tribunal-status");
  const output = el("tribunal-output");
  const receiptOutput = el("tribunal-hash");

  run.addEventListener("click", async () => {
    if (running) return;
    running = true;
    run.disabled = true;
    exportButton.disabled = true;
    lastReceipt = null;
    output.replaceChildren();
    receiptOutput.textContent = "No measured receipt yet.";
    try {
      const config = validateConfig({
        seed: Number(el("tribunal-seed").value),
        count: Number(el("tribunal-rows").value),
        warmups: Number(el("tribunal-warmup").value),
        trials: Number(el("tribunal-trials").value)
      });
      status.textContent = "Running isolated paired trials. Keep this tab visible…";
      const report = await compare(config, (done,total) => {
        status.textContent = "Paired passes: " + done + "/" + total + " (warmups included)";
      });
      lastReceipt = await makeReceipt(report);
      const table = document.createElement("table");
      table.className = "tribunal-results";
      const caption = document.createElement("caption");
      caption.textContent = "Measured detached DOM mutation times (milliseconds; lower is less time for this operation).";
      table.append(caption);
      const thead = document.createElement("thead");
      const header = document.createElement("tr");
      for (const label of ["Operation", "Direct median", "Keyed median", "Paired Δ (keyed − direct)", "Bootstrap 95% interval"]) {
        const th = document.createElement("th");
        th.textContent = label;
        header.append(th);
      }
      thead.append(header);
      table.append(thead);
      const body = document.createElement("tbody");
      for (const phase of PHASES) {
        const m = report.statistics[phase];
        const cells = [
          phase, fmt(m.direct_median_ms), fmt(m.keyed_median_ms),
          fmt(m.paired_delta_median_ms),
          "[" + fmt(m.paired_delta_bootstrap_95_ms[0]) + ", " + fmt(m.paired_delta_bootstrap_95_ms[1]) + "]"
        ];
        const tr = document.createElement("tr");
        for (const value of cells) {
          const td = document.createElement("td");
          td.textContent = value;
          tr.append(td);
        }
        body.append(tr);
      }
      table.append(body);
      output.append(table);
      const bytes = document.createElement("p");
      bytes.className = "tribunal-footnote";
      bytes.textContent = "First-party adapter source: direct " + report.adapter_source_bytes.direct +
        " bytes; keyed " + report.adapter_source_bytes.keyed +
        " bytes. Excludes shared harness, site assets, browser runtime, minification and compression.";
      output.append(bytes);
      const warning = document.createElement("p");
      warning.className = "tribunal-footnote";
      warning.textContent = report.low_clock_resolution_observed
        ? "WARNING: Zero-duration samples detected; timing resolution may be insufficient. Treat differences as inconclusive."
        : "Descriptive local measurements only; browser/JIT/GC/CPU conditions are uncontrolled. No cross-framework or statistical superiority claim.";
      output.append(warning);
      receiptOutput.textContent = "SHA-256 of exported UTF-8 payload: " + lastReceipt.sha256;
      status.textContent = "PASS — " + report.correctness.trials_verified + " DOM phase assertions. " +
        report.config.trials + " measured paired trials. Source identity and measurement authenticity are NOT independently certified.";
      exportButton.disabled = false;
    } catch (error) {
      status.textContent = "NO RESULT — " + error.message + ". Failed or incomplete runs cannot be exported.";
      output.replaceChildren();
    } finally {
      run.disabled = false;
      running = false;
    }
  });
  exportButton.addEventListener("click", () => {
    if (lastReceipt && !running) downloadReceipt(lastReceipt);
  });
}
