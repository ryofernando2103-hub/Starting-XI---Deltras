// Pembaca halaman laga ileague.id untuk skor live.
// File berawalan "_" tidak dijadikan endpoint oleh Vercel.

const BASE = 'https://www.ileague.id';
const CLUB_URL = BASE + '/clubs/single/PEGADAIAN_CHAMPIONSHIP_2026-27/DELTRAS_FC';
const UA = 'Mozilla/5.0 (compatible; StartingXIDeltras-live/1.0)';

const clean = (s) => (s || '')
  .replace(/<[^>]*>/g, ' ')
  .replace(/&nbsp;/g, ' ')
  .replace(/&#0?39;|&apos;/g, "'")
  .replace(/&amp;/g, '&')
  .replace(/\s+/g, ' ')
  .trim();

const title = (s) => s.toLowerCase().replace(/(^|[\s'-])(\S)/g, (m, a, b) => a + b.toUpperCase());

async function get(url) {
  const r = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'text/html' }, redirect: 'follow' });
  if (!r.ok) throw new Error('ileague ' + r.status);
  return r.text();
}

// URL halaman laga untuk tanggal tertentu, diambil dari halaman klub (slug tim di ileague tidak beraturan).
function findMatchUrl(clubPage, date) {
  const re = new RegExp('href="(' + BASE.replace(/\./g, '\\.') + '/result/detail/[^"]*/' + date + '/[^"]+)"', 'i');
  const m = clubPage.match(re);
  return m ? m[1] : null;
}

function parseEvents(ul) {
  const out = [];
  const re = /<li>([\s\S]*?)<\/li>/g;
  let m;
  while ((m = re.exec(ul))) {
    const li = m[1];
    const icon = li.match(/<i class="([^"]+)"([^>]*)>/);
    if (!icon) continue;
    const cls = icon[1], attr = icon[2];
    const name = clean(li.slice(0, li.indexOf('<i ')));
    const min = (clean(li.slice(li.indexOf('</i>') + 4)).match(/\d+(?:\+\d+)?/) || [''])[0];
    let type = null;
    if (/futbol|soccer/.test(cls)) type = /own|og|red/i.test(cls + attr) ? 'og' : 'goal';
    else if (/square/.test(cls)) type = /red/i.test(attr) ? 'red' : 'yellow';
    if (!type) continue;
    out.push({ type, name: title(name), min });
  }
  // urutkan sesuai menit (ileague mengurutkan per nama)
  const key = (s) => { const p = s.split('+'); return (+p[0] || 0) + (+p[1] || 0) / 100; };
  return out.sort((a, b) => key(a.min) - key(b.min));
}

function parseMatch(page) {
  const box = page.match(
    /<div style="text-align: center;font-size: 18px;font-weight: bold;color: white">([\s\S]*?)<\/div>\s*<div id="blink_live">([\s\S]*?)<\/div>\s*<div class="result-match">([\s\S]*?)<\/div>\s*<div class="live-time">\s*<div class="live-on"[^>]*>([\s\S]*?)<\/div>/
  );
  if (!box) throw new Error('struktur halaman laga berubah');
  const status = clean(box[1]);
  const blink = clean(box[2]);
  const scoreTxt = clean(box[3]);
  const liveOn = clean(box[4]);
  const sc = scoreTxt.match(/^(\d+)\s*:\s*(\d+)$/);

  const sides = [];
  const re = /<div class="team( right)? match-hero-team">[\s\S]*?<span class="match-hero-name">([^<]*)<\/span>[\s\S]*?<ul>([\s\S]*?)<\/ul>/g;
  let m;
  while ((m = re.exec(page)) && sides.length < 2) sides.push({ name: title(clean(m[2])), events: parseEvents(m[3]) });
  if (sides.length !== 2) throw new Error('daftar kejadian tidak ditemukan');

  const ft = /\bFT\b|full ?time|selesai/i.test(status);
  const state = ft ? 'ft' : sc ? 'live' : 'pre';
  // Menit/fase laga: ambil teks pertama yang terisi (mis. "HT", "67'").
  const phase = state === 'live' ? ([liveOn, blink, status].find((t) => t && !/^live$/i.test(t)) || '') : '';
  const ko = (page.match(/Kick Off <b>(\d{1,2}:\d{2}) WIB<\/b>/) || [])[1] || null;

  return {
    state,
    phase,
    kickoff: ko,
    home: { name: sides[0].name, score: sc ? +sc[1] : null, events: sides[0].events },
    away: { name: sides[1].name, score: sc ? +sc[2] : null, events: sides[1].events },
  };
}

module.exports = { BASE, CLUB_URL, get, findMatchUrl, parseMatch };
