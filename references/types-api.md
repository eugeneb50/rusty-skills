# Types, API design and naming

Load when: designing structs/enums/traits, a public API, conversions,
numeric code, closures, collections, or naming things. Rule of thumb: make
illegal states unrepresentable **where a bug has happened or would be
costly** — not everywhere (lean.md).

## Model the domain in types

- **Parse, don't validate**: convert untrusted input once, at the boundary,
  into a type that can only hold valid values (`Email::parse(s)? -> Email`);
  inner code takes `Email`, never re-checks. [api-parse-dont-validate] [type-newtype-validated]
- Newtypes for ids and units so they can't be swapped: `UserId(u64)`,
  `Millis(u64)`. [type-newtype-ids] [api-newtype-safety]
- Enums for mutually exclusive states, carrying each state's data — not a
  struct of `Option`s and a status string. [type-enum-states]
- No stringly-typed APIs: a closed set of values is an enum, with `FromStr`
  + `Display` at the edges. [type-no-stringly] [anti-stringly-typed]
- `Option<T>` for absence (no sentinel `-1`, `""`); `Result` for failure. [type-option-nullable]
- `NonZero*` when zero is invalid (and `Option<NonZeroU32>` is free). [num-nonzero]
- `!` for functions that never return (`-> !` exit/loop). [type-never-diverge]
- Typestate (`Conn<Open>` / `Conn<Closed>` with `PhantomData`) only when
  misuse order is a real bug source; it costs API surface. [api-typestate] [type-phantom-marker]
- `#[repr(transparent)]` on newtypes that cross FFI. [type-repr-transparent]

## Pattern matching

- Match your own enums exhaustively; a `_` arm hides new variants
  (`clippy::wildcard_enum_match_arm` in strict mode). [pat-exhaustive-enum]
- `let Some(x) = opt else { return ... };` for early exits
  (`clippy::manual_let_else`). [pat-let-else]
- `matches!(v, A | B)` for boolean tests; `if let ... && cond` chains
  (edition 2024) instead of nesting. [pat-matches-macro] [pat-if-let-chains]
- `n @ 1..=9` to bind while matching a range/pattern. [pat-at-bindings]

## Traits and generics

- Static dispatch (`impl Trait`, generics) by default; `dyn Trait` to store
  heterogeneous values or cut code size. Don't box what `impl Trait`
  returns fine. [trait-dyn-vs-generic] [anti-type-erasure]
- Keep traits you use as `dyn` object-safe (no generic methods, no `Self`
  returns without `where Self: Sized`). [trait-object-safety]
- Associated type when each impl has one output (`Iterator::Item`); generic
  parameter when a type implements it many ways (`From<T>`). [trait-associated-type-vs-generic]
- Few required methods, the rest defaulted on top of them. [trait-default-methods]
- Blanket impls (`impl<T: Display> MyTrait for T`) carefully: they block
  every other impl. [trait-blanket-impl]
- Orphan rule: wrap a foreign type in a newtype to give it a foreign trait. [trait-coherence-newtype]
- Bounds only where used, in `where` clauses when long. [type-generic-bounds]
- Native `async fn` in traits (1.75+) instead of `#[async_trait]` unless you
  need `dyn`. [async-fn-in-trait]
- Sealed traits to stop outside impls; extension traits to add methods to
  foreign types. [api-sealed-trait] [api-extension-trait]
- **No trait or generic with one implementation** "for testing/flexibility"
  until a second implementation or a test double actually exists. [anti-over-abstraction]

## Conversions

- Implement `From` (you get `Into` free); never implement `Into`. [api-from-not-into]
- `TryFrom` for fallible conversions, `FromStr` for parsing text (enables
  `.parse()`). [conv-tryfrom-fallible] [conv-fromstr-parsing]
- `AsMut<T>` for flexible mutable borrowed input (rarely needed). [conv-asmut-mutable]
- `Deref` only for smart pointers / transparent wrappers — never to fake
  inheritance. [type-deref-coercion]
- `Display` for users, `Debug` for developers; never swap them. [type-display-vs-debug]

## Numbers

- Overflow is a decision: `checked_*` (fail), `saturating_*` (clamp),
  `wrapping_*` (intended modulo), `overflowing_*`. Release builds wrap
  silently by default; consider `overflow-checks = true`. [num-overflow-explicit]
