// Unit checks for src/state/urlState.ts (no test framework in this package): transpile with the
// project's own TypeScript and assert the R2-8 rules. Run: npm run test:url
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import assert from 'node:assert/strict';
import ts from 'typescript';

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, '../src/state/urlState.ts'), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
const dir = mkdtempSync(join(tmpdir(), 'url-state-'));
const file = join(dir, 'urlState.mjs');
writeFileSync(file, js);
const m = await import(pathToFileURL(file).href);
rmSync(dir, { recursive: true, force: true });

const list = [
  { id: 'controlled-rubbings-v2-text-2026-10-17', batch: '2026-10-17-v2-text', defaultForReport: true },
  { id: 'heldout-v20-v21-2026-10-18', batch: '2026-10-18-v21-heldout', defaultForReport: false },
];
let n = 0; const ok = (fn) => { fn(); n += 1; };

ok(() => assert.deepEqual(m.parseUrlState('').state, {}));
ok(() => assert.equal(m.buildUrlSearch({}, ''), ''));                       // no params -> nothing written
ok(() => { const p = m.parseUrlState('?tab=evil&steleId=x'); assert.equal(p.state.tab, undefined); assert.equal(p.issues[0].key, 'tab'); });
ok(() => { const p = m.parseUrlState('?runId=99999999T999999_deadbeef'); assert.equal(p.state.runId, '99999999T999999_deadbeef'); });
ok(() => { const p = m.parseUrlState('?runId=../../x'); assert.equal(p.state.runId, undefined); assert.equal(p.issues[0].key, 'runId'); });
ok(() => assert.deepEqual(m.resolveExperiment(list, {}), { status: 'none', experimentId: null }));
ok(() => { const r = m.resolveExperiment(list, { batch: '2026-10-17-v2-text' }); assert.equal(r.status, 'ok'); assert.equal(r.experimentId, 'controlled-rubbings-v2-text-2026-10-17'); assert.equal(r.via, 'batch'); });
ok(() => { const r = m.resolveExperiment(list, { experimentId: 'heldout-v20-v21-2026-10-18', batch: '2026-10-17-v2-text' }); assert.equal(r.experimentId, 'heldout-v20-v21-2026-10-18'); assert.match(r.notice, /以 experimentId 为准/); });
ok(() => { const r = m.resolveExperiment(list, { experimentId: 'nope' }); assert.equal(r.status, 'unknown'); assert.equal(r.experimentId, 'nope'); });
ok(() => { const r = m.resolveExperiment(list, { batch: 'nope' }); assert.equal(r.status, 'unknown'); assert.equal(r.experimentId, null); });
ok(() => assert.equal(m.defaultExperimentId(list), 'controlled-rubbings-v2-text-2026-10-17'));
ok(() => assert.equal(m.defaultExperimentId([{ id: 'a' }]), null));          // no default -> null, no heldout fallback
ok(() => assert.equal(m.buildUrlSearch({ experimentId: 'e', batch: 'b' }, '?batch=b&keep=1'), '?keep=1&experimentId=e'));
console.log(`urlState checks passed: ${n}`);
