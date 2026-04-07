# UX flow audit (Uzbek-first)

## Buyer flow

- **Entry confusion**: user home page does not always explain buyer path clearly.
- **Navigation gap**: missing consistent back action on webapp pages.
- **Error UX**: many pages show inline red text at bottom; users miss it.
- **Recovery path**: network/auth errors do not always suggest next action.

## Seller flow

- **Onboarding clarity**: sellers need a persistent checklist for first 5 tasks.
- **Shop guard**: seller pages can open even when shop is missing; causes confusion.
- **CRUD confidence**: no consistent action feedback style across save/update/delete.
- **Copy quality**: technical API-like phrases reduce trust and comprehension.

## Shared UX issues

- **Inconsistent status feedback**: mix of Telegram alert, inline messages, and no feedback.
- **No app-level toast layer**: no auto-dismiss, no queue, no unified style.
- **Back behavior**: no standard fallback route when history is empty.
- **State components**: empty/error/loading patterns are not fully consistent.

## Platform/admin impact

- Seller/operator-facing tasks are now broader, but UX polish must match webapp:
  - filter persistence,
  - clear next-action copy,
  - consistency in pagination and feedback.

## Revamp focus

1. Global toast + back header pattern.
2. Buyer path simplification (catalog > detail > order).
3. Seller guards + onboarding checklist.
4. Uzbek copy normalization for trust and clarity.
