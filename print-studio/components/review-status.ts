'use client';
// Review status for each handout. 'reviewed' means read, with points still to settle;
// 'approved' means ready to print. A status only counts while its card revision matches,
// so an edited card drops back to "to review". When the studio runs locally the record is
// saved to data/review-status.json (through /api/reviews), so it survives a browser change
// and can be read by whoever edits the cards. On the hosted site it stays in this browser.
import { useCallback, useEffect, useRef, useState } from 'react';
import type { CommentStore } from '@/components/review-comments';

export type ReviewStatus = 'reviewed' | 'approved';
export type Review = { revision: string; at: string; status?: ReviewStatus };
export type Reviews = Record<string, Review>;

// Older records had one "reviewed" tick. A tick on a card with no comments was an approval;
// a tick on a card with comments means it still needs work.
function withStatus(reviews: Reviews, commented: Set<string>): Reviews {
  return Object.fromEntries(
    Object.entries(reviews).map(([id, r]) => [
      id,
      r.status ? r : { ...r, status: commented.has(id) ? 'reviewed' : 'approved' },
    ]),
  );
}

// Keeps the later record for each handout (a tick made while the shared record loads).
function later(base: Reviews, extra: Reviews): Reviews {
  const next = { ...base };
  for (const [id, r] of Object.entries(extra)) if (!next[id] || next[id].at < r.at) next[id] = r;
  return next;
}

async function post(body: Record<string, unknown>) {
  const r = await fetch('/api/reviews', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const result = (await r.json()) as { reviews?: Reviews; message?: string };
  if (!r.ok || !result.reviews) throw new Error(result.message || 'The review could not be saved.');
  return result.reviews;
}

/**
 * Shares the page's review record with data/review-status.json. Waits until the page has
 * loaded this browser's record (`ready`) and the comments are known, then merges the two,
 * keeping the later record for each handout.
 */
export function useSharedReviews(
  reviews: Reviews,
  setReviews: (next: Reviews | ((old: Reviews) => Reviews)) => void,
  ready: boolean,
  comments: CommentStore,
) {
  const [shared, setShared] = useState<boolean | null>(null);
  const [error, setError] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (!ready || comments.shared === null || started.current) return;
    started.current = true;
    const commented = new Set(comments.comments.map((c) => c.itemId));
    const local = withStatus(reviews, commented);
    void (async () => {
      try {
        const merged = await post({ action: 'merge', reviews: local });
        setReviews((old) => later(merged, withStatus(old, commented)));
        setShared(true);
      } catch {
        setReviews((old) => later(local, withStatus(old, commented)));
        setShared(false);
      }
    })();
  }, [ready, comments.shared, comments.comments, reviews, setReviews]);

  const set = useCallback(
    (id: string, review: Review) => {
      setError('');
      setReviews((old) => ({ ...old, [id]: review }));
      if (shared) {
        post({ action: 'set', id, review }).catch((e: unknown) =>
          setError(e instanceof Error ? e.message : 'The review could not be saved.'),
        );
      }
    },
    [shared, setReviews],
  );

  return { shared, error, set };
}
