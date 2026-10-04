# Plan

Move existing components into owning feature folders; split the global types file
by ownership. Add feature API modules over shared transport, public entry points
and colocated component tests. Extract useStudy and StudiesWorkspace from App;
keep routing/composition in App. Allow intersections to compose forecasting and
storage through public entry points and consume public study contracts. Shared
code imports no features; slices import no application shell. Check imports with
TypeScript AST using the existing compiler dependency.
