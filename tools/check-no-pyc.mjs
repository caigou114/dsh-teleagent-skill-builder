/**
 * Prepack guard.
 *
 * The TeleAgent review rejects any skill carrying bytecode ("存在恶意扩展名文件"),
 * and plugin bundles must stay clean too. Run before `npm pack` / `npm publish`:
 * exits non-zero the moment a `.pyc`, `.pyo` or `__pycache__` shows up.
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const packageRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const FORBIDDEN_SUFFIXES = ['.pyc', '.pyo'];
const SKIP_DIRS = new Set(['node_modules', '.git']);
const REQUIRED = ['package.json', 'cordis.patch.yml', 'lib/index.js', 'assets/skills/teleagent-skill-builder/SKILL.md'];

const problems = [];
let files = 0;
let bytes = 0;

function walk(dir) {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
        if (entry.isDirectory()) {
            if (SKIP_DIRS.has(entry.name)) continue;
            if (entry.name === '__pycache__') {
                problems.push(`发现 __pycache__ 目录：${relative(packageRoot, join(dir, entry.name))}（平台审核会拒收）`);
                continue;
            }
            walk(join(dir, entry.name));
            continue;
        }
        const path = join(dir, entry.name);
        const rel = relative(packageRoot, path).replaceAll('\\', '/');
        const lower = entry.name.toLowerCase();
        if (FORBIDDEN_SUFFIXES.some((suffix) => lower.endsWith(suffix))) {
            problems.push(`发现字节码文件：${rel}（平台审核会拒收 .pyc/.pyo）`);
            continue;
        }
        files += 1;
        bytes += statSync(path).size;
    }
}

walk(packageRoot);

for (const required of REQUIRED) {
    try {
        statSync(join(packageRoot, required));
    } catch {
        problems.push(`缺少必需文件：${required}`);
    }
}

const manifest = JSON.parse(readFileSync(join(packageRoot, 'package.json'), 'utf8'));
if (!manifest.keywords?.includes('dsh-plugin')) problems.push('package.json 的 keywords 必须包含 "dsh-plugin"，否则插件市场索引不到');
if (manifest.dsh?.bundle?.patch !== './cordis.patch.yml') problems.push('package.json 缺少 "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }');
if (!manifest.name?.startsWith('dsh-')) problems.push('包名建议以 dsh- 开头，便于在插件市场里检索');

if (problems.length > 0) {
    console.error('[check-no-pyc] 失败：');
    for (const problem of problems) console.error(`  - ${problem}`);
    process.exit(1);
}

console.log(`[check-no-pyc] 通过：${files} 个文件，${(bytes / 1024).toFixed(1)} KB，无 .pyc/.pyo/__pycache__`);
