/**
 * dsh-teleagent-skill-builder host entry.
 *
 * The TeleAgent skill-authoring standard ships as plain files under
 * `assets/skills/teleagent-skill-builder`. On boot this plugin copies them into
 * the DSH skills directory so every session already has the standard loaded,
 * no manual `cp` step and no `.pyc` left behind.
 */
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const name = 'teleagent-skill-builder';

/** Skill id, also the directory name under the DSH skills root. */
const SKILL_ID = 'teleagent-skill-builder';
/** Bumped whenever the bundled standard changes, so upgrades re-copy. */
const STANDARD_VERSION = '1.0.0';
/** Marker file recording what this plugin last copied. */
const MARKER = '.kit-version';
/** Bytecode the TeleAgent review rejects; never copy or keep it. */
const FORBIDDEN = ['.pyc', '.pyo'];

function packageRoot() {
    return join(dirname(fileURLToPath(import.meta.url)), '..');
}

/** Absolute path of the bundled skill inside this package. */
export function bundledSkillDir() {
    return join(packageRoot(), 'assets', 'skills', SKILL_ID);
}

/** Where skills live: `config.skillsDir` wins, else `~/.dsh/skills`. */
export function skillsRoot(config) {
    const custom = config?.skillsDir;
    if (typeof custom === 'string' && custom.trim().length > 0) return custom;
    return join(homedir(), '.dsh', 'skills');
}

function log(ctx, level, message) {
    const logger = ctx?.logger;
    if (logger && typeof logger[level] === 'function') logger[level](message);
    else console.log(`[teleagent-skill-builder] ${message}`);
}

function skippedByBytecodeRule(path) {
    const normalized = path.replaceAll('\\', '/');
    if (normalized.includes('__pycache__')) return true;
    return FORBIDDEN.some((suffix) => normalized.toLowerCase().endsWith(suffix));
}

/**
 * Copy the bundled standard into the skills root.
 * @param ctx - Host context (used only for logging).
 * @param config - `{ install?: boolean, skillsDir?: string }`.
 * @returns `{ installed, target, version?, reason? }` — never throws.
 */
export function install(ctx, config = {}) {
    if (config.install === false) {
        log(ctx, 'info', '已禁用自动安装（install: false），跳过技能标准同步');
        return { installed: false, reason: 'disabled' };
    }
    const source = bundledSkillDir();
    if (!existsSync(join(source, 'SKILL.md'))) {
        log(ctx, 'warn', `技能标准文件缺失，跳过同步：${source}`);
        return { installed: false, reason: 'missing-source' };
    }
    const target = join(skillsRoot(config), SKILL_ID);
    const marker = join(target, MARKER);
    const previous = existsSync(marker) ? readFileSync(marker, 'utf8').trim() : '';
    if (previous === STANDARD_VERSION && existsSync(join(target, 'SKILL.md'))) {
        return { installed: false, target, version: STANDARD_VERSION, reason: 'up-to-date' };
    }
    try {
        mkdirSync(target, { recursive: true });
        cpSync(source, target, {
            recursive: true,
            force: true,
            filter: (path) => !skippedByBytecodeRule(path),
        });
        rmSync(join(target, '__pycache__'), { recursive: true, force: true });
        rmSync(join(target, 'scripts', '__pycache__'), { recursive: true, force: true });
        writeFileSync(marker, `${STANDARD_VERSION}\n`, 'utf8');
        const suffix = previous ? `（${previous} → ${STANDARD_VERSION}）` : '';
        log(ctx, 'info', `TeleAgent 技能标准已就位：${target}${suffix}`);
        return { installed: true, target, version: STANDARD_VERSION };
    } catch (error) {
        log(ctx, 'warn', `技能标准同步失败：${error?.message ?? error}`);
        return { installed: false, target, reason: 'error', error };
    }
}

/** Cordis entry: run once when the profile mounts this plugin. */
export function apply(ctx, config) {
    try {
        return install(ctx, config ?? {});
    } catch (error) {
        log(ctx, 'warn', `技能标准插件启动失败：${error?.message ?? error}`);
        return { installed: false, reason: 'error', error };
    }
}
