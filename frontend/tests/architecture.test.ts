// @vitest-environment node
import path from 'node:path';
import {expect, it} from 'vitest';
// The checker intentionally runs outside the browser application.
// @ts-expect-error Plain Node script does not need a runtime TypeScript declaration.
import {checkArchitecture, violations, SRC} from '../scripts/check-architecture.mjs';

it('enforces production slice boundaries', () => {
  expect(checkArchitecture()).toEqual([]);
});
it('rejects shared dependencies, private imports and misplaced transport', () => {
  expect(violations(path.join(SRC, 'shared/example.ts'), 'import {useStudy} from "../features/studies";')).not.toEqual([]);
  expect(violations(path.join(SRC, 'features/studies/example.ts'), 'import {ChatDock} from "../assistant/ChatDock";')).not.toEqual([]);
  expect(violations(path.join(SRC, 'features/studies/example.ts'), 'import App from "../../App";')).not.toEqual([]);
  expect(violations(path.join(SRC, 'features/studies/example.ts'), 'import {request} from "../../shared/http";')).not.toEqual([]);
  expect(violations(path.join(SRC, 'features/intersections/example.ts'), 'import {PredictionPanel} from "../forecasting";')).toEqual([]);
});
