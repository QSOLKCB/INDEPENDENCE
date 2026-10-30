import {runProofChecks,CONTRACT_IDS} from "./core.js";

const $=id=>document.getElementById(id);
const node=(tag,cls,body)=>{
  const x=document.createElement(tag);
  if(cls)x.className=cls;
  if(body!==undefined)x.textContent=String(body);
  return x;
};
let exportEnvelope=null;
function display(report){
  const box=$("proof-results");
  box.replaceChildren();
  for(const row of report.checks){
    const card=node("article","proof-case");
    card.append(node("span","proof-id",row.id));
    card.append(node("strong","proof-state "+(row.status==="COUNTEREXAMPLE"?"proof-counterexample":"proof-observed"),row.status));
    card.append(node("p","","Cases: "+row.cases+" · assertions: "+row.assertions));
    if(row.implication)card.append(node("p","proof-implication",row.implication));
    if(row.stored_fingerprint)card.append(node("p","proof-hash-compare",
      "Stored: "+row.stored_fingerprint+" / after mutation: "+row.recomputed_fingerprint));
    box.append(card);
  }
  for(const title of ["LEAN-TRANSITION","SPARK-TRANSITION","RECEIPT-AUTHENTICITY"]){
    const card=node("article","proof-case");
    card.append(node("span","proof-id",title),node("strong","proof-state proof-pending","NOT PROVED"));
    card.append(node("p","","Future obligation: no verified formal discharge or execution attestation is claimed."));
    box.append(card);
  }
}
async function wrapReceipt(report){
  if(!globalThis.crypto?.subtle)throw new Error("WebCrypto needs HTTPS or localhost");
  const payload_text=JSON.stringify(report,null,2);
  const raw=new TextEncoder().encode(payload_text);
  const digest=await crypto.subtle.digest("SHA-256",raw);
  const sha256=[...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,"0")).join("");
  return {format:"PROOF-CONTRACT-RECEIPT/1",algorithm:"SHA-256/UTF-8",sha256,payload_text};
}
function downloadReceipt(envelope){
  const data=new Blob([JSON.stringify(envelope,null,2)+"\n"],{type:"application/json"});
  const url=URL.createObjectURL(data),link=document.createElement("a");
  link.href=url;
  link.download="proof-contracts-"+envelope.sha256.slice(0,12)+".json";
  document.body.append(link);
  try{link.click();}finally{link.remove();setTimeout(()=>URL.revokeObjectURL(url),0);}
}
export function mountProof(){
  if(!$("proof"))return;
  const run=$("proof-run"),download=$("proof-export"),status=$("proof-status"),hash=$("proof-hash");
  download.disabled=true;
  run.addEventListener("click",async()=>{
    run.disabled=true;
    download.disabled=true;
    exportEnvelope=null;
    hash.textContent="No verified payload digest.";
    $("proof-results").replaceChildren();
    status.textContent="Executing deterministic checks against the loaded first-party JavaScript…";
    try{
      const report=runProofChecks();
      if(report.checks.length!==CONTRACT_IDS.length)
        throw new Error("incomplete proof check sequence");
      display(report);
      status.textContent="Completed "+report.checks.length+
        " observations; the mutable fingerprint is a documented COUNTEREXAMPLE. No formal proofs executed.";
      try{
        exportEnvelope=await wrapReceipt(report);
        hash.textContent="SHA-256 (exact UTF-8 report): "+exportEnvelope.sha256;
        download.disabled=false;
      }catch(error){
        hash.textContent="Receipt not available: "+error.message;
      }
    }catch(error){
      status.textContent="FAILED: "+error.message+". No evidence receipt issued.";
      hash.textContent="No valid receipt.";
    }finally{run.disabled=false;}
  });
  download.addEventListener("click",()=>{
    if(exportEnvelope&&!run.disabled)downloadReceipt(exportEnvelope);
  });
}
