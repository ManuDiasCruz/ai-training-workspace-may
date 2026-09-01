import { spawnSync } from 'node:child_process';
let name = '';
try { name = new URL(process.env.DATABASE_URL ?? '').pathname.slice(1); } catch {}
if (process.env.NODE_ENV !== 'test' || !name.endsWith('_test')) {
  throw new Error('Test migrations require NODE_ENV=test and a database name ending in _test');
}
const result = spawnSync(process.execPath, ['node_modules/prisma/build/index.js', 'migrate', 'deploy'], { stdio: 'inherit' });
process.exit(result.status ?? 1);
