import {STAGES, CONTROLS, CASE_STUDIES, makeHandoff, gateStatus} from "./core.js";

// All displayed content is static first-party text or user-entered plain text.
// Nothing is submitted, persisted, evaluated as code, or sent to a remote model.
const $ = id => document.getElementById(id);
function el(tag, className, content) {
  const element = document.createElement(tag);
  if(className) element.className=className;
  if(content!==undefined) element.textContent=String(content);
  return element;
}
function stageDetails(stage) {
  const view=$("workflow-stage-detail");
  view.replaceChildren();
  const kicker=el("p","workflow-owner",stage.owner+" / "+stage.id.toUpperCase());
  const title=el("h3","",stage.title);
  const description=el("p","workflow-stage-description",stage.instruction);
  const drift=el("div","workflow-drift");
  drift.append(el("strong","","DRIFT FAILURE"),el("p","",stage.drift));
  const proof=el("div","workflow-proof");
  proof.append(el("strong","","EVIDENCE GATE"),el("p","",stage.evidence));
  const example=el("div","workflow-example");
  example.append(el("strong","","EXAMPLE"),el("p","",stage.example));
  view.append(kicker,title,description,drift,proof,example);
}
const fields=["goal","scope","excluded","invariants","acceptance"];
function inputValues() {
  return Object.fromEntries(fields.map(key=>[key,$("workflow-"+key).value]));
}
function setMessage(message,failed=false) {
  $("workflow-builder-status").textContent=message;
  $("workflow-builder-status").className="workflow-builder-status "+(failed?"workflow-error":"");
}
export function mountWorkflow(){
  if(!$("workflow"))return;
  const nav=$("workflow-stage-nav");
  const first=[];
  for(const [index,stage] of STAGES.entries()){
    const button=el("button","workflow-stage-button",
      String(index+1).padStart(2,"0")+" / "+stage.title);
    button.type="button";
    button.setAttribute("aria-pressed","false");
    button.addEventListener("click",()=>{
      for(const previous of nav.children)previous.setAttribute("aria-pressed",previous===button?"true":"false");
      stageDetails(stage);
    });
    nav.append(button);
    first.push(button);
  }
  first[0]?.click();

  const gateList=$("workflow-gate-list");
  const acknowledged={};
  function displayGates(){
    const result=gateStatus(acknowledged);
    $("workflow-gate-status").textContent=result.acknowledged+"/"+result.total+
      " safeguards acknowledged (self-assessment only; no repository checks were run).";
  }
  for(const gate of CONTROLS){
    const wrapper=el("label","workflow-gate");
    const input=el("input");
    input.type="checkbox";
    input.checked=false;
    input.addEventListener("change",()=>{
      acknowledged[gate.id]=input.checked;
      displayGates();
    });
    const label=el("span","workflow-gate-label");
    label.append(el("strong","",gate.label),el("small","",gate.why));
    wrapper.append(input,label);
    gateList.append(wrapper);
  }
  displayGates();

  const studies=$("workflow-case-studies");
  for(const item of CASE_STUDIES){
    const card=el("article","workflow-case");
    card.append(el("span","workflow-case-version",item.version),
      el("h4","",item.title),el("p","",item.lesson));
    const link=el("a","","INSPECT MERGED PR ↗");
    link.href=item.source;
    link.rel="noopener noreferrer";
    card.append(link);
    studies.append(card);
  }

  const output=$("workflow-prompt");
  const copy=$("workflow-copy");
  let current="";
  function invalidate(){
    current="";
    output.textContent="No handoff generated. Enter an observable goal and generate your prompt.";
    copy.disabled=true;
    setMessage("Prompt not generated. Nothing has been submitted or executed.");
  }
  for(const key of fields)$("workflow-"+key).addEventListener("input",invalidate);
  $("workflow-load-example").addEventListener("click",()=>{
    const sample={
      goal:"Add a first-party static workflow section accessible at #workflow.",
      scope:"index.html, workflow/*.js, workflow/*.css, tests and documentation only.",
      excluded:"No third-party packages, remote LLM calls, checkout automation, credential access, unrelated refactors, or release operations.",
      invariants:"Preserve docs/INVARIANTS.md, deterministic browser checks, offline Python tests, strict CSP and human merge authority.",
      acceptance:"Navigation reaches #workflow; source audit passes; new positive/negative tests pass; existing features and deployment remain intact."
    };
    for(const key of fields)$("workflow-"+key).value=sample[key];
    invalidate();
    setMessage("Illustrative mission loaded. Review and edit before using; no checks have run.");
  });
  $("workflow-build").addEventListener("click",()=>{
    try{
      current=makeHandoff(inputValues());
      output.textContent=current;
      copy.disabled=false;
      setMessage("Local template generated. Review all constraints before sending it to any agent.");
    }catch(error){
      invalidate();
      setMessage("Cannot generate handoff: "+error.message,true);
    }
  });
  copy.addEventListener("click",async()=>{
    if(!current)return;
    try{
      if(!navigator.clipboard?.writeText)throw new Error("Clipboard unavailable in this context");
      await navigator.clipboard.writeText(current);
      setMessage("Prompt copied locally. No model was called; you control where to send it.");
    }catch(error){
      setMessage("Copy failed: "+error.message+". Select and copy the displayed text manually.",true);
    }
  });
  invalidate();
}
