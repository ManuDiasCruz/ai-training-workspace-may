import { spawnSync } from 'node:child_process';
import dotenv from 'dotenv';

const mode = process.argv[2] || 'unit';
if (!['unit', 'integration', 'serve'].includes(mode)) throw new Error('Unknown test mode');
if (mode !== 'unit') {
  dotenv.config({ path: '.env.test' });
  let url;
  try { url = new URL(process.env.DATABASE_URL); } catch { /* handled below */ }
  if (!url || !['postgres:', 'postgresql:'].includes(url.protocol) || !url.pathname.endsWith('_test')) {
    console.error('Refusing database tests: provide a dedicated DATABASE_URL whose database name ends in _test.');
    process.exit(1);
  }
}
process.env.NODE_ENV = 'test';
function run(args) {
  const result = spawnSync(process.execPath, args, { stdio: 'inherit', env: process.env });
  if (result.error || result.status !== 0) process.exit(result.status || 1);
}
if (mode !== 'unit') run(['node_modules/prisma/build/index.js', 'migrate', 'deploy']);
if (mode === 'serve') {
  process.env.ENABLE_TEST_ROUTES = 'true';
  run(['node_modules/tsx/dist/cli.mjs', 'src/server.ts']);
} else {
  delete process.env.ENABLE_TEST_ROUTES;
  run(['--experimental-vm-modules', 'node_modules/jest/bin/jest.js', '--runInBand', `tests/${mode}`]);
}
