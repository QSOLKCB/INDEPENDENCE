// GREMLIN-BREEDING/1 — fixed mutation catalogue over pure, inert functions.
// Mutants NEVER rewrite repository files, execute generated code, or touch networks.
export const PROTOCOL = "GREMLIN-BREEDING/1";
export const SUITES = Object.freeze(["smoke","full"]);
const isReceipt = value => typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
const htmlMap = Object.freeze({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"});
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => htmlMap[char]);
function finite(value) {
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(finite);
  if (value && typeof value === "object") return Object.values(value).every(finite);
  return true;
}
const isVendored = ({root,file}) => {
  if (!file.startsWith(root + "/")) return false;
  return file.slice(root.length + 1).split("/").slice(0,-1)
    .some(part => part === ".venv" || part === "node_modules");
};
const importPattern = /\bimport\s*(?:\(\s*|[^;\n]*?\bfrom\s*)?['"]https?:\/\//i;
const remoteImport = value => importPattern.test(value);

// Case inputs are deliberately fixed local values, never evaluated, interpreted as HTML markup,
// dynamically imported, sent over the network, or used with a shell or external target.
const targets = [
  {
    id:"receipt", name:"SHA Identity",
    reference:isReceipt,
    cases:[
      ["valid64","a".repeat(64),true,"smoke"],
      ["reject40","a".repeat(40),false,"smoke"],
      ["rejectNonHex","g".repeat(64),false,"full"],
      ["rejectUpper","A".repeat(64),false,"full"],
      ["validOther","b".repeat(64),true,"full"]
    ],
    mutants:[
      ["accept40or64","Boundary widened",x=>typeof x==="string"&&/^(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(x)],
      ["acceptUppercase","Case restriction removed",x=>typeof x==="string"&&/^[0-9a-f]{64}$/i.test(x)],
      ["lengthOnly","Hex check removed",x=>typeof x==="string"&&x.length===64]
    ]
  },
  {
    id:"encoding", name:"HTML Encoding",
    reference:escapeHtml,
    cases:[
      ["tag","<x>","&lt;x&gt;","smoke"],
      ["plain","safe","safe","smoke"],
      ["ampersand","A&B","A&amp;B","full"],
      ["quotes",'"'+"'","&quot;&#39;","full"],
      ["combined","<x&>","&lt;x&amp;&gt;","full"]
    ],
    mutants:[
      ["noEncoding","Encoding removed",x=>String(x)],
      ["missAmp","Ampersand escape removed",x=>String(x).replace(/[<>"']/g,c=>htmlMap[c])],
      ["missQuotes","Quote escapes removed",x=>String(x).replace(/[&<>]/g,c=>htmlMap[c])]
    ]
  },
  {
    id:"finite", name:"Finite JSON",
    reference:finite,
    cases:[
      ["finiteObject",{n:1},true,"smoke"],
      ["finiteList",[1,2],true,"smoke"],
      ["directInfinite",{n:Infinity},false,"full"],
      ["nestedInfinite",{nested:[{n:Infinity}]},false,"full"],
      ["nullAllowed",null,true,"full"],
      ["negativeInfinite",[-Infinity],false,"full"]
    ],
    mutants:[
      ["alwaysTrue","Finite check removed",()=>true],
      ["shallow","Recursive validation removed",x=>{
        if(typeof x==="number")return Number.isFinite(x);
        if(x&&typeof x==="object")return Object.values(x).every(v=>typeof v!=="number"||Number.isFinite(v));
        return true;
      }],
      ["rejectNull","Null handling inverted",x=>x===null?false:finite(x)]
    ]
  },
  {
    id:"scope", name:"Repository Scope",
    reference:isVendored,
    cases:[
      ["localVendor",{root:"/repo",file:"/repo/node_modules/pkg.js"},true,"smoke"],
      ["clean",{root:"/repo",file:"/repo/app.js"},false,"smoke"],
      ["ancestorVenv",{root:"/tmp/.venv/repo",file:"/tmp/.venv/repo/app.js"},false,"full"],
      ["localVenv",{root:"/repo",file:"/repo/.venv/lib/a.py"},true,"full"],
      ["partialFolder",{root:"/repo",file:"/repo/node_modules-ish/x.js"},false,"full"]
    ],
    mutants:[
      ["absoluteAncestry","Scope widened to checkout ancestors",({file})=>
        file.split("/").slice(0,-1).some(x=>x===".venv"||x==="node_modules")],
      ["ignoreVenv","One vendored directory omitted",({root,file})=>
        file.startsWith(root+"/")&&file.slice(root.length+1).split("/").slice(0,-1).includes("node_modules")],
      ["substringFolder","Exact directory boundary removed",({root,file})=>
        file.startsWith(root+"/")&&file.slice(root.length+1).split("/").slice(0,-1).some(x=>
          x.includes(".venv")||x.includes("node_modules"))]
    ]
  },
  {
    id:"imports", name:"Remote Import Audit",
    reference:remoteImport,
    cases:[
      ["named", "import {x} from "+"'https://example.invalid/x.js';",true,"smoke"],
      ["local","import './local.js';",false,"smoke"],
      ["sideEffect","import "+"'https://example.invalid/x.js';",true,"full"],
      ["dynamic","import("+"'https://example.invalid/x.js');",true,"full"],
      ["urlAsData","const note = 'https://example.invalid/x.js';",false,"full"]
    ],
    mutants:[
      ["fromOnly","Side-effect import form omitted",x=>
        /\bimport\s*(?:\(\s*|[^;\n]*?\bfrom\s*)['"]https?:\/\//i.test(x)],
      ["staticOnly","Dynamic import form omitted",x=>
        /\bimport\s*(?:[^;\n]*?\bfrom\s*)?['"]https?:\/\//i.test(x)],
      ["anyURL","Import context ignored",x=>/https?:\/\//i.test(x)]
    ]
  }
];
export const TARGETS=Object.freeze(targets.map(t=>Object.freeze({
  id:t.id,name:t.name,cases:Object.freeze(t.cases.map(c=>Object.freeze({id:c[0],tier:c[3]}))),
  mutants:Object.freeze(t.mutants.map(m=>Object.freeze({id:m[0],operator:m[1]})))
})));

function nextRandom(seed) {
  let state=seed>>>0;
  return ()=>{
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>>= 0);
  };
}
export function validateConfig({seed,suite}={}) {
  if(!Number.isInteger(seed)||seed<1||seed>0xffffffff)throw new RangeError("seed must be unsigned nonzero 32-bit");
  if(!SUITES.includes(suite))throw new RangeError("unknown test suite");
  return {seed,suite};
}
function equal(a,b){return Object.is(a,b);}
function catalogue() {
  return targets.flatMap(t=>t.mutants.map(m=>({target:t,mutant:m})));
}
export function runMutationLab(options) {
  const {seed,suite}=validateConfig(options);
  let baselineAssertions=0;
  for(const target of targets){
    for(const [id,input,expected] of target.cases){
      if(!equal(target.reference(input),expected))
        throw new Error("baseline oracle failed: "+target.id+"/"+id);
      baselineAssertions++;
    }
  }
  const mutations=catalogue();
  const random=nextRandom(seed);
  for(let i=mutations.length-1;i>0;i--){
    const j=random()%(i+1);
    [mutations[i],mutations[j]]=[mutations[j],mutations[i]];
  }
  const results=[];
  for(const {target,mutant} of mutations){
    const [mutantId,operator,candidate]=mutant;
    const allFailures=target.cases.filter(([,input,expected])=>!equal(candidate(input),expected)).map(([id])=>id);
    if(!allFailures.length)throw new Error("equivalent or unproven mutant: "+target.id+"/"+mutantId);
    const selected=new Set(target.cases.filter(c=>suite==="full"||c[3]==="smoke").map(c=>c[0]));
    const failed=allFailures.filter(id=>selected.has(id));
    results.push({
      id:target.id+"/"+mutantId, target:target.id, mutant:mutantId,
      operator, status:failed.length?"killed":"survived",
      failing_tests:failed, witness_tests:allFailures
    });
  }
  const killed=results.filter(r=>r.status==="killed").length;
  return {
    schema_version:1, protocol:PROTOCOL,
    config:{seed,suite},targets:targets.length,baseline_assertions:baselineAssertions,
    mutants:results.length,results,
    summary:{killed,survived:results.length-killed, mutation_score:{numerator:killed,denominator:results.length}},
    limitations:[
      "Fixed first-party mutation catalogue; not arbitrary mutation of application source files.",
      "Survival means selected tests missed a known divergent fixture, not that the defect is safe.",
      "Mutation score is scoped to these curated cases and cannot certify repository-wide test quality."
    ]
  };
}
