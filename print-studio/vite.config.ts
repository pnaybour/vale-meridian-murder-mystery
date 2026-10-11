import tailwindcss from '@tailwindcss/postcss';
import { execFile } from 'node:child_process';
import { readFile, rename, writeFile } from 'node:fs/promises';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import vinext from 'vinext';
import { defineConfig, type Plugin } from 'vite';

const execFileAsync = promisify(execFile);
const projectRoot = fileURLToPath(new URL('.', import.meta.url));

// The studio uses no Cloudflare bindings; the plugin only provides the server runtime.
const localBindingConfig = {
  main: 'vinext/server/fetch-handler',
  compatibility_flags: ['nodejs_compat'],
  d1_databases: [],
  r2_buckets: [],
};

const manualDatabaseReload = {
  name: 'valemeridian-manual-database-reload',
  configureServer(server) {
    server.middlewares.use(
      '/api/reload-data',
      async (request, response, next) => {
        if (request.method !== 'POST') {
          next();
          return;
        }
        response.setHeader('Content-Type', 'application/json; charset=utf-8');
        try {
          const refresh = await execFileAsync(
            'python3',
            ['scripts/export_snapshot.py'],
            { cwd: projectRoot },
          );
          const check = await execFileAsync(
            'python3',
            ['scripts/check_snapshot.py'],
            { cwd: projectRoot },
          );
          response.statusCode = 200;
          response.end(
            JSON.stringify({
              ok: true,
              message: 'Reloaded and verified the latest local database.',
              refresh: refresh.stdout.trim(),
              check: check.stdout.trim(),
            }),
          );
        } catch (error) {
          const details = error as Error & { stdout?: string; stderr?: string };
          response.statusCode = 500;
          response.end(
            JSON.stringify({
              ok: false,
              message: 'The database could not be reloaded.',
              details: (details.stderr || details.stdout || details.message).trim(),
            }),
          );
        }
      },
    );
  },
} satisfies Plugin;

// Review comments live beside the event database, outside the app, so they survive a
// browser change and can be read by whoever edits the cards. Local development only.
const commentsFile = fileURLToPath(new URL('../data/review-comments.json', import.meta.url));
type StoredComment = { id: string; status: string; resolvedAt?: string } & Record<string, unknown>;

async function readComments(): Promise<StoredComment[]> {
  try {
    const body = JSON.parse(await readFile(commentsFile, 'utf8')) as { comments?: StoredComment[] };
    return body.comments ?? [];
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return [];
    throw error;
  }
}

async function writeComments(comments: StoredComment[]) {
  const temporary = `${commentsFile}.tmp`;
  await writeFile(
    temporary,
    `${JSON.stringify({ updatedAt: new Date().toISOString(), comments }, null, 2)}\n`,
  );
  await rename(temporary, commentsFile);
}

const reviewComments = {
  name: 'valemeridian-review-comments',
  configureServer(server) {
    server.middlewares.use('/api/comments', async (request, response) => {
      response.setHeader('Content-Type', 'application/json; charset=utf-8');
      try {
        if (request.method === 'GET') {
          response.end(JSON.stringify({ comments: await readComments() }));
          return;
        }
        if (request.method !== 'POST') {
          response.statusCode = 405;
          response.end(JSON.stringify({ message: 'Use GET or POST.' }));
          return;
        }
        let raw = '';
        for await (const chunk of request) raw += chunk;
        const body = JSON.parse(raw || '{}') as {
          action?: string;
          id?: string;
          status?: string;
          comment?: StoredComment;
        };
        let comments = await readComments();
        if (body.action === 'add' && body.comment?.id && typeof body.comment.text === 'string') {
          comments = [...comments.filter((c) => c.id !== body.comment!.id), body.comment];
        } else if (body.action === 'status' && body.id && ['open', 'resolved'].includes(body.status ?? '')) {
          comments = comments.map((c) =>
            c.id === body.id
              ? { ...c, status: body.status!, resolvedAt: body.status === 'resolved' ? new Date().toISOString() : undefined }
              : c,
          );
        } else if (body.action === 'delete' && body.id) {
          comments = comments.filter((c) => c.id !== body.id);
        } else {
          response.statusCode = 400;
          response.end(JSON.stringify({ message: 'Unrecognised comment request.' }));
          return;
        }
        await writeComments(comments);
        response.end(JSON.stringify({ comments }));
      } catch (error) {
        response.statusCode = 500;
        response.end(JSON.stringify({ message: `Comments could not be saved: ${(error as Error).message}` }));
      }
    });
  },
} satisfies Plugin;

