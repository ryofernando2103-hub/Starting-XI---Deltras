// GET /api/live?d=YYYY-MM-DD  → skor live laga Deltras pada tanggal itu.
// Hasil disimpan di CDN Vercel 60 detik, jadi ileague.id dibaca paling banyak ±1 kali per menit
// berapa pun jumlah pengunjungnya.
const { CLUB_URL, get, findMatchUrl, parseMatch } = require('./_ileague');

let urlCache = {}; // tanggal -> { url, at }

module.exports = async (req, res) => {
  const d = String((req.query && req.query.d) || '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) {
    res.status(400).json({ error: 'parameter d harus YYYY-MM-DD' });
    return;
  }
  try {
    let hit = urlCache[d];
    if (!hit || Date.now() - hit.at > 6 * 3600e3) {
      const url = findMatchUrl(await get(CLUB_URL), d);
      if (!url) {
        res.setHeader('Cache-Control', 'public, s-maxage=600');
        res.status(404).json({ error: 'laga tidak ditemukan' });
        return;
      }
      hit = urlCache[d] = { url, at: Date.now() };
    }
    const data = parseMatch(await get(hit.url));
    res.setHeader('Cache-Control', data.state === 'ft'
      ? 'public, s-maxage=300, stale-while-revalidate=600'
      : 'public, s-maxage=60, stale-while-revalidate=30');
    res.status(200).json({ d, ...data, src: hit.url, at: new Date().toISOString() });
  } catch (e) {
    res.setHeader('Cache-Control', 'public, s-maxage=15');
    res.status(502).json({ error: String(e.message || e) });
  }
};
