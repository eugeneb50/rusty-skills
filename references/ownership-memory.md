# Ownership, borrowing and memory

Load when: choosing parameter/return types, fighting the borrow checker,
sharing state, or reducing allocations. Memory tuning is measure-first
(perf.md): the defaults below are about clarity; the second half is for
proven hot paths only.

## Defaults (always)

- Borrow, don't clone. A `.clone()` must be needed by ownership, not by
  convenience; `clippy::redundant_clone` finds the free ones. [own-borrow-over-clone] [anti-clone-excessive]
- Parameters: `&str` not `&String`, `&[T]` not `&Vec<T>`, `&Path` not
  `&PathBuf` (`clippy::ptr_arg`). [own-slice-over-vec] [anti-string-for-str] [anti-vec-for-slice]
- Take ownership (`String`, `Vec<T>`) only when you store it; then callers
  can move in instead of you cloning. `clippy::needless_pass_by_value`
  flags the reverse.
- `impl AsRef<str>`/`AsRef<Path>` when you only read; `impl Into<String>`
  when you store. Don't make every function generic for it. [api-impl-asref] [api-impl-into]
- `Cow<'_, str>` when a function returns borrowed input on the common path
  and an owned value only sometimes (escaping, normalising). [own-cow-conditional]
- Let lifetime elision work; name lifetimes only when the compiler asks.
  Names: `'a`, `'de`, `'src`. [own-lifetime-elision] [name-lifetime-short]
- `Copy` for small plain values (ids, coords, flags ≤ ~16 bytes). Keep
  `Clone` explicit when copying costs something. [own-copy-small] [own-clone-explicit]
- Move big values; `Box` only when moves are measured to cost or a
  recursive type needs it. [own-move-large]
- `std::mem::take`/`replace` to move a field out of `&mut self` instead of
  cloning it. [mem-take-replace]
- Drop order: struct fields top-to-bottom, locals in reverse declaration
  order. Matters for guards, files, handles; put the guard that must die
  last, first. [mem-drop-order]

## Shared state

| Need | Use |
|---|---|
| Shared read-only across threads | `Arc<T>` (clone with `Arc::clone(&x)`, `clippy::clone_on_ref_ptr`) [own-arc-shared] |
| Single-thread shared | `Rc<T>` [own-rc-single-thread] |
| Single-thread mutation through `&` | `Cell` (Copy) / `RefCell` (runtime-checked; a double borrow panics) [own-refcell-interior] |
| Cross-thread mutation | `Mutex<T>`; short critical sections, never across `.await` [own-mutex-interior] |
| Reads ≫ writes, measured contention | `RwLock<T>` (writer starvation is possible; often a `Mutex` is still faster) [own-rwlock-readers] |
| A counter/flag | atomics, not `Mutex<bool>` (`clippy::mutex_atomic`) |
| Latest value to many async readers | `tokio::sync::watch` (async.md) |

Prefer **one owner + messages** over `Arc<Mutex<_>>` webs when a task can own
the state. A global `static` that holds a resource is never dropped (no
flush, no cleanup at exit): give resources an owner with a lifetime.

## Proven hot paths only (profile first)

- `Vec::with_capacity`/`String::with_capacity` when the size is known. [mem-with-capacity]
- Reuse buffers: `clear()` and refill; `clone_from` reuses the target's
  allocation; `drain(..)` to move out without reallocating. [mem-reuse-collections] [mem-clone-from] [perf-drain-reuse]
- `write!(buf, ...)` into an existing `String` instead of `format!`; a
  literal or `to_owned()` when no formatting happens. [mem-write-over-format] [mem-avoid-format] [anti-format-hot-path]
- Small-size-optimised collections: `SmallVec<[T; N]>` (spills to heap),
  `ArrayVec<T, N>` (never heap, fixed cap), `ThinVec` (one-pointer, for
  mostly-empty vectors in large structs). Add the crate only with a
  measurement. [mem-smallvec] [mem-arrayvec] [mem-thinvec]
- `Box<[T]>` / `Box<str>` for data that never grows (saves the capacity
  word); compact/inline strings (`compact_str`, `smol_str`) for many short
  strings. [mem-boxed-slice] [mem-compact-string]
- Box a large enum variant so the rest don't pay its size
  (`clippy::large_enum_variant`). [mem-box-large-variant]
- Right-size integers in large arrays of structs (`u32` index vs `usize`). [mem-smaller-integers]
- Guard a hot type's size: `const _: () = assert!(size_of::<T>() <= 32);`. [mem-assert-type-size]
- Arena (`bumpalo`, `typed-arena`) for many short-lived same-lifetime
  allocations (parsers, ASTs). [mem-arena-allocator]
- Zero-copy: borrow from the input (`&'a str` fields, `serde` borrowing),
  `bytes::Bytes` for shared network buffers. [mem-zero-copy]
