// Dead-code strip for the beta maps.
// usage: node strip.cjs <in.js> <out.js> <stubs.json> [--report]
//   stubs.json: {"functionName": "{ replacement body }", ...}
// 1. The named top-level functions get an empty body (they are the removed tabs' renderers and tools).
// 2. Every top-level function or side-effect-free const/let that is then no longer referenced
//    (transitively, from the code that still runs) is deleted.
// Identifiers are matched by name, which over-approximates references, so it only ever keeps too much.
const fs = require('fs');
const path = require('path');
const NM = process.env.NODE_TOOLS || '/opt/npm-tools/node_modules';
const acorn = require(path.join(NM, 'acorn'));
const walk = require(path.join(NM, 'acorn-walk'));

const [, , inF, outF, stubF, ...flags] = process.argv;
const src = fs.readFileSync(inF, 'utf8');
const STUBS = stubF ? JSON.parse(fs.readFileSync(stubF, 'utf8')) : {};
const PURE = new Set(STUBS.__pure__ || []); delete STUBS.__pure__;
const STUB = new Set(Object.keys(STUBS));
const ast = acorn.parse(src, { ecmaVersion: 'latest', sourceType: 'script', allowHashBang: true });

function idsIn(node) {
  const s = new Set();
  walk.full(node, n => { if (n.type === 'Identifier') s.add(n.name); });
  return s;
}
function hasSideEffects(node) {
  if (!node) return false;
  let fx = false;
  walk.fullAncestor(node, (n, st, anc) => {
    if (fx) return;
    if (['CallExpression', 'NewExpression', 'AssignmentExpression', 'UpdateExpression', 'AwaitExpression', 'TaggedTemplateExpression'].includes(n.type)) {
      // calls inside a nested function body don't run at declaration time
      const insideFn = anc.slice(0, -1).some(a => a !== node && /Function/.test(a.type));
      if (!insideFn) fx = true;
    }
  });
  return fx;
}
function patNames(p, out = []) {
  if (!p) return out;
  if (p.type === 'Identifier') out.push(p.name);
  else if (p.type === 'ObjectPattern') p.properties.forEach(q => patNames(q.value || q.argument, out));
  else if (p.type === 'ArrayPattern') p.elements.forEach(e => patNames(e, out));
  else if (p.type === 'RestElement') patNames(p.argument, out);
  else if (p.type === 'AssignmentPattern') patNames(p.left, out);
  return out;
}

const defs = new Map(); // name -> [{kind, node, decl, refs}]
const roots = new Set();
const edits = []; // {start,end,text}
const stubbed = [], dropped = [], fxNames = [];
for (const st of ast.body) {
  if (st.type === 'FunctionDeclaration') {
    const name = st.id.name;
    let refs;
    if (STUB.has(name)) {
      const body = STUBS[name];
      edits.push({ start: st.body.start, end: st.body.end, text: body });
      refs = idsIn(acorn.parse('function _(' + st.params.map(q => src.slice(q.start, q.end)).join(',') + ')' + body, { ecmaVersion: 'latest' }));
      stubbed.push(name);
    }
    else refs = idsIn(st);
    refs.delete(name);
    (defs.get(name) || defs.set(name, []).get(name)).push({ kind: 'fn', node: st, refs });
  } else if (st.type === 'VariableDeclaration') {
    for (const d of st.declarations) {
      const names = patNames(d.id);
      const removable = d.id.type === 'Identifier' && (PURE.has(d.id.name) || !hasSideEffects(d.init));
      if (!removable && d.id.type === 'Identifier') fxNames.push(d.id.name);
      const refs = d.init ? idsIn(d.init) : new Set();
      if (!removable) { refs.forEach(r => roots.add(r)); names.forEach(n => roots.add(n)); continue; }
      (defs.get(names[0]) || defs.set(names[0], []).get(names[0])).push({ kind: 'var', node: d, decl: st, refs });
    }
  } else {
    // a top-level statement that re-assigns a stubbed function (a wrapper that adds to a removed tab) goes too
    let patches = false;
    walk.full(st, n => { if (n.type === 'AssignmentExpression' && n.left.type === 'Identifier' && STUB.has(n.left.name)) patches = true; });
    if (patches) { edits.push({ start: st.start, end: st.end, text: '' }); dropped.push(src.slice(st.start, st.start + 60)); continue; }
    idsIn(st).forEach(r => roots.add(r));
  }
}
for (const n of STUB) if (!stubbed.includes(n)) { console.error('stub target not found: ' + n); process.exit(2); }
// reachability
const live = new Set();
const queue = [...roots];
while (queue.length) {
  const n = queue.pop();
  if (live.has(n)) continue;
  live.add(n);
  for (const d of defs.get(n) || []) d.refs.forEach(r => { if (!live.has(r)) queue.push(r); });
}
const removed = [];
const declLeft = new Map();
for (const [name, ds] of defs) {
  if (live.has(name)) continue;
  for (const d of ds) {
    removed.push({ name, kind: d.kind, bytes: d.node.end - d.node.start });
    if (d.kind === 'fn') edits.push({ start: d.node.start, end: d.node.end, text: '' });
    else {
      const left = declLeft.get(d.decl) ?? d.decl.declarations.length;
      declLeft.set(d.decl, left - 1);
      d.decl._rm = (d.decl._rm || []).concat(d.node);
    }
  }
}
for (const [decl, left] of declLeft) {
  if (left === 0) edits.push({ start: decl.start, end: decl.end, text: '' });
  else {
    // rebuild the declaration from the declarators that stay
    const keep = decl.declarations.filter(d => !decl._rm.includes(d));
    edits.push({ start: decl.start, end: decl.end, text: decl.kind + ' ' + keep.map(d => src.slice(d.start, d.end)).join(',') + ';' });
  }
}
// apply edits, outermost first, skipping any nested inside an already-removed range
edits.sort((a, b) => a.start - b.start || b.end - a.end);
const flat = [];
for (const e of edits) { const last = flat[flat.length - 1]; if (last && e.start < last.end) continue; flat.push(e); }
let out = src;
for (const e of flat.reverse()) out = out.slice(0, e.start) + e.text + out.slice(e.end);
fs.writeFileSync(outF, out);
const tot = removed.reduce((a, r) => a + r.bytes, 0);
if (flags.includes('--report')) {
  // declarations kept only because their initialiser calls something: candidates for __pure__
  const refd = new Set();
  for (const [n, ds] of defs) if (live.has(n)) ds.forEach(d => d.refs.forEach(r => refd.add(r)));
  for (const st of ast.body) if (st.type !== 'FunctionDeclaration' && st.type !== 'VariableDeclaration') idsIn(st).forEach(r => refd.add(r));
  for (const st of ast.body) if (st.type === 'VariableDeclaration') for (const d of st.declarations) if (d.init) idsIn(d.init).forEach(r => { if (!patNames(d.id).includes(r)) refd.add(r); });
  fxNames.filter(n => !refd.has(n)).forEach(n => console.log('side-effect decl, otherwise unused:', n));
  removed.sort((a, b) => b.bytes - a.bytes).forEach(r => console.log(String(r.bytes).padStart(7), r.kind, r.name));
}
dropped.forEach(d => console.log('dropped patch: ' + d.replace(/\s+/g, ' ')));
console.log(`stubbed ${STUB.size}, removed ${removed.length} declarations, ${(tot / 1024).toFixed(1)} KB; ${(src.length / 1024).toFixed(1)} KB -> ${(out.length / 1024).toFixed(1)} KB`);
