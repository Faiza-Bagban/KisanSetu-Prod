// frontend/src/utils/cache.js
// Week 9 Day 2 (Sakshi) — simple TTL cache for API responses
// Reduces unnecessary re-fetches on page revisit within same session.

const CACHE = {};

/**
 * Get cached value if not expired.
 * @param {string} key
 * @param {number} ttlMs - time to live in milliseconds
 */
export function getCached(key, ttlMs = 60_000) {
  const entry = CACHE[key];
  if (!entry) return null;
  if (Date.now() - entry.ts > ttlMs) {
    delete CACHE[key];
    return null;
  }
  return entry.data;
}

/**
 * Store value in cache.
 */
export function setCached(key, data) {
  CACHE[key] = { data, ts: Date.now() };
}

/**
 * Wrapper — fetch from cache or call fetchFn, then cache result.
 * @param {string} key
 * @param {Function} fetchFn - async function that returns data
 * @param {number} ttlMs
 */
export async function cachedFetch(key, fetchFn, ttlMs = 60_000) {
  const cached = getCached(key, ttlMs);
  if (cached !== null) return cached;
  const data = await fetchFn();
  setCached(key, data);
  return data;
}