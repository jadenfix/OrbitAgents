# OrbitAgents frontend checks

```bash
npm ci --ignore-scripts --no-audit --no-fund
npm run type-check
npm test -- --runInBand
npm run build
```

`src/main.tsx` loads `src/App.tsx`. The five explicitly excluded `App-*` files are preserved historical snapshots, not imported application code. All other source and tests remain in the TypeScript project. Importing an excluded snapshot from active code will still bring it into type checking.

Authentication uses the existing AuthContext/API, including rejection handling. No local timer or fallback fabricates successful login. Router tests use a real router with mocked auth state; login tests mock provider responses. These checks do not verify the live authentication service, browser automation workers, or provider credentials.

`npm run lint` now loads its configuration correctly, but still reports existing explicit-any, Fast Refresh, and hook-dependency warnings under the repository's zero-warning policy. Those failures are recorded rather than suppressed.
