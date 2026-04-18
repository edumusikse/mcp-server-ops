const esbuild = require('esbuild');
const watch = process.argv.includes('--watch');

const ctx = esbuild.context({
    entryPoints: ['src/extension.ts'],
    bundle: true,
    outfile: 'dist/extension.js',
    external: ['vscode'],
    format: 'cjs',
    platform: 'node',
    target: 'node20',
    sourcemap: true,
    minify: !watch,
});

ctx.then(c => watch ? c.watch() : c.rebuild().then(() => { console.log('built'); c.dispose(); }))
   .catch(() => process.exit(1));
