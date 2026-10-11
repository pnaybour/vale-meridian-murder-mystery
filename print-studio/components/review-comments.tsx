'use client';
// Review comments on handouts. When the studio runs locally the comments are saved to
// data/review-comments.json in the project (through /api/comments), so they survive a
// browser change and can be read by whoever edits the cards. On the hosted site, where
// that endpoint does not exist, they fall back to this browser only.
import { useCallback, useEffect, useState } from 'react';
import { MessageSquare, Check, RotateCcw, Trash2, ArrowUpRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import type { Item } from '@/lib/types';

export type ReviewComment = {
  id: string;
  itemId: string;
  itemTitle: string;
  character: string;
  round: number | null;
  revision: string;
  quote: string;
  text: string;
  status: 'open' | 'resolved';
  createdAt: string;
  resolvedAt?: string;
  /** What the card editor did about it, written into data/review-comments.json with the fix. */
  reply?: string;
};

const LOCAL_KEY = 'valemeridian-review-comments-v1';

export function useReviewComments() {
  const [comments, setComments] = useState<ReviewComment[]>([]);
  const [shared, setShared] = useState<boolean | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    fetch('/api/comments')
      .then(async (r) => {
        if (!r.ok) throw new Error('unavailable');
        const body = (await r.json()) as { comments: ReviewComment[] };
        if (!cancelled) {
          setComments(body.comments);
          setShared(true);
        }
      })
      .catch(() => {
        if (cancelled) return;
        try {
          setComments(JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]'));
        } catch {
          setComments([]);
        }
        setShared(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const apply = useCallback(
    async (action: string, payload: Record<string, unknown>, local: (list: ReviewComment[]) => ReviewComment[]) => {
      setError('');
      if (shared) {
        try {
          const r = await fetch('/api/comments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, ...payload }),
          });
          const body = (await r.json()) as { comments?: ReviewComment[]; message?: string };
          if (!r.ok || !body.comments) throw new Error(body.message || 'The comment could not be saved.');
          setComments(body.comments);
        } catch (e) {
          setError(e instanceof Error ? e.message : 'The comment could not be saved.');
        }
        return;
      }
      setComments((old) => {
        const next = local(old);
        try {
          localStorage.setItem(LOCAL_KEY, JSON.stringify(next));
        } catch {
          setError('Browser storage is unavailable, so this comment will be lost on reload.');
        }
        return next;
      });
    },
    [shared],
  );

  const add = (item: Item, text: string, quote: string) => {
    const comment: ReviewComment = {
      id: `c-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
      itemId: item.id,
      itemTitle: item.title,
      character: item.character,
      round: item.round,
      revision: item.revision,
      quote,
      text,
      status: 'open',
      createdAt: new Date().toISOString(),
    };
    return apply('add', { comment }, (list) => [...list, comment]);
  };
  const setStatus = (id: string, status: 'open' | 'resolved') =>
    apply('status', { id, status }, (list) =>
      list.map((c) =>
        c.id === id
          ? { ...c, status, resolvedAt: status === 'resolved' ? new Date().toISOString() : undefined }
          : c,
      ),
    );
  const remove = (id: string) => apply('delete', { id }, (list) => list.filter((c) => c.id !== id));

  return { comments, shared, error, add, setStatus, remove };
}

export type CommentStore = ReturnType<typeof useReviewComments>;

function when(iso: string) {
  return new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function CommentCard({
  c,
  store,
  changed,
  approved,
  onOpen,
}: {
  c: ReviewComment;
  store: CommentStore;
  changed: boolean;
  approved: boolean;
  onOpen?: () => void;
}) {
  return (
    <li className={`comment-card ${c.status}${approved ? ' on-approved' : ''}`}>
      <div className="comment-meta">
        {onOpen ? (
          <button className="comment-item" onClick={onOpen}>
            {c.character || c.itemTitle} · {c.itemTitle}
            {c.round !== null && ` · R${c.round}`} <ArrowUpRight size={12} />
          </button>
        ) : (
          <span>{when(c.createdAt)}</span>
        )}
        {changed && <span className="comment-changed">card changed since</span>}
        {approved && <span className="comment-approved">card approved</span>}
        {c.status === 'resolved' && <span className="comment-resolved">resolved</span>}
      </div>
      {c.quote && <blockquote>{c.quote}</blockquote>}
      <p>{c.text}</p>
      {c.reply && <p className="comment-reply">{c.reply}</p>}
      <div className="comment-actions">
        {onOpen && <span className="comment-when">{when(c.createdAt)}</span>}
        {c.status === 'open' ? (
          <button onClick={() => void store.setStatus(c.id, 'resolved')}>
            <Check size={13} /> Resolve
          </button>
        ) : (
          <button onClick={() => void store.setStatus(c.id, 'open')}>
            <RotateCcw size={13} /> Reopen
          </button>
        )}
        <button onClick={() => void store.remove(c.id)} aria-label="Delete comment">
          <Trash2 size={13} /> Delete
        </button>
      </div>
    </li>
  );
}

/**
 * Comment box and thread for the item in the proof panel. Key it by item id so a new item
 * starts empty. Once the card is approved its comments are greyed out.
 */
export function CommentsPanel({ item, store, approved }: { item: Item; store: CommentStore; approved: boolean }) {
  const [text, setText] = useState('');
  const [quote, setQuote] = useState('');
  const mine = store.comments
    .filter((c) => c.itemId === item.id)
    .sort((a, b) => (a.status === b.status ? a.createdAt.localeCompare(b.createdAt) : a.status === 'open' ? -1 : 1));

  // Picks up text the reader deliberately highlights in the proof (a drag or a
  // keyboard selection that ends there), so a comment can point at a phrase.
  useEffect(() => {
    const capture = (event: Event) => {
      const stage = document.querySelector('.proof-stage');
      if (!stage || !(event.target instanceof Node) || !stage.contains(event.target)) return;
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed || !sel.anchorNode || !sel.focusNode) return;
      if (!stage.contains(sel.anchorNode) || !stage.contains(sel.focusNode)) return;
      const s = sel.toString().replace(/\s+/g, ' ').trim();
      if (s.length > 2) setQuote(s);
    };
    document.addEventListener('mouseup', capture);
    document.addEventListener('keyup', capture);
    return () => {
      document.removeEventListener('mouseup', capture);
      document.removeEventListener('keyup', capture);
    };
  }, [item.id]);

  const submit = async () => {
    if (!text.trim()) return;
    await store.add(item, text.trim(), quote);
    setText('');
    setQuote('');
  };

  return (
    <section className="comments-panel" aria-label="Review comments">
      <h3>
        <MessageSquare size={14} /> Review comments
        {mine.length > 0 && <small>{mine.filter((c) => c.status === 'open').length} open</small>}
      </h3>
      {mine.length > 0 && (
        <ul className="comment-thread">
          {mine.map((c) => (
            <CommentCard
              key={c.id}
              c={c}
              store={store}
              changed={c.revision !== item.revision}
              approved={approved}
            />
          ))}
        </ul>
      )}
      {quote && (
        <div className="comment-quote">
          <blockquote>{quote}</blockquote>
          <button onClick={() => setQuote('')} aria-label="Remove quoted text">
            Remove quote
          </button>
        </div>
      )}
      <label htmlFor="review-comment-text" className="sr-only">
        Add a review comment
      </label>
      <Textarea
        id="review-comment-text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="What should change? Highlight words in the proof to quote them."
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) void submit();
        }}
      />
      <div className="comment-submit">
        <span>
          {store.shared === false
            ? 'Saved in this browser only'
            : store.shared
              ? 'Saved to data/review-comments.json'
              : ''}
        </span>
        <Button variant="outline" onClick={() => void submit()} disabled={!text.trim()}>
          Add comment
        </Button>
      </div>
      {store.error && <p className="comment-error">{store.error}</p>}
    </section>
  );
}

/**
 * Every comment across the studio, with a jump to each item: open comments first, then
 * those on cards since approved (greyed out), then resolved ones.
 */
export function CommentsList({
  store,
  items,
  approvedIds,
  onOpen,
}: {
  store: CommentStore;
  items: Item[];
  approvedIds: Set<string>;
  onOpen: (itemId: string) => void;
}) {
  const [showResolved, setShowResolved] = useState(false);
  const revisions = new Map(items.map((i) => [i.id, i.revision]));
  const rank = (c: ReviewComment) => (c.status === 'resolved' ? 2 : approvedIds.has(c.itemId) ? 1 : 0);
  const list = store.comments
    .filter((c) => showResolved || c.status === 'open')
    .sort((a, b) => rank(a) - rank(b) || b.createdAt.localeCompare(a.createdAt));
  const open = store.comments.filter((c) => c.status === 'open');
  const onApproved = open.filter((c) => approvedIds.has(c.itemId)).length;
  const resolvedCount = store.comments.length - open.length;
  return (
    <div className="comments-list">
      <div className="comments-list-head">
        <span>
          {open.length - onApproved} open{onApproved > 0 && ` · ${onApproved} on approved cards`} · {resolvedCount}{' '}
          resolved
        </span>
        {resolvedCount > 0 && (
          <label>
            <input type="checkbox" checked={showResolved} onChange={(e) => setShowResolved(e.target.checked)} /> Show
            resolved
          </label>
        )}
      </div>
      {list.length ? (
        <ul className="comment-thread">
          {list.map((c) => (
            <CommentCard
              key={c.id}
              c={c}
              store={store}
              changed={revisions.has(c.itemId) && revisions.get(c.itemId) !== c.revision}
              approved={approvedIds.has(c.itemId)}
              onOpen={() => onOpen(c.itemId)}
            />
          ))}
        </ul>
      ) : (
        <p className="muted">No open comments. Add one from the proof panel of any handout.</p>
      )}
      {store.error && <p className="comment-error">{store.error}</p>}
    </div>
  );
}
