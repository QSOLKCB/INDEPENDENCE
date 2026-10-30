import {TARGETS, runMutationLab, validateConfig} from "./core.js";

const byId = id => document.getElementById(id);
const el = (tag, className, value) => {
  const x = document.createElement(tag);
  if (className) x.className = className;
  if (value !== undefined) x.textContent = String(value);
  return x;
};
const targetName = new Map(TARGETS.map(t => [t.id,t.name]));
let latestEnvelope = null;

function display(report) {
  const summary=byId("breeding-summary");
  const list=byId("breeding-records");
  summary.replaceChildren();
  list.replaceChildren();
  for(const [label,value] of [
    ["FIXED MUTANTS",report.mutants],
    ["KILLED",report.summary.killed],
    ["SURVIVED",report.summary.survived],
    ["MUTATION SCORE",report.summary.killed+"/"+report.mutants]
  ]){
    const card=el("div","breeding-stat");
    card.append(el("strong","",value),el("span","",label));
    summary.append(card);
  }
  const fragment=document.createDocumentFragment();
  for(const result of report.results){
    const card=el("article","breeding-record");
    card.append(el("span","breeding-record-label",targetName.get(result.target)));
    card.append(el("h3","",result.mutant));
    card.append(el("p","",result.operator));
    const status=el("strong","breeding-state "+(result.status==="killed"?"breeding-killed":"breeding-survived"),
      result.status.toUpperCase());
    card.append(status);
    card.append(el("p","breeding-detail",
      "Caught by selected suite: "+(result.failing_tests.join(", ")||"none")));
    card.append(el("p","breeding-detail",
      "Known divergence witness(es): "+result.witness_tests.join(", ")));
    fragment.append(card);
  }
  list.append(fragment);
}
async function envelope(report) {
  if (!globalThis.crypto?.subtle) throw new Error("WebCrypto unavailable; export requires HTTPS or localhost");
  const payload_text=JSON.stringify(report,null,2);
  const bytes=new TextEncoder().encode(payload_text);
  const hash=await crypto.subtle.digest("SHA-256",bytes);
  const sha256=[...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,"0")).join("");
  return {format:"GREMLIN-BREEDING-RECEIPT/1",algorithm:"SHA-256/UTF-8",sha256,payload_text};
}
function saveReceipt(data) {
  const blob=new Blob([JSON.stringify(data,null,2)+"\n"],{type:"application/json"});
  const uri=URL.createObjectURL(blob);
  const anchor=document.createElement("a");
  anchor.href=uri;
  anchor.download="gremlin-breeding-"+data.sha256.slice(0,12)+".json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(uri),0);
}
export function mountBreeding() {
  if(!byId("breeding"))return;
  const run=byId("breeding-run");
  const exportButton=byId("breeding-export");
  const status=byId("breeding-status");
  const digest=byId("breeding-digest");
  run.addEventListener("click",async()=>{
    run.disabled=true;
    exportButton.disabled=true;
    latestEnvelope=null;
    digest.textContent="No receipt exported.";
    byId("breeding-summary").replaceChildren();
    byId("breeding-records").replaceChildren();
    try{
      const config=validateConfig({
        seed:Number(byId("breeding-seed").value),
        suite:byId("breeding-suite").value
      });
      const report=runMutationLab(config);
      display(report);
      status.textContent="COMPLETE: "+report.baseline_assertions+
        " baseline oracle checks, "+report.mutants+" non-equivalent fixture mutants. "+
        report.summary.survived+" survived the selected suite. Results are not security certification.";
      try{
        latestEnvelope=await envelope(report);
        digest.textContent="SHA-256 of UTF-8 report: "+latestEnvelope.sha256;
        exportButton.disabled=false;
      }catch(error){
        digest.textContent="Export unavailable: "+error.message+". The measured classifications above remain visible.";
      }
    }catch(error){
      status.textContent="INVALID RUN: "+error.message+". No evidence receipt issued.";
      digest.textContent="No valid receipt.";
    }finally{run.disabled=false;}
  });
  exportButton.addEventListener("click",()=>{
    if(latestEnvelope && !run.disabled)saveReceipt(latestEnvelope);
  });
}
