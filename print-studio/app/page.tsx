'use client';
import { useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  ScanLine,
  IdCard,
  LockKeyhole,
  Armchair,
  PencilLine,
  ClipboardList,
  Search,
  Download,
  Check,
  ChevronRight,
  Palette,
  Printer,
  X,
  Eye,
  CheckCircle2,
  Circle,
  ArrowUpRight,
  PackageCheck,
  RotateCcw,
  RefreshCw,
  MessageSquare,
  Mail,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  CommentsList,
  CommentsPanel,
  useReviewComments,
} from '@/components/review-comments';
import {
  useSharedReviews,
  type ReviewStatus,
  type Reviews,
} from '@/components/review-status';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
} from '@/components/ui/sidebar';
import data from '@/lib/event.json';
import {
  defaultBrand,
  type Brand,
  type Category,
  type Item,
} from '@/lib/types';

const items = data.items as Item[];
const categories = [
  {
    id: 'clues',
    name: 'Clue cards',
    icon: BookOpen,
    desc: 'Approved clues, organised for each round.',
  },
  {
    id: 'badges',
    name: 'Name badges',
    icon: IdCard,
    desc: '90 × 56 mm badges · Eight per A4 sheet, with crop marks.',
  },
  {
    id: 'evidence',
    name: 'Evidence',
    icon: ScanLine,
    desc: 'Photographs, anonymous slips, the journey note and one laboratory report.',
  },
  {
    id: 'private',
    name: 'Private & performer',
    icon: LockKeyhole,
    desc: 'Separate instructions, kept private until their cues.',
  },
  {
    id: 'seating',
    name: 'Seating & place cards',
    icon: Armchair,
    desc: `A seating plan for the hotel and guests, ${data.validation.seats} place cards and ${data.validation.tables} table signs.`,
  },
  {
    id: 'stationery',
    name: 'Slips & notes',
    icon: PencilLine,
    desc: 'Accusation slips for each guest\u2019s own conclusion, A5 private notes, and pre-filled question notes for cross-table conversations. Two notes per landscape A4 sheet.',
  },
  {
    id: 'labels',
    name: 'Envelope labels',
    icon: Mail,
    desc: `One label per clue, ${data.items.filter((i) => i.template === 'label').length} in all · Avery J8161, 63.5 × 46.6 mm, eighteen per sheet, a fresh sheet for each round. Also the A4 table-envelope fronts for Rounds 2 and 3, printed on A4 and stuck on.`,
  },
  {
    id: 'gm',
    name: 'GM reference pack',
    icon: ClipboardList,
    desc: 'Release dividers, running order and preparation notes.',
  },
] as const;
function Choice({
  value,
  onChange,
  options,
  label,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  label: string;
}) {
  return (
    <Select value={value} onValueChange={(v) => onChange(String(v))}>
      <SelectTrigger aria-label={label} className="choice">
        <SelectValue>
          {options.find((o) => o.value === value)?.label}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
function Proof({ item, brand }: { item: Item; brand: Brand }) {
  const evidence = ['slip', 'taxi', 'report'].includes(item.template);
  const shortMenuChoice = (value?: string) =>
    (value || 'Not supplied')
      .replace(/\s+[–-]\s+.*$/, '')
      .replace(/\s*\([^)]*\)\s*$/, '')
      .replace(/\s*&\s*Pineapple Compote.*$/, '')
      .trim();
  const menuLines =
    item.menu?.missing === true
      ? ['Menu choices to confirm']
      : [
          `Starter: ${shortMenuChoice(item.menu?.starter)}`,
          `Main: ${shortMenuChoice(item.menu?.main)}`,
          `Dessert: ${shortMenuChoice(item.menu?.dessert)}`,
        ];
  return (
    <div
      className={`paper ${item.template} ${brand.inkSaver ? 'ink-saver' : ''}`}
      style={
        {
          '--print-accent': brand.inkSaver ? '#242326' : brand.color,
        } as React.CSSProperties
      }
    >
      {/* Pages that print their own wordmark do not want the panel's masthead as well. */}
      {!evidence && !['place', 'table', 'table-plan', 'room-plan'].includes(item.template) && (
        <div className="paper-masthead">
          <strong>{brand.name}</strong>
          {item.round !== null && (
            <span>{item.private ? 'PRIVATE' : `ROUND ${item.round}`}</span>
          )}
        </div>
      )}
      {item.template === 'label' ? (
        // Show the sticker at its real proportions rather than falling back to the item text.
        <div className="sticker">
          <strong className="sticker-brand">{brand.name}</strong>
          <span className="sticker-round">ROUND {item.round}</span>
          <span className="sticker-name">{item.guest}</span>
          <span className="sticker-character">{item.character}</span>
          <span className="sticker-table">Table {item.table}</span>
        </div>
      ) : item.template === 'table-plan' && item.tablePlan ? (
        (() => {
          // Show the guest sheet as it prints: wordmark, the little floor plan, then the tables.
          const plan = item.tablePlan;
          const xs = plan.outline.map((q) => q[0]);
          const ys = plan.outline.map((q) => q[1]);
          const [minX, minY] = [Math.min(...xs) - 0.8, Math.min(...ys) - 0.8];
          const [w, h] = [Math.max(...xs) + 0.8 - minX, Math.max(...ys) + 0.8 - minY];
          const list = (numbers: number[]) =>
            numbers.length === 1
              ? `Table ${numbers[0]}`
              : `Tables ${numbers.slice(0, -1).join(', ')} and ${numbers[numbers.length - 1]}`;
          return (
            <>
              <h3 className="guest-plan-brand">{brand.name}</h3>
              <p className="seating-subtitle">{brand.subtitle}</p>
              <h3>Find your table</h3>
              <div className="guest-plan-head">
                <svg viewBox={`${minX} ${minY} ${w} ${h}`} className="guest-plan-svg" role="img"
                  aria-label="Plan of the two rooms with the tables numbered">
                  <polygon points={plan.outline.map((q) => q.join(',')).join(' ')}
                    fill="#f8f1f3" stroke="#d6c4ca" strokeWidth={0.08} />
                  {plan.tables.map((t) => (
                    <g key={t.number}>
                      <circle cx={t.x} cy={t.y} r={0.78} fill="#fff" stroke="#d6c4ca" strokeWidth={0.07} />
                      <text x={t.x} y={t.y} textAnchor="middle" dominantBaseline="central"
                        fontSize={0.8} fontWeight="700" fill="#242326">{t.number}</text>
                    </g>
                  ))}
                </svg>
                <div>
                  {Object.entries(plan.rooms)
                    .filter(([key]) => (plan.roomTables[key] ?? []).length > 0)
                    .map(([key, room]) => (
                      <div key={key} className="guest-plan-room">
                        <strong>{room.name}</strong>
                        <span>{list(plan.roomTables[key])}</span>
                        {room.caption && <em>{room.caption}</em>}
                      </div>
                    ))}
                </div>
              </div>
              <div className="seating-plan-grid">
                {plan.tables.map((t) => (
                  <section key={t.number}>
                    <h4>
                      Table {t.number}
                      <small>{plan.rooms[t.room].short ?? plan.rooms[t.room].name}</small>
                    </h4>
                    <ol className="guest-plan-names">
                      {t.guests.map((g) => (
                        <li key={g}>{g}</li>
                      ))}
                    </ol>
                  </section>
                ))}
              </div>
              <p className="seating-event">
                {plan.hosts} · {plan.date} · {plan.venue}
              </p>
            </>
          );
        })()
      ) : item.template === 'room-plan' && item.roomPlan ? (
        (() => {
          // Draw the floor the same way the PDF does, so the panel shows the page rather than
          // falling back to its text. Metres map straight onto the SVG view box.
          const plan = item.roomPlan;
          const chair = plan.chairAllowance;
          const pad = Math.max(...plan.tables.map((t) => t.diameter / 2 + chair)) + 0.3;
          const xs = plan.outline.map((q) => q[0]);
          const ys = plan.outline.map((q) => q[1]);
          const [minX, minY] = [Math.min(...xs) - pad, Math.min(...ys) - pad];
          const [w, h] = [Math.max(...xs) + pad - minX, Math.max(...ys) + pad - minY];
          const seatAt = (cx: number, cy: number, r: number, angle: number) => {
            const rad = ((angle - 90) * Math.PI) / 180;
            return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
          };
          return (
            <>
              <h3>Proposed room layout and seating</h3>
              <p className="seating-event">
                {plan.tables.reduce((n, t) => n + t.seats.length, 0)} guests ·{' '}
                {plan.tables.length} round tables<br />{plan.date} · {plan.venue}
              </p>
              <p className="seating-subtitle">
                Top of plan — far wall of the beamed main room
              </p>
              <svg viewBox={`${minX} ${minY} ${w} ${h}`} className="room-plan-svg" role="img"
                aria-label="Room layout with every table and chair">
                <polygon
                  points={plan.outline.map((q) => q.join(',')).join(' ')}
                  fill="#f8f1f3" stroke="#d6c4ca" strokeWidth={0.06}
                />
                {plan.tables.map((t) => {
                  const top = t.diameter / 2;
                  const ring = top + chair;
                  return (
                    <g key={t.number}>
                      <circle cx={t.x} cy={t.y} r={ring} fill="#eef2f4" stroke="#e4dcdf" strokeWidth={0.04} />
                      <circle cx={t.x} cy={t.y} r={top} fill="#dfe7ea" stroke="#d6c4ca" strokeWidth={0.05} />
                      {t.seats.map((s) => {
                        const [sx, sy] = seatAt(t.x, t.y, (top + ring) / 2, s.angle);
                        return <circle key={s.seat} cx={sx} cy={sy} r={0.13} fill="#732b40" />;
                      })}
                      <text x={t.x} y={t.y} textAnchor="middle" dominantBaseline="central"
                        fontSize={0.62} fontWeight="700" fill="#242326">T{t.number}</text>
                    </g>
                  );
                })}
              </svg>
              <div className="seating-plan-grid">
                {Object.entries(plan.rooms)
                  .filter(([key]) => plan.tables.some((t) => t.room === key))
                  .map(([key, room]) => (
                    <section key={key}>
                      <h4>{room.name}</h4>
                      <ol>
                        {plan.tables.filter((t) => t.room === key).map((t) => (
                          <li key={t.number} value={t.number}>
                            <strong>Table {t.number}</strong>
                            <span>{t.diameter.toFixed(1)} m · {t.seats.length} guests</span>
                          </li>
                        ))}
                      </ol>
                    </section>
                  ))}
              </div>
              {/* The document carries a page per table, so the preview shows them too. */}
              {[...plan.tables].sort((x, y) => x.number - y.number).map((t) => {
                const top = t.diameter / 2;
                const ring = top + chair;
                // The labels sit outside the chair ring, so the view box has to allow for the
                // longest of them or the names are clipped at the panel edge.
                const longest = Math.max(
                  ...t.seats.flatMap((s) => [s.guest.length, s.character.length]),
                );
                const span = (ring + 0.7 + longest * 0.19) * 2;
                return (
                  <div key={t.number} className="table-diagram">
                    <h4>
                      Table {t.number}
                      <small>{plan.rooms[t.room].name} · {t.seats.length} guests</small>
                    </h4>
                    <svg
                      viewBox={`${-span / 2} ${-span / 2} ${span} ${span}`}
                      className="table-diagram-svg"
                      role="img"
                      aria-label={`Table ${t.number} with every chair placed`}
                    >
                      <circle cx={0} cy={0} r={ring} fill="#f4f7f8" stroke="#e4dcdf" strokeWidth={0.03} />
                      <circle cx={0} cy={0} r={top} fill="#dfe7ea" stroke="#c9c4c6" strokeWidth={0.04} />
                      <line x1={0} y1={-ring - 0.25} x2={0} y2={-ring - 0.75}
                        stroke="#732b40" strokeWidth={0.06} />
                      {t.seats.map((s) => {
                        const [sx, sy] = seatAt(0, 0, (top + ring) / 2, s.angle);
                        const [lx, ly] = seatAt(0, 0, ring + 0.62, s.angle);
                        const anchor = lx < -0.08 ? 'end' : lx > 0.08 ? 'start' : 'middle';
                        return (
                          <g key={s.seat}>
                            <circle cx={sx} cy={sy} r={0.26} fill="#fff" stroke="#732b40" strokeWidth={0.04} />
                            <text x={sx} y={sy} textAnchor="middle" dominantBaseline="central"
                              fontSize={0.3} fontWeight="700" fill="#732b40">{s.seat}</text>
                            <text x={lx} y={ly} textAnchor={anchor} dominantBaseline="central"
                              fontSize={0.33} fontWeight="700" fill="#242326">{s.guest}</text>
                            <text x={lx} y={ly + 0.4} textAnchor={anchor} dominantBaseline="central"
                              fontSize={0.27} fill="#6a5960">{s.character}</text>
                          </g>
                        );
                      })}
                    </svg>
                  </div>
                );
              })}
            </>
          );
        })()
      ) : item.template === 'seating-plan' && item.seatingPlan ? (
        <>
          <h3>Seating plan</h3>
          <p className="seating-event">{item.seatingPlan.hosts}<br />{item.seatingPlan.date} · {item.seatingPlan.venue}</p>
          <p className="seating-subtitle">{brand.subtitle}</p>
          <div className="seating-plan-grid">
            {item.seatingPlan.tables.map((table) => (
              <section key={table.number}>
                <h4>Table {table.number}<small>{table.seats.length} guests</small></h4>
                <ol>
                  {table.seats.map((seat) => (
                    <li key={seat.seat} value={seat.seat}>
                      <strong>{seat.guest}</strong>
                      <span>{seat.character}</span>
                    </li>
                  ))}
                </ol>
              </section>
            ))}
          </div>
          <p className="seating-event">Numbers beside names show seat order.</p>
        </>
      ) : ['badge', 'place'].includes(item.template) ? (
        <>
          {item.template === 'place' && (
            <div className="place-reverse">
              <strong>{brand.name}</strong>
              {menuLines.map((line) => (
                <span key={line}>{line}</span>
              ))}
              {item.hasFoodIntolerance && item.dietaryNote && (
                <b>DIET: {item.dietaryNote}</b>
              )}
            </div>
          )}
          <div className="badge-name">{item.character}</div>
          {item.template === 'badge' && item.description && (
            <p className="badge-description">{item.description}</p>
          )}
          <div className="badge-bottom">
            <span>
              {item.template === 'place' && item.hasFoodIntolerance && (
                <b className="diet-flag">DIET</b>
              )}
              {item.guest}
            </span>
            <b>T{item.table}</b>
          </div>
          {item.template === 'place' && (
            <div className="paper-masthead place-brand-footer">
              <strong>{brand.name}</strong>
            </div>
          )}
        </>
      ) : item.template === 'table' ? (
        <div className="table-sign-sheet" aria-label={`Table ${item.table}: A4 sheet, fold across the centre into A5`}>
          {['back', 'front'].map((side) => (
            <div className={`table-sign table-sign-${side}`} key={side}>
              <b className="table-sign-brand">{brand.name}</b>
              <strong>TABLE {item.table}</strong>
              <div className="table-sign-guests" style={{ gridTemplateRows: `repeat(${Math.ceil((item.tableGuests?.length ?? 0) / 2)}, 1fr)` }}>
                {item.tableGuests?.map((guest) => (
                  <div key={guest.guest}>
                    <b>{guest.character}</b>
                    <span>({guest.guest})</span>
                    <em>{guest.flags.join(' · ')}</em>
                  </div>
                ))}
              </div>
              <p>{brand.subtitle}</p>
              <small>GF = gluten free · V = vegetarian · PESC = pescatarian</small>
            </div>
          ))}
        </div>
      ) : item.template === 'photo' || item.template === 'money' ? (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="paper-photo" src={item.image} alt={item.title} />
          <p className="photo-caption">{item.content}</p>
        </>
      ) : item.template === 'qnote' ? (
        <>
          <div className="qnote-head">
            <span>A note · Round {item.round}</span>
            <b>{item.title}</b>
          </div>
          <p className="qnote-to">
            <span>To:</span> <b>{item.toCharacter}</b> / Table {item.toTable}
          </p>
          <p className="qnote-to">
            <span>From:</span> {item.character} / Table {item.table}
          </p>
          <p className="qnote-draft">{item.content}</p>
          <div className="rule" />
          <div className="rule" />
          <p className="message-label">Reply</p>
          <div className="note-lines">
            {Array.from({ length: 7 }, (_, i) => (
              <div className="rule" key={i} />
            ))}
          </div>
          <p className="qnote-foot">
            You can ask face to face, or send this note; the reply comes back on
            it.
          </p>
        </>
      ) : item.template === 'ballot' ? (
        <>
          <h3>Who do you think did the murder?</h3>
          <p>
            What was the motive, means and opportunity? Fill in and discuss on
            your table.
          </p>
          <p>I accuse:</p>
          <div className="rule" />
          {[
            ['Motive', 'why they wanted him dead'],
            ['Means', 'what they used, and how they got it'],
            ['Opportunity', 'how they could have done it: were they near?'],
          ].map(([label, hint]) => (
            <div key={label}>
              <p className="message-label">
                {label} <small>{hint}</small>
              </p>
              <div className="rule" />
              <div className="rule" />
            </div>
          ))}
        </>
      ) : item.template === 'note' ? (
        <>
          <h3>A private note</h3>
          <p>To:</p>
          <div className="rule" />
          <p>From:</p>
          <div className="rule" />
          <p className="message-label">Message</p>
          <div className="note-lines">
            {Array.from({ length: 10 }, (_, i) => (
              <div className="rule" key={i} />
            ))}
          </div>
        </>
      ) : (
        <>
          {!evidence && (
            <>
              <h3>{item.character || 'Game Master'}</h3>
              {item.guest && (
                <div className="paper-recipient">
                  {item.guest}
                  {item.table && (
                    <>
                      {' '}
                      <span>/</span> Table {item.table}
                    </>
                  )}
                </div>
              )}
              <h4>{item.title}</h4>
            </>
          )}
          {item.template === 'taxi' && <h4>DRIVER’S JOURNEY NOTE</h4>}
          <div className="paper-copy">{item.content}</div>
          {!evidence && (
            <div className="paper-id">
              {item.id}
              {item.noteKey && <b className="paper-note-key">Note {item.noteKey}</b>}
            </div>
          )}
        </>
      )}
    </div>
  );
}
export default function Studio() {
  const [category, setCategory] = useState<Category>('clues'),
    [query, setQuery] = useState(''),
    [round, setRound] = useState('all'),
    [table, setTable] = useState('all'),
    [reviewFilter, setReviewFilter] = useState('all');
  const [selected, setSelected] = useState<Set<string>>(new Set()),
    [activeId, setActiveId] = useState(
      items.find((i) => i.category === 'clues')!.id,
    );
  const [reviews, setReviews] = useState<Reviews>({}),
    [quantities, setQuantities] = useState<Record<string, number>>({}),
    [brand, setBrand] = useState<Brand>(defaultBrand);
  const [ready, setReady] = useState(false),
    [storageWarning, setStorageWarning] = useState(''),
    [dialog, setDialog] = useState<
      'brand' | 'pack' | 'source' | 'comments' | null
    >(null),
    [sort, setSort] = useState('round'),
    [fullPage, setFullPage] = useState(false);
  const [busy, setBusy] = useState(false),
    [message, setMessage] = useState(''),
    [pdfUrl, setPdfUrl] = useState('');
  const comments = useReviewComments();
  const openComments = (id: string) =>
    comments.comments.filter((c) => c.itemId === id && c.status === 'open').length;
  const sharedReviews = useSharedReviews(reviews, setReviews, ready, comments);
  useEffect(() => {
    // Load browser-only state after the first server-matched render.
    const hydrationTimer = window.setTimeout(() => {
      try {
        const reloadMessage = sessionStorage.getItem(
          'valemeridian-database-reload-message',
        );
        if (reloadMessage) {
          setMessage(reloadMessage);
          sessionStorage.removeItem('valemeridian-database-reload-message');
        }
        const raw = localStorage.getItem('valemeridian-print-studio-v1');
        if (raw) {
          const saved = JSON.parse(raw);
          setBrand({ ...defaultBrand, ...saved.brand });
          setReviews(saved.reviews ?? {});
          setQuantities(saved.quantities ?? {});
          setSelected(
            new Set(
              (saved.selected ?? []).filter((id: string) =>
                items.some((i) => i.id === id),
              ),
            ),
          );
        }
      } catch {
        setStorageWarning(
          'Browser storage is unavailable. Download your review record to keep your work.',
        );
      }
      setReady(true);
    }, 0);
    return () => window.clearTimeout(hydrationTimer);
  }, []);
  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(
        'valemeridian-print-studio-v1',
        JSON.stringify({ brand, reviews, quantities, selected: [...selected] }),
      );
    } catch {
      queueMicrotask(() =>
        setStorageWarning('Changes could not be saved in this browser.'),
      );
    }
  }, [brand, reviews, quantities, selected, ready]);
  useEffect(
    () => () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    },
    [pdfUrl],
  );
  // A review only counts for the revision it was given to; older records with no status
  // are converted by useSharedReviews once the comments have loaded.
  const reviewState = (i: Item): ReviewStatus | null =>
    reviews[i.id]?.revision === i.revision
      ? (reviews[i.id].status ?? 'reviewed')
      : null;
  const reviewed = (i: Item) => reviewState(i) !== null;
  const approved = (i: Item) => reviewState(i) === 'approved';
  const approvedIds = new Set(items.filter(approved).map((i) => i.id));
  const current = categories.find((c) => c.id === category)!;
  const filtered = useMemo(
    () =>
      items.filter(
        (i) =>
          i.category === category &&
          (round === 'all' || String(i.round) === round) &&
          (table === 'all' || String(i.table) === table) &&
          (reviewFilter === 'all' ||
            (reviews[i.id]?.revision === i.revision
              ? (reviews[i.id].status ?? 'reviewed')
              : 'unreviewed') === reviewFilter) &&
          [i.title, i.character, i.guest, i.id, i.content]
            .join(' ')
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [category, round, table, reviewFilter, query, reviews],
  );
  const active = items.find((i) => i.id === activeId)!;
  const selectedItems = items
    .filter((i) => selected.has(i.id))
    .map((i) => ({ ...i, quantity: quantities[i.id] ?? i.quantity }));
  const approvedCount = items.filter(approved).length,
    reviewedOnlyCount = items.filter(
      (i) => reviewState(i) === 'reviewed',
    ).length,
    pieceCount = selectedItems.reduce((n, i) => n + i.quantity, 0);
  const toggle = (id: string) =>
    setSelected((old) => {
      const next = new Set(old);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  function navigate(id: Category) {
    setCategory(id);
    setRound('all');
    setTable('all');
    setQuery('');
    setReviewFilter('all');
    setActiveId(items.find((i) => i.category === id)!.id);
  }
  function openItem(id: string) {
    const item = items.find((i) => i.id === id);
    if (!item) return;
    navigate(item.category);
    setActiveId(id);
    setDialog(null);
  }
  function downloadFile(blob: Blob, name: string) {
    const url = URL.createObjectURL(blob),
      a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  async function reloadFromDatabase() {
    setBusy(true);
    setMessage('Checking the latest local database…');
    try {
      const response = await fetch('/api/reload-data', { method: 'POST' });
      const result = (await response.json()) as {
        message?: string;
        details?: string;
      };
      if (!response.ok) {
        throw new Error(result.details || result.message || 'Reload failed.');
      }
      sessionStorage.setItem(
        'valemeridian-database-reload-message',
        result.message || 'Reloaded and verified the latest local database.',
      );
      window.location.reload();
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'The latest database could not be loaded.',
      );
      setBusy(false);
    }
  }
  async function generate(list: Item[], preview = false, sortOverride?: string) {
    setBusy(true);
    setMessage('');
    try {
      const needsPictures = list.some((i) => ['photo', 'money'].includes(i.template));
      const [{ makePdf }, { default: fonts }, pictures] = await Promise.all([
        import('@/lib/pdf.mjs'),
        import('@/lib/fonts.json'),
        needsPictures
          ? import('@/lib/photos.json').then((m) => m.default)
          : Promise.resolve({}),
      ]);
      // The Vale Meridian logo artwork for clue cards, envelopes, question notes and table signs.
      const logo = list.some((i) => ['card', 'divider', 'envelope', 'table-envelope', 'qnote', 'table'].includes(i.template))
        ? await fetch('/valemeridian-logo.png')
            .then((r) => r.blob())
            .then((b) => new Promise<string>((done) => {
              const reader = new FileReader();
              reader.onload = () => done(String(reader.result));
              reader.readAsDataURL(b);
            }))
        : undefined;
      const result = makePdf(list, fonts, {
        logo,
        images: pictures,
        brand,
        event: data.event,
        sort: sortOverride ?? sort,
        fullPage,
        manifest: !preview && !list.every((i) => i.template === 'seating-plan'),
        snapshotId: data.source.databaseHash.slice(0, 8),
      });
      const blob = result.doc.output('blob');
      if (preview) setPdfUrl(URL.createObjectURL(blob));
      else {
        downloadFile(
          blob,
          `valemeridian-${list.length === 1 ? list[0].id : 'print-pack'}.pdf`,
        );
        setMessage(
          list.every((i) => i.template === 'seating-plan')
            ? `Seating plan downloaded: ${result.printPages} landscape A4 sheet${result.printPages === 1 ? '' : 's'}, ready for the hotel and guests.`
            : `PDF downloaded: ${result.printPages} print pages, plus the packing checklist.`,
        );
      }
    } catch (e) {
      setMessage(
        e instanceof Error ? e.message : 'The PDF could not be generated.',
      );
    } finally {
      setBusy(false);
    }
  }
  function reviewActive(status: ReviewStatus) {
    sharedReviews.set(active.id, {
      revision: active.revision,
      at: new Date().toISOString(),
      status,
    });
    const next = filtered.find(
      (i, index) =>
        index > filtered.findIndex((x) => x.id === active.id) && !reviewed(i),
    );
    if (next) setActiveId(next.id);
  }
  return (
    <SidebarProvider
      style={{ '--sidebar-width': '244px' } as React.CSSProperties}
    >
      <Sidebar className="studio-sidebar" collapsible="offcanvas">
        <SidebarHeader className="studio-logo">
          <div className="brand-symbol">
            V<span>V</span>
          </div>
          <div>
            <strong>VALE MERIDIAN</strong>
            <span>PRINT STUDIO</span>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <div className="nav-caption">PRINT LIBRARY</div>
          <SidebarMenu>
            {categories.map((c) => (
              <SidebarMenuItem key={c.id}>
                <SidebarMenuButton
                  isActive={category === c.id}
                  onClick={() => navigate(c.id)}
                  className="nav-item"
                >
                  <c.icon size={18} />
                  <span>{c.name}</span>
                  <small>
                    {items.filter((i) => i.category === c.id).length}
                  </small>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
          <div className="nav-caption tools-caption">WORKSPACE</div>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => setDialog('brand')}
                className="nav-item"
              >
                <Palette size={18} />
                <span>Brand & print settings</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => setDialog('source')}
                className="nav-item"
              >
                <PackageCheck size={18} />
                <span>Source & preparation</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                onClick={() => setDialog('comments')}
                className="nav-item"
              >
                <MessageSquare size={18} />
                <span>Review comments</span>
                <small>
                  {
                    comments.comments.filter(
                      (c) => c.status === 'open' && !approvedIds.has(c.itemId),
                    ).length
                  }
                </small>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarContent>
        <SidebarFooter>
          <div className="event-stamp">
            <span>{data.event.hosts.toUpperCase()}</span>
            <strong>{data.event.date}</strong>
            <p>{data.event.venue}</p>
          </div>
          <button className="snapshot-link" onClick={() => setDialog('source')}>
            <span className="status-dot" /> Saved print snapshot{' '}
            <ChevronRight size={14} />
          </button>
        </SidebarFooter>
      </Sidebar>
      <main className="studio-main">
        <header className="topbar">
          <div>
            <SidebarTrigger className="mobile-menu" />
            <span>Vale Meridian gala</span>
            <ChevronRight size={14} />
            <strong>Print preparation</strong>
          </div>
          <button className="host-label" onClick={() => setDialog('source')}>
            <LockKeyhole size={14} /> Host workspace
          </button>
        </header>
        <div className="workspace-heading">
          <div>
            <div className="eyebrow">THE PRINT LIBRARY</div>
            <h1>{current.name}</h1>
            <p>{current.desc}</p>
          </div>
          <div className="heading-actions">
            {category === 'seating' && (
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => generate([{ ...items.find((i) => i.id === 'seating-plan')!, quantity: 1 }])}
              >
                <Download size={17} /> Download seating plan
              </Button>
            )}
            {category === 'clues' &&
              // One round at a time, in the same order as the printed clue envelopes (by table,
              // then character), so each card goes straight into its envelope.
              [0, 1, 2, 3].map((r) => (
                <Button
                  key={r}
                  variant="outline"
                  disabled={busy}
                  title={`All round ${r} clue cards, in envelope order`}
                  onClick={() =>
                    generate(
                      items
                        .filter((i) => i.category === 'clues' && i.round === r)
                        .map((i) => ({ ...i, quantity: 1 })),
                      false,
                      'table',
                    )
                  }
                >
                  <Download size={17} /> Round {r}
                </Button>
              ))}
            {category === 'badges' && (
              <Button
                variant="outline"
                disabled={busy || !filtered.length}
                onClick={() =>
                  generate(
                    filtered.map((i) => ({
                      ...i,
                      quantity: quantities[i.id] ?? i.quantity,
                    })),
                  )
                }
              >
                <Download size={17} /> Download badge sheets
              </Button>
            )}
            <Button
              className="primary-button"
              onClick={() => setDialog('pack')}
              disabled={!selected.size}
            >
              <Printer size={17} /> Prepare print pack{' '}
              <span className="button-count">{selected.size}</span>
            </Button>
          </div>
        </div>
        <div className="summary-strip">
          <div>
            <strong>{data.source.clueCount}</strong>
            <span>master records</span>
          </div>
          <div>
            <strong>
              {approvedCount}
              <small> / {items.length}</small>
            </strong>
            <span>
              approved
              {reviewedOnlyCount > 0 &&
                ` · ${reviewedOnlyCount} reviewed, not approved`}
              {sharedReviews.shared === false && ' (this browser)'}
            </span>
          </div>
          <div>
            <strong>{pieceCount}</strong>
            <span>pieces in print selection</span>
          </div>
          <button onClick={() => setDialog('source')}>
            <CheckCircle2 size={16} />
            <span>Clue wording checked against master</span>
            <ArrowUpRight size={15} />
          </button>
        </div>
        {storageWarning && <div className="notice">{storageWarning}</div>}
        {message && (
          <output className="notice">
            {message}
            <button
              aria-label="Dismiss notification"
              onClick={() => setMessage('')}
            >
              <X size={16} />
            </button>
          </output>
        )}
        <div className="work-surface">
          <section className="library">
            <div className="filters">
              <div className="search">
                <Search size={17} />
                <Input
                  aria-label="Search handouts"
                  placeholder="Search name, character or clue…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <div className="filter-row">
                <Choice
                  label="Filter by round"
                  value={round}
                  onChange={setRound}
                  options={[
                    { value: 'all', label: 'All rounds' },
                    ...[0, 1, 2, 3, 4].map((v) => ({
                      value: String(v),
                      label: `Round ${v}`,
                    })),
                  ]}
                />
                <Choice
                  label="Filter by table"
                  value={table}
                  onChange={setTable}
                  options={[
                    { value: 'all', label: 'All tables' },
                    ...[1, 2, 3, 4, 5, 6, 7, 8].map((v) => ({
                      value: String(v),
                      label: `Table ${v}`,
                    })),
                  ]}
                />
                <Choice
                  label="Filter by review"
                  value={reviewFilter}
                  onChange={setReviewFilter}
                  options={[
                    { value: 'all', label: 'Any review status' },
                    { value: 'unreviewed', label: 'To review' },
                    { value: 'reviewed', label: 'Reviewed, not approved' },
                    { value: 'approved', label: 'Approved' },
                  ]}
                />
              </div>
            </div>
            <div className="list-caption">
              <label>
                <Checkbox
                  aria-label="Select all filtered items"
                  checked={
                    filtered.length > 0 &&
                    filtered.every((i) => selected.has(i.id))
                  }
                  onCheckedChange={(checked) =>
                    setSelected((old) => {
                      const next = new Set(old);
                      filtered.forEach((i) =>
                        checked ? next.add(i.id) : next.delete(i.id),
                      );
                      return next;
                    })
                  }
                />
                <span>{filtered.length} items</span>
              </label>
              <button onClick={() => setSelected(new Set())}>
                Clear print selection
              </button>
            </div>
            <div className="handout-list">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="check-cell">
                      <span className="sr-only">Select</span>
                    </TableHead>
                    <TableHead>HANDOUT / RECIPIENT</TableHead>
                    <TableHead className="round-cell">ROUND</TableHead>
                    <TableHead className="review-cell">REVIEW</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((i) => (
                    <TableRow
                      key={i.id}
                      data-active={active.id === i.id}
                      className="handout-row"
                    >
                      <TableCell className="check-cell">
                        <Checkbox
                          aria-label={`Add ${i.title} for ${i.character || 'GM'} to print selection`}
                          checked={selected.has(i.id)}
                          onCheckedChange={() => toggle(i.id)}
                        />
                      </TableCell>
                      <TableCell>
                        <button
                          className="item-open"
                          onClick={() => setActiveId(i.id)}
                        >
                          <strong>{i.character || i.title}</strong>
                          <span>
                            {i.guest
                              ? `${i.guest}${i.table ? ` · Table ${i.table}` : ''}`
                              : i.source}
                          </span>
                          {i.category === 'clues' && (
                            <>
                              <small>{i.title}</small>
                              <small className="item-clue-id">{i.id}</small>
                            </>
                          )}
                          {['photo', 'money'].includes(i.template) && <small>{i.title}</small>}
                          {i.template === 'qnote' && (
                            <small className="item-clue-id">
                              {i.title} → {i.toCharacter} · Table {i.toTable}
                            </small>
                          )}
                          {openComments(i.id) > 0 && (
                            <small
                              className={`item-comment-count${approved(i) ? ' on-approved' : ''}`}
                            >
                              <MessageSquare size={11} /> {openComments(i.id)}{' '}
                              open comment{openComments(i.id) === 1 ? '' : 's'}
                            </small>
                          )}
                        </button>
                      </TableCell>
                      <TableCell className="round-cell">
                        {i.round !== null ? (
                          <span className={`round-pill r${i.round}`}>
                            R{i.round}
                          </span>
                        ) : (
                          <span className="dim">—</span>
                        )}
                      </TableCell>
                      <TableCell className="review-cell">
                        <button
                          onClick={() => setActiveId(i.id)}
                          className={`${reviewState(i) ?? 'unreviewed'}-icon`}
                          aria-label={
                            approved(i)
                              ? 'Approved'
                              : reviewed(i)
                                ? 'Reviewed, not approved'
                                : 'To review'
                          }
                        >
                          {approved(i) ? (
                            <CheckCircle2 size={18} />
                          ) : reviewed(i) ? (
                            <Eye size={17} />
                          ) : (
                            <Circle size={17} />
                          )}
                        </button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {!filtered.length && (
              <div className="empty-state">
                <Search />
                <h3>No matching handouts</h3>
                <p>Try a different name or clear your filters.</p>
                <Button variant="outline" onClick={() => navigate(category)}>
                  Clear filters
                </Button>
              </div>
            )}
          </section>
          <aside className="proof-panel">
            <div className="proof-title">
              <span>HANDOUT PROOF</span>
              <span>
                {active.template === 'badge'
                  ? '90 × 56 mm · 8 per A4 sheet'
                  : active.template === 'note'
                    ? 'A5 · 2 per landscape A4 sheet'
                    : active.template === 'seating-plan'
                      ? 'Landscape A4 · all tables'
                    : active.template === 'room-plan'
                      ? 'Landscape A4 · room layout with chairs'
                    : active.template === 'table-plan'
                      ? 'Portrait A4 · guest handout'
                    : active.template === 'place'
                      ? '90 × 80 mm · fold'
                    : active.template === 'table'
                      ? 'A4 · fold in half to A5 · back upside down'
                      : active.template === 'ballot'
                        ? '90 × 80 mm · 6 per A4 sheet'
                      : 'A4 print layout'}
              </span>
            </div>
            <Tabs defaultValue="proof">
              <TabsList className="preview-tabs">
                <TabsTrigger value="proof">Preview</TabsTrigger>
                <TabsTrigger value="details">Details</TabsTrigger>
              </TabsList>
              <TabsContent value="proof">
                <div className="proof-stage">
                  <Proof item={active} brand={brand} />
                </div>
                <div className="preview-note">
                  Screen proof · Open the PDF to check exact page layout.
                </div>
              </TabsContent>
              <TabsContent value="details">
                <dl className="details">
                  <dt>Item reference</dt>
                  <dd>{active.id}</dd>
                  <dt>Source</dt>
                  <dd>{active.source}</dd>
                  <dt>Release</dt>
                  <dd>
                    {active.round !== null
                      ? `Round ${active.round}`
                      : 'Event stationery'}
                    {active.cue && ` · ${active.cue}`}
                  </dd>
                  <dt>Content revision</dt>
                  <dd>{active.revision}</dd>
                  <dt>Review</dt>
                  <dd>
                    {reviewed(active)
                      ? `${approved(active) ? 'Approved' : 'Reviewed, not approved'} ${new Date(reviews[active.id].at).toLocaleDateString('en-GB')}`
                      : 'Not yet reviewed'}
                  </dd>
                </dl>
              </TabsContent>
            </Tabs>
            {active.private && (
              <div className="private-note">
                <LockKeyhole size={15} />
                <span>
                  {active.cue ||
                    'Keep this item private until its release cue.'}
                </span>
              </div>
            )}
            {active.proof && (
              <div className="private-note">
                Newly typeset evidence: review against the prop specification.
              </div>
            )}
            <div className="proof-actions">
              <Button
                variant="outline"
                onClick={() =>
                  generate(
                    [
                      {
                        ...active,
                        quantity:
                          active.template === 'note'
                            ? 2
                            : active.template === 'ballot'
                              ? 6
                              : 1,
                      },
                    ],
                    true,
                  )
                }
                disabled={busy}
              >
                <Eye size={16} />{' '}
                {active.template === 'badge'
                  ? 'Preview this badge'
                  : active.template === 'note'
                    ? 'Preview note sheet'
                    : active.template === 'ballot'
                      ? 'Preview voting sheet'
                    : 'Open PDF proof'}
              </Button>
              <Button variant="outline" onClick={() => toggle(active.id)}>
                {selected.has(active.id) ? (
                  <Check size={16} />
                ) : (
                  <Printer size={16} />
                )}{' '}
                {selected.has(active.id)
                  ? 'In print pack'
                  : 'Add to print pack'}
              </Button>
              <Button
                className={`review-button${reviewState(active) === 'reviewed' ? ' is-set' : ''}`}
                onClick={() => reviewActive('reviewed')}
              >
                <Eye size={16} />
                {reviewState(active) === 'reviewed'
                  ? 'Reviewed · next'
                  : 'Mark reviewed & next'}
              </Button>
              <Button
                className={`approve-button${approved(active) ? ' is-set' : ''}`}
                onClick={() => reviewActive('approved')}
              >
                <CheckCircle2 size={16} />
                {approved(active) ? 'Approved · next' : 'Approve & next'}
              </Button>
            </div>
            {sharedReviews.error && (
              <p className="comment-error">{sharedReviews.error}</p>
            )}
            <CommentsPanel
              key={active.id}
              item={active}
              store={comments}
              approved={approved(active)}
            />
          </aside>
        </div>
      </main>
      <Dialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
      >
        <DialogContent className="studio-dialog">
          <DialogHeader>
            <DialogTitle>
              {dialog === 'brand'
                ? 'Brand & print settings'
                : dialog === 'pack'
                  ? 'Prepare your print pack'
                  : dialog === 'comments'
                    ? 'Review comments'
                    : 'Source & preparation'}
            </DialogTitle>
            <DialogDescription>
              {dialog === 'brand'
                ? 'Applies to event stationery and clue cards. Evidence keeps its own appearance.'
                : dialog === 'pack'
                  ? 'Export a PDF with a packing checklist. Print A4 at actual size, single-sided.'
                  : dialog === 'comments'
                    ? 'Notes on the wording of handouts. Open one to see the card it refers to.'
                    : 'A checked snapshot of the event, with local seating and preparation instructions.'}
            </DialogDescription>
          </DialogHeader>
          {dialog === 'brand' && (
            <div className="brand-settings">
              <label htmlFor="brand-name">
                Brand name
                <Input
                  id="brand-name"
                  maxLength={24}
                  value={brand.name}
                  onChange={(e) =>
                    setBrand((b) => ({ ...b, name: e.target.value }))
                  }
                />
              </label>
              <label htmlFor="brand-subtitle">
                Table-sign subtitle
                <Input
                  id="brand-subtitle"
                  maxLength={64}
                  value={brand.subtitle}
                  onChange={(e) =>
                    setBrand((b) => ({ ...b, subtitle: e.target.value }))
                  }
                />
              </label>
              <label>
                Accent colour
                <div className="colour-options">
                  {['#732b40', '#213c57', '#214d43', '#27242d'].map((color) => (
                    <button
                      key={color}
                      aria-label={`Use ${color}`}
                      aria-pressed={brand.color === color}
                      style={{ background: color }}
                      onClick={() => setBrand((b) => ({ ...b, color }))}
                    >
                      {brand.color === color && <Check size={18} />}
                    </button>
                  ))}
                  <input
                    type="color"
                    aria-label="Custom accent colour"
                    value={brand.color}
                    onChange={(e) =>
                      setBrand((b) => ({ ...b, color: e.target.value }))
                    }
                  />
                </div>
              </label>
              <label className="check-label">
                <Checkbox
                  checked={brand.inkSaver}
                  onCheckedChange={(v) =>
                    setBrand((b) => ({ ...b, inkSaver: Boolean(v) }))
                  }
                />{' '}
                Ink-saving black and white
              </label>
              <label className="check-label">
                <Checkbox
                  checked={brand.cutMarks}
                  onCheckedChange={(v) =>
                    setBrand((b) => ({ ...b, cutMarks: Boolean(v) }))
                  }
                />{' '}
                Include crop marks
              </label>
              <Button variant="outline" onClick={() => setBrand(defaultBrand)}>
                <RotateCcw size={15} /> Restore Vale Meridian style
              </Button>
              <p className="muted">
                Saved in this browser. Approved clue wording is unchanged.
              </p>
            </div>
          )}
          {dialog === 'pack' && (
            <>
              <div className="pack-summary">
                <Printer />
                <strong>
                  {selected.size} entries{' '}
                  <span>/ {pieceCount} printed pieces</span>
                </strong>
              </div>
              <p className="muted">
                {selectedItems.filter((i) => !approved(i)).length} selected
                entries not yet approved. Private material and different rounds
                start on separate sheets.
              </p>
              <div className="pack-list">
                {selectedItems.map((i) => (
                  <div key={i.id}>
                    <div>
                      <strong>{i.title}</strong>
                      <span>
                        {i.guest || i.character || i.category}
                        {i.private ? ' · PRIVATE' : ''}
                      </span>
                    </div>
                    <label>
                      <span className="sr-only">Copies of {i.title}</span>
                      <Input
                        type="number"
                        min={1}
                        max={500}
                        value={i.quantity}
                        onChange={(e) =>
                          setQuantities((old) => ({
                            ...old,
                            [i.id]: Number(e.target.value),
                          }))
                        }
                      />
                    </label>
                    <button
                      aria-label={`Remove ${i.title}`}
                      onClick={() => toggle(i.id)}
                    >
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
              <Choice
                label="Print sort order"
                value={sort}
                onChange={setSort}
                options={[
                  { value: 'round', label: 'Sort by round, then table' },
                  { value: 'table', label: 'Sort by table, then round' },
                  { value: 'guest', label: 'Sort by guest, then round' },
                ]}
              />
              <label className="check-label">
                <Checkbox
                  checked={fullPage}
                  onCheckedChange={(v) => setFullPage(Boolean(v))}
                />{' '}
                Full-page clue cards (more room)
              </label>
              <div className="dialog-actions">
                <Button
                  variant="outline"
                  disabled={busy || !selected.size}
                  onClick={() => generate(selectedItems, true)}
                >
                  <Eye size={16} /> PDF proof
                </Button>
                <Button
                  className="primary-button"
                  disabled={busy || !selected.size}
                  onClick={() => generate(selectedItems)}
                >
                  <Download size={16} />
                  {busy ? 'Preparing…' : 'Download PDF pack'}
                </Button>
              </div>
              {message && <output className="notice">{message}</output>}
            </>
          )}
          {dialog === 'comments' && (
            <CommentsList
              store={comments}
              items={items}
              approvedIds={approvedIds}
              onOpen={openItem}
            />
          )}
          {dialog === 'source' && (
            <div className="source-panel">
              <div className="source-check">
                <CheckCircle2 />
                <strong>{data.source.clueCount} active clue records checked</strong>
              </div>
              <Button
                className="primary-button"
                disabled={busy}
                onClick={reloadFromDatabase}
              >
                <RefreshCw size={16} className={busy ? 'spin' : undefined} />
                {busy ? 'Reloading database…' : 'Reload from database'}
              </Button>
              <p className="muted">
                Reads the latest local SQLite database, rebuilds the print data,
                and verifies every active clue before refreshing this page.
              </p>
              <p>{data.source.description}</p>
              <p>{data.source.refresh}</p>
              <dl className="details">
                <dt>Snapshot captured</dt>
                <dd>
                  {new Date(data.source.capturedAt).toLocaleString('en-GB')}
                </dd>
                <dt>Approved seating</dt>
                <dd>
                  {data.validation.guests} attendees, including{' '}
                  {data.validation.provisional} provisional ·{' '}
                  {data.validation.seats} seated across {data.validation.tables}{' '}
                  tables
                </dd>
                <dt>Badge handling</dt>
                <dd>
                  {data.validation.badges} badges: Vincent and Peter have
                  separate badges for one performer. Peter’s identity is
                  withheld from the arrival place card.
                </dd>
              </dl>
              {data.unallocatedCharacters.length > 0 && (
                <p className="notice">
                  Unallocated: {data.unallocatedCharacters.join(', ')}.
                  Character cards remain available for a replacement player.
                </p>
              )}
              {data.pendingGuests.length > 0 && (
                <p className="notice">
                  Awaiting characters and seats: {data.pendingGuests.join(', ')}
                  . Their badges and place cards will be available once
                  allocated.
                </p>
              )}
              <h3>Physical preparation</h3>
              <p>{data.preparationNote}</p>
              <Button
                variant="outline"
                disabled={busy}
                onClick={() =>
                  generate(
                    items.filter(
                      (i) => i.id === 'reference-physical-props-2026-09-09',
                    ),
                  )
                }
              >
                <Download size={16} /> Download physical checklist
              </Button>
              {Array.from(new Set(data.preparation.map((p) => p.section))).map(
                (section) => (
                  <section key={section}>
                    <h3>{section}</h3>
                    {data.preparation
                      .filter((p) => p.section === section)
                      .map((p) => (
                        <div className="prep-item" key={p.title}>
                          <strong>
                            {p.title} <small>{p.status}</small>
                          </strong>
                          <p>
                            {p.quantity} · {p.owner} · {p.when}
                          </p>
                          <p>{p.detail}</p>
                        </div>
                      ))}
                  </section>
                ),
              )}
              {message && <output className="notice">{message}</output>}
              <Button
                variant="outline"
                onClick={() =>
                  downloadFile(
                    new Blob(
                      [
                        JSON.stringify(
                          {
                            snapshot: data.source,
                            brand,
                            reviews,
                            quantities,
                            selected: [...selected],
                          },
                          null,
                          2,
                        ),
                      ],
                      { type: 'application/json' },
                    ),
                    'valemeridian-review-record.json',
                  )
                }
              >
                <Download size={16} /> Download review record
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
      <Dialog open={!!pdfUrl} onOpenChange={(open) => !open && setPdfUrl('')}>
        <DialogContent className="pdf-dialog">
          <DialogHeader>
            <DialogTitle>Print proof</DialogTitle>
            <DialogDescription>
              A4 · Actual size / 100% · Single-sided
            </DialogDescription>
          </DialogHeader>
          {pdfUrl && (
            <>
              <iframe src={pdfUrl} title="Generated print-ready PDF" />
              <a
                className="pdf-fallback"
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
              >
                Open PDF in a new tab <ArrowUpRight size={14} />
              </a>
            </>
          )}
        </DialogContent>
      </Dialog>
    </SidebarProvider>
  );
}
