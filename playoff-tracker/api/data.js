const NHL_API = 'https://api-web.nhle.com/v1';
const MONEYPUCK_URL =
  'https://moneypuck.com/moneypuck/simulations/simulations_recent.csv';
const TEAM = 'WSH';
const TOTAL_GAMES = 82;

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 's-maxage=240, stale-while-revalidate=30');
  res.setHeader('Access-Control-Allow-Origin', '*');

  try {
    const result = await buildResponse();
    res.status(200).json(result);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch data', detail: err.message });
  }
};

async function buildResponse() {
  const season = computeSeason();
  const [standings, schedule, oddsCsv] = await Promise.all([
    fetchJson(`${NHL_API}/standings/now`),
    fetchJson(`${NHL_API}/club-schedule-season/${TEAM}/${season}`),
    fetchText(MONEYPUCK_URL),
  ]);
  const standingsMap = buildStandingsMap(standings.standings);
  return {
    caps: standingsMap[TEAM] || null,
    divisionRace: computeDivisionRace(standings.standings),
    remainingGames: computeRemainingGames(schedule, standingsMap),
    playoffOdds: parsePlayoffOdds(oddsCsv),
    updatedAt: new Date().toISOString(),
  };
}

function computeSeason() {
  const now = new Date();
  const year = now.getMonth() >= 9 ? now.getFullYear() : now.getFullYear() - 1;
  return `${year}${year + 1}`;
}

async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} returned ${r.status}`);
  return r.json();
}

async function fetchText(url) {
  const r = await fetch(url);
  if (!r.ok) return '';
  return r.text();
}

function buildStandingsMap(teams) {
  const map = {};
  for (const t of teams) {
    map[t.teamAbbrev.default] = formatTeam(t);
  }
  return map;
}

function formatTeam(t) {
  return {
    name: t.teamName.default,
    abbrev: t.teamAbbrev.default,
    points: t.points,
    wins: t.wins,
    losses: t.losses,
    otLosses: t.otLosses,
    gamesPlayed: t.gamesPlayed,
    remaining: TOTAL_GAMES - t.gamesPlayed,
    regulationWins: t.regulationWins,
    goalDifferential: t.goalDifferential,
    conference: t.conferenceAbbrev,
    division: t.divisionAbbrev,
    logo: t.teamLogo,
  };
}

function toDivisionEntry(t, index) {
  const caps = formatTeam(t);
  const maxPossible = caps.points + caps.remaining * 2;
  return {
    ...caps,
    position: index + 1,
    inPlayoffs: index < 3,
    isCaps: t.teamAbbrev.default === TEAM,
    maxPossible,
  };
}

function computeDivisionRace(teams) {
  const metro = teams.filter((t) => t.divisionAbbrev === 'M');
  metro.sort((a, b) => b.points - a.points);
  const entries = metro.map(toDivisionEntry);
  const capsEntry = entries.find((e) => e.isCaps);
  const thirdPlace = entries[2] || null;
  const magicNumber =
    capsEntry && thirdPlace
      ? thirdPlace.points + thirdPlace.remaining * 2 - capsEntry.points + 1
      : null;
  const pointsBack =
    capsEntry && thirdPlace ? thirdPlace.points - capsEntry.points : null;
  return {
    standings: entries,
    capsScenario: {
      pointsBack: pointsBack > 0 ? pointsBack : 0,
      magicNumber,
      thirdPlaceTeam: thirdPlace ? thirdPlace.name : null,
      thirdPlacePoints: thirdPlace ? thirdPlace.points : null,
      thirdPlaceRemaining: thirdPlace ? thirdPlace.remaining : null,
      capsRemaining: capsEntry ? capsEntry.remaining : null,
      capsMaxPoints: capsEntry ? capsEntry.maxPossible : null,
      capsRegWins: capsEntry ? capsEntry.regulationWins : null,
      thirdPlaceRegWins: thirdPlace ? thirdPlace.regulationWins : null,
      capsHoldTiebreaker:
        capsEntry && thirdPlace
          ? capsEntry.regulationWins > thirdPlace.regulationWins
          : null,
      eliminated: computeEliminated(capsEntry, thirdPlace),
    },
  };
}

function computeEliminated(capsEntry, thirdPlace) {
  if (!capsEntry || !thirdPlace) return false;
  return capsEntry.maxPossible < thirdPlace.points;
}

function mapGameToEntry(g, standingsMap) {
  const isHome = g.homeTeam.abbrev === TEAM;
  const oppAbbrev = isHome ? g.awayTeam.abbrev : g.homeTeam.abbrev;
  const opp = standingsMap[oppAbbrev] || {};
  return {
    date: g.gameDate,
    startTime: g.startTimeUTC,
    isHome,
    opponent: {
      abbrev: oppAbbrev,
      name: opp.name || oppAbbrev,
      points: opp.points || 0,
      wins: opp.wins || 0,
      losses: opp.losses || 0,
      otLosses: opp.otLosses || 0,
      logo: opp.logo || '',
    },
  };
}

function computeRemainingGames(schedule, standingsMap) {
  const futureStates = new Set(['FUT', 'PRE']);
  return (schedule.games || [])
    .filter((g) => futureStates.has(g.gameState))
    .map((g) => mapGameToEntry(g, standingsMap));
}

function findColumn(headers, ...names) {
  return headers.findIndex((h) => names.some((n) => h.includes(n)));
}

function parseOddsColumns(headers) {
  return {
    team: findColumn(headers, 'team'),
    situation: Math.max(
      findColumn(headers, 'scenerio'),
      findColumn(headers, 'scenario'),
      findColumn(headers, 'situation')
    ),
    playoffs: Math.max(
      findColumn(headers, 'madeplayoffs'),
      findColumn(headers, 'makeplayoffs')
    ),
    points: findColumn(headers, 'points'),
  };
}

function parseOddsRow(cols, idx) {
  return {
    makePlayoffs: parseFloat(cols[idx.playoffs]) || 0,
    projectedPoints: idx.points >= 0 ? parseFloat(cols[idx.points]) || 0 : null,
  };
}

function extractTeamRows(lines, idx) {
  const scenarios = {};
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',');
    if (cols[idx.team]?.trim() !== TEAM) continue;
    const sit = idx.situation >= 0 ? cols[idx.situation]?.trim() : 'ALL';
    scenarios[sit] = parseOddsRow(cols, idx);
  }
  return scenarios;
}

function parsePlayoffOdds(csv) {
  if (!csv) return null;
  try {
    const lines = csv.trim().split('\n');
    const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
    const idx = parseOddsColumns(headers);
    if (idx.team < 0 || idx.playoffs < 0) return null;
    const scenarios = extractTeamRows(lines, idx);
    return Object.keys(scenarios).length > 0 ? scenarios : null;
  } catch {
    return null;
  }
}