- No narrowing `as`: `u32::try_from(x)?`; widen with `From`.
  Lints: `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap`. [num-cast-try-from]
- Floats: never `==` (`clippy::float_cmp`); compare within a tolerance;
  sort with `total_cmp`. [num-float-compare]
- `clamp` / saturating ops to bound values. [num-saturating-clamp]
- Numeric newtypes may implement `LowerHex`/`Binary`/... when users print
  them that way. [type-numeric-fmt]

## Closures

- Accept the loosest bound: `FnOnce` ⊇ `FnMut` ⊇ `Fn`. [closure-fn-trait-bounds]
- Return `impl Fn`, not `Box<dyn Fn>`, unless stored heterogeneously. [closure-impl-fn-return]
- `impl Fn` generic for hot callbacks; `&dyn Fn` to cut monomorphisation. [closure-static-vs-dyn]
- `move` for closures that outlive the scope; clone what you keep first.
  Edition 2021 captures disjoint fields — capture only what you use. [closure-move-capture] [closure-disjoint-capture]
- Async callbacks: `AsyncFn*` bounds (1.85+) over `F: Fn() -> Fut`. [async-async-fn-bounds]

## Collections

- `Vec` by default; `VecDeque` for queues; never `LinkedList`. [coll-seq-choice]
- `HashMap` unordered/fast; `BTreeMap` sorted/range/deterministic output;
  `IndexMap` insertion order. **Iteration order that reaches output must be
  deterministic** (tests, diffs, JSON). [coll-map-choice]
- `HashSet`/`BTreeSet` for membership, not `Vec::contains` in a loop. [coll-set-membership]
- `BinaryHeap` (with `Reverse` for min) for priority queues. [coll-binaryheap]
- `entry()` for insert-or-update (`clippy::map_entry`). [perf-entry-api]

## Constants

- `const` = inlined value; `static` = one address (and interior mutability
  via atomics/`OnceLock`). Never `static mut`. [const-vs-static]
- `const fn` where it can run at compile time; inline `const { }` blocks
  for compile-time assertions. [const-fn] [const-block]
- Const generics `<const N: usize>` for fixed-size types. [const-generics]

## Public API checklist (libraries)

- Derive/implement the common traits users expect: `Debug` always; `Clone`,
  `PartialEq`, `Eq`, `Hash`, `Default`, `Ord` where meaningful;
  `Send + Sync` preserved. [api-common-traits] [api-default-impl]
- `#[non_exhaustive]` on public enums/structs you will extend. [api-non-exhaustive]
- Builder for many optional params, with `#[must_use]` setters; plain
  constructor when there are ≤ 3 params. [api-builder-pattern]
- Collections implement `FromIterator`, `Extend`, `IntoIterator` for `T`,
  `&T`, `&mut T`. [api-impl-fromiterator]
- Operators only where math-like semantics are obvious. [api-operator-overload]
- serde behind a feature flag in libraries. [api-serde-optional]

## Naming (Rust API Guidelines; rustc/clippy enforce most)

- `UpperCamelCase` types/traits/variants; `snake_case` fns/vars/modules;
  `SCREAMING_SNAKE_CASE` consts/statics; `T`, `E`, `K`, `V` type params. [name-types-camel] [name-variants-camel] [name-funcs-snake] [name-consts-screaming] [name-type-param-single]
- Acronyms are words: `HttpServer`, `Uuid`. [name-acronym-word]
- Conversions: `as_` free borrow, `to_` costly/allocating, `into_` consumes. [name-as-free] [name-to-expensive] [name-into-ownership]
- Getters drop `get_` (`fn len()`); booleans read as questions
  (`is_`, `has_`, `can_`, `should_`). [name-no-get-prefix] [name-is-has-bool]
- Iterators: `iter()`, `iter_mut()`, `into_iter()`, returning `Iter`,
  `IterMut`, `IntoIter`. [name-iter-convention] [name-iter-method] [name-iter-type-match]
- Crate names without `-rs`/`-rust`. [name-crate-no-rs]
- Shortest name that is unambiguous **in context**; no `Manager`,
  `Helper`, `Impl`, `_v2`, `_new` (lean.md).