// Review status per handout ('reviewed' or 'approved', tied to a card revision), kept
// beside the comments for the same reasons. Local development only.
const reviewsFile = fileURLToPath(new URL('../data/review-status.json', import.meta.url));
type StoredReview = { revision: string; at: string; status?: string };

async function readReviews(): Promise<Record<string, StoredReview>> {
  try {
    const body = JSON.parse(await readFile(reviewsFile, 'utf8')) as { reviews?: Record<string, StoredReview> };
    return body.reviews ?? {};
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return {};
    throw error;
  }
}

async function writeReviews(reviews: Record<string, StoredReview>) {
  const temporary = `${reviewsFile}.tmp`;
  const sorted = Object.fromEntries(Object.entries(reviews).sort(([a], [b]) => a.localeCompare(b)));
  await writeFile(
    temporary,
    `${JSON.stringify({ updatedAt: new Date().toISOString(), reviews: sorted }, null, 2)}\n`,
  );
  await rename(temporary, reviewsFile);
}

const isReview = (r: unknown): r is StoredReview =>
  !!r &&
  typeof (r as StoredReview).revision === 'string' &&
  typeof (r as StoredReview).at === 'string' &&
  ['reviewed', 'approved'].includes((r as StoredReview).status ?? '');

const reviewStatus = {
  name: 'valemeridian-review-status',
  configureServer(server) {
    server.middlewares.use('/api/reviews', async (request, response) => {
      response.setHeader('Content-Type', 'application/json; charset=utf-8');
      try {
        if (request.method === 'GET') {
          response.end(JSON.stringify({ reviews: await readReviews() }));
          return;
        }
        if (request.method !== 'POST') {
          response.statusCode = 405;
          response.end(JSON.stringify({ message: 'Use GET or POST.' }));
          return;
        }
        let raw = '';
        for await (const chunk of request) raw += chunk;
        const body = JSON.parse(raw || '{}') as {
          action?: string;
          id?: string;
          review?: unknown;
          reviews?: Record<string, unknown>;
        };
        const reviews = await readReviews();
        if (body.action === 'set' && body.id && isReview(body.review)) {
          reviews[body.id] = body.review;
        } else if (body.action === 'clear' && body.id) {
          delete reviews[body.id];
        } else if (body.action === 'merge' && body.reviews) {
          // Keeps the later of two records for the same handout.
          for (const [id, review] of Object.entries(body.reviews)) {
            if (isReview(review) && (!reviews[id] || reviews[id].at < review.at)) reviews[id] = review;
          }
        } else {
          response.statusCode = 400;
          response.end(JSON.stringify({ message: 'Unrecognised review request.' }));
          return;
        }
        await writeReviews(reviews);
        response.end(JSON.stringify({ reviews }));
      } catch (error) {
        response.statusCode = 500;
        response.end(JSON.stringify({ message: `Review status could not be saved: ${(error as Error).message}` }));
      }
    });
  },
} satisfies Plugin;

export default defineConfig(async () => {
  // Keep Wrangler and Miniflare state project-local. These are non-secret tool
  // settings; application environment belongs in ignored `.env*` files.
  process.env.WRANGLER_WRITE_LOGS ??= 'false';
  process.env.WRANGLER_LOG_PATH ??= '.wrangler/logs';
  process.env.MINIFLARE_REGISTRY_PATH ??= '.wrangler/registry';

  // Wrangler snapshots its log path while the Cloudflare plugin is imported.
  const { cloudflare } = await import('@cloudflare/vite-plugin');

  return {
    css: { postcss: { plugins: [tailwindcss()] } },
    // PRINT_STUDIO_LAN=1 binds to every interface so a machine beside the printer can open the
    // studio in a browser. The print pack is built in the browser, so nothing else is needed
    // there. Off by default: this is a development server with endpoints that write to the repo.
    server: {
      ...(process.env.PRINT_STUDIO_LAN ? { host: true } : {}),
    },
    plugins: [
      manualDatabaseReload,
      reviewComments,
      reviewStatus,
      vinext(),
      cloudflare({
        viteEnvironment: { name: 'rsc', childEnvironments: ['ssr'] },
        config: localBindingConfig,
      }),
    ],
  };
});
