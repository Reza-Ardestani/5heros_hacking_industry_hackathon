import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import ts from 'typescript';

export const SRC = fileURLToPath(new URL('../src/', import.meta.url));
const SLICES = new Set(['studies', 'intersections', 'forecasting', 'assistant', 'storage']);

export function violations(file, source, root = SRC) {
  const failures = [];
  const relative = path.relative(root, file).split(path.sep);
  const ownSlice = relative[0] === 'features' ? relative[1] : null;
  const shared = relative[0] === 'shared';
  const test = relative.includes('__tests__');
  const parsed = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true);
  function inspect(node) {
    let module;
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier)
      module = node.moduleSpecifier.text;
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword &&
        ts.isStringLiteral(node.arguments[0])) module = node.arguments[0].text;
    if (module?.startsWith('.')) {
      const destination = path.resolve(path.dirname(file), module);
      const target = path.relative(root, destination).split(path.sep);
      if (target[0] === 'features') {
        const targetSlice = target[1];
        if (!SLICES.has(targetSlice)) failures.push(`Unknown slice ${targetSlice}`);
        if (shared) failures.push('Shared code cannot import features');
        if (ownSlice !== targetSlice && target.length > 2 &&
            !(target.length === 3 && ['index', 'index.ts'].includes(target[2])))
          failures.push(`Private cross-feature import ${module}`);
      } else if (ownSlice && !test && ['App', 'App.tsx', 'main', 'main.tsx'].includes(target[0])) {
        failures.push('Feature cannot import application shell');
      }
      if (shared && ['App', 'App.tsx', 'main', 'main.tsx'].includes(target[0]))
        failures.push('Shared code cannot import application shell');
      if (ownSlice && !test && target.join('/') === 'shared/http' && path.basename(file) !== 'api.ts')
        failures.push('Feature transport calls belong in api.ts');
    }
    if (ts.isCallExpression(node) && node.expression.getText(parsed) === 'fetch' &&
        path.relative(root, file).split(path.sep).join('/') !== 'shared/http.ts')
      failures.push('Raw fetch belongs in shared/http.ts');
    ts.forEachChild(node, inspect);
  }
  inspect(parsed);
  return failures;
}

export function checkArchitecture(root = SRC) {
  const failures = [];
  function scan(directory) {
    for (const item of fs.readdirSync(directory, {withFileTypes: true})) {
      const file = path.join(directory, item.name);
      if (item.isDirectory()) scan(file);
      else if (/\.tsx?$/.test(item.name))
        failures.push(...violations(file, fs.readFileSync(file, 'utf8'), root)
          .map(message => `${path.relative(root, file)}: ${message}`));
    }
  }
  scan(root);
  return failures;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  const failures = checkArchitecture();
  if (failures.length) {
    process.stderr.write(failures.join('\n') + '\n');
    process.exitCode = 1;
  } else process.stdout.write('Frontend slice boundaries passed.\n');
}
