import {EXHIBITS, runExhibit, runAll, assembleReport} from "./core.js";

const $ = id => document.getElementById(id);
const node = (type,cls,value) => {
  const element = document.createElement(type);
  if (cls) element.className=cls;
  if (value!==undefined) element.textContent=String(value);
  return element;
};
let last=null;
let reportText="";
let receiptSHA="";
function show(id) {
  const item=EXHIBITS.find(x=>x.id===id);
  if(!item) return;
  const output=$("museum-stage");
  output.replaceChildren();
  const header=node("div","museum-exhibit-meta",item.kind+" / "+item.provenance);
  const title=node("h3","museum-exhibit-title",item.title);
  const lesson=node("p","museum-lesson",item.lesson);
  const source=node("a","museum-source","ORIGIN / SOURCE ↗");
  source.href=item.source;
  source.rel="noopener noreferrer";
  const before=node("pre","museum-code museum-before","Click REPRODUCE to inspect the fixed specimen.");
  const after=node("pre","museum-code museum-after","The corrected behaviour will be displayed here.");
  const input=node("pre","museum-code museum-input","Specimen input shown after reproduction.");
  const verification=node("p","museum-assertions","Assertions not yet run.");
  const execute=node("button","museum-execute","REPRODUCE THIS GREMLIN ↗");
  execute.type="button";
  execute.addEventListener("click",()=>{
    const result=runExhibit(id);
    input.textContent=result.input;
    before.textContent=result.legacy;
    after.textContent=result.hardened;
    verification.textContent=(result.passed?"PASS":"FAIL")+" — "+result.assertions.passed+"/"+result.assertions.total+
      " deterministic fixture checks. No payload executed.";
    verification.className="museum-assertions "+(result.passed?"museum-pass":"museum-fail");
  });
  output.append(header,title,lesson,node("h4","","SPECIMEN / INERT INPUT"),input,
    node("h4","","LEGACY / FAILURE MODE"),before,node("h4","","CORRECTION / BOUNDED MITIGATION"),
    after,verification,execute,source);
}

async function receipt(report) {
  // Exact payload-text hashing. A digest does not authenticate who made a claim.
  const payload_text=JSON.stringify(report,null,2);
  const bytes=new TextEncoder().encode(payload_text);
  if(!globalThis.crypto?.subtle) throw new Error("WebCrypto unavailable: HTTPS or localhost required");
  const hash=await crypto.subtle.digest("SHA-256",bytes);
  const sha256=[...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,"0")).join("");
  return {format:"GREMLIN-MUSEUM-RECEIPT/1",algorithm:"SHA-256/UTF-8",sha256,payload_text};
}

export function mountMuseum() {
  if(!$("museum")) return;
  const list=$("museum-specimens");
  for (const item of EXHIBITS) {
    const button=node("button","museum-specimen",item.title);
    button.type="button";
    button.dataset.exhibit=item.id;
    button.addEventListener("click",()=>{
      for(const child of list.children) child.setAttribute("aria-pressed",child===button?"true":"false");
      show(item.id);
    });
    button.setAttribute("aria-pressed","false");
    list.append(button);
  }
  const initial=list.firstElementChild;
  initial?.click();
  const run=$("museum-run-all");
  const exportButton=$("museum-export");
  const status=$("museum-status");
  const fingerprint=$("museum-hash");
  run.addEventListener("click",async()=>{
    exportButton.disabled=true;
    last=null;
    reportText="";
    receiptSHA="";
    status.textContent="Running local, deterministic fixture checks…";
    try {
      const results=runAll();
      const report=assembleReport(results);
      last=await receipt(report);
      receiptSHA=last.sha256;
      reportText=JSON.stringify(last,null,2)+"\n";
      fingerprint.textContent="SHA-256 (exact UTF-8 payload): "+receiptSHA;
      status.textContent="PASS: "+results.length+" exhibits, "+
        results.reduce((n,r)=>n+r.assertions.passed,0)+" assertions. Demonstrations only; no real-world exploit claims.";
      exportButton.disabled=false;
    } catch(error) {
      status.textContent="FAILED / NOT EXPORTED: "+error.message;
      fingerprint.textContent="No valid receipt.";
    }
  });
  exportButton.addEventListener("click",()=>{
    if(!last||!reportText||!receiptSHA) return;
    const blob=new Blob([reportText],{type:"application/json"});
    const url=URL.createObjectURL(blob);
    const link=document.createElement("a");
    link.href=url;
    link.download="gremlin-museum-"+receiptSHA.slice(0,12)+".json";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),0);
  });
}
