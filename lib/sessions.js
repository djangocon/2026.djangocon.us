const fs = require('fs');
const yaml = require('yaml');
const { parseISO, format } = require('date-fns');
const { TZDate } = require('@date-fns/tz');

function parseDateTime(raw, timezone) {
  if (raw instanceof Date) {
    return new TZDate(raw, timezone);
  }
  if (typeof raw === 'string') {
    const normalized = raw.replace(' ', 'T');
    return new TZDate(parseISO(normalized), timezone);
  }
  return new TZDate(raw, timezone);
}

module.exports = function(config, timezone = 'UTC') {
  const HEADER_ROWS = 0; // no reserved header row; slots start on grid row 1

  // Build the date -> [slots] structure for the talk/break/etc. track (t0),
  // excluding open spaces (by title). Shared by both the schedule grid and the
  // open-space row-span math so the two always agree on slot ordering.
  function buildSortedSlots(collectionApi) {
    let sessions = collectionApi.getFilteredByGlob("src/_content/schedule/{tutorials,talks,sprints}/*.md");

    if (sessions.length === 0) return {};

    const manualContent = fs.readFileSync('src/_content/schedule/manual.yaml', 'utf8');
    const manualData = yaml.parse(manualContent) || [];
    sessions = sessions.concat(manualData);

    sessions = sessions.filter(session => {
      const data = session.data || session;
      return !(data.hidden || session.hidden) && data.title !== 'Open Spaces';
    });

    const sessionsByDateAndTime = sessions.reduce((acc, session) => {
      const sessionData = session.data || session;

      const startDateObj = parseDateTime(sessionData.start_datetime, timezone);
      const endDateObj = parseDateTime(sessionData.end_datetime, timezone);

      const startDate = format(startDateObj, 'yyyy-MM-dd');
      const start = format(startDateObj, "yyyy-MM-dd'T'HH:mm:ssXXX");
      const end = format(endDateObj, "yyyy-MM-dd'T'HH:mm:ssXXX");

      if (!acc[startDate]) {
        acc[startDate] = [];
      }

      const slotKey = `${start}-${end}`;
      let slot = acc[startDate].find(slot => `${slot.start}-${slot.end}` === slotKey);

      if (!slot) {
        slot = { start: start, end: end, sessions: [] };
        acc[startDate].push(slot);
      }

      slot.sessions.push(sessionData);

      return acc;
    }, {});

    const sortedSessionsByDateAndTime = Object.keys(sessionsByDateAndTime)
      .sort((a, b) => new Date(a) - new Date(b))
      .reduce((sortedAcc, date) => {
        sortedAcc[date] = sessionsByDateAndTime[date];
        return sortedAcc;
      }, {});

    for (let date in sortedSessionsByDateAndTime) {
      sortedSessionsByDateAndTime[date].forEach(slot => {
        slot.sessions.sort((a, b) => {
          const aStart = parseDateTime(a.start_datetime, timezone);
          const bStart = parseDateTime(b.start_datetime, timezone);

          const startComparison = aStart - bStart;
          if (startComparison !== 0) return startComparison;

          const aEnd = parseDateTime(a.end_datetime, timezone);
          const bEnd = parseDateTime(b.end_datetime, timezone);

          const endComparison = aEnd - bEnd;
          if (endComparison !== 0) return endComparison;

          return a.track.localeCompare(b.track);
        });
      });

      sortedSessionsByDateAndTime[date].sort((a, b) => {
        const aStart = typeof a.start === 'string' ? parseISO(a.start) : a.start;
        const bStart = typeof b.start === 'string' ? parseISO(b.start) : b.start;
        const startComparison = aStart - bStart;
        if (startComparison !== 0) return startComparison;

        const aEnd = typeof a.end === 'string' ? parseISO(a.end) : a.end;
        const bEnd = typeof b.end === 'string' ? parseISO(b.end) : b.end;
        return aEnd - bEnd;
      });
    }

    return sortedSessionsByDateAndTime;
  }

  function loadOpenSpaces() {
    const manualContent = fs.readFileSync('src/_content/schedule/manual.yaml', 'utf8');
    const manualData = yaml.parse(manualContent) || [];
    return manualData.filter(space => space.track === 't1' && !space.hidden);
  }

  function nearestIndex(slots, ms) {
    let idx = 0;
    let best = Infinity;
    slots.forEach((slot, i) => {
      const diff = Math.abs(new Date(slot.start).getTime() - ms);
      if (diff < best) { best = diff; idx = i; }
    });
    return idx;
  }

  config.addCollection("sessionsByDateAndTime", function(collectionApi) {
    return buildSortedSlots(collectionApi);
  });

  // A single chronologically ordered list per date, mixing talk slots and open
  // spaces as peers. The desktop grid can't use this (it needs open spaces in
  // their own column, spanning rows), but the mobile layout is one column, so
  // it renders straight down this list and everything lands in true time order.
  // Each row is { type: "slot" | "space", start, end } plus the payload.
  config.addCollection("scheduleRowsByDate", function(collectionApi) {
    const slotsByDate = buildSortedSlots(collectionApi);

    const byDate = {};
    for (let date in slotsByDate) {
      byDate[date] = slotsByDate[date].map(slot => ({
        type: 'slot',
        start: slot.start,
        end: slot.end,
        startMs: parseISO(slot.start).getTime(),
        endMs: parseISO(slot.end).getTime(),
        slot,
      }));
    }

    loadOpenSpaces().forEach(space => {
      const startObj = parseDateTime(space.start_datetime, timezone);
      const endObj = parseDateTime(space.end_datetime, timezone);
      const date = format(startObj, 'yyyy-MM-dd');
      const start = format(startObj, "yyyy-MM-dd'T'HH:mm:ssXXX");
      const end = format(endObj, "yyyy-MM-dd'T'HH:mm:ssXXX");

      if (!byDate[date]) byDate[date] = [];
      byDate[date].push({
        type: 'space',
        start,
        end,
        startMs: startObj.getTime(),
        endMs: endObj.getTime(),
        space: Object.assign({}, space, { start, end }),
      });
    });

    for (let date in byDate) {
      // Strict chronological order. On an exact start/end tie a talk slot wins,
      // so concurrent talks stay the primary thing you read first.
      byDate[date].sort((a, b) => {
        if (a.startMs !== b.startMs) return a.startMs - b.startMs;
        if (a.endMs !== b.endMs) return a.endMs - b.endMs;
        if (a.type === b.type) return 0;
        return a.type === 'slot' ? -1 : 1;
      });
      byDate[date].forEach(row => { delete row.startMs; delete row.endMs; });
    }

    return byDate;
  });

  // Open spaces (track "t1") grouped by date, each carrying the CSS grid rows
  // it should span. An open space covers every talk slot it overlaps in time,
  // so on desktop it renders as one tall block beside those talks. Row math:
  // grid row 1 is the column header, slot k (0-based) lives on grid row k + 2.
  config.addCollection("openSpacesByDate", function(collectionApi) {
    const slotsByDate = buildSortedSlots(collectionApi);

    const byDate = {};
    loadOpenSpaces().forEach(space => {
      const startObj = parseDateTime(space.start_datetime, timezone);
      const endObj = parseDateTime(space.end_datetime, timezone);
      const date = format(startObj, 'yyyy-MM-dd');

      const entry = Object.assign({}, space, {
        date,
        startMs: startObj.getTime(),
        endMs: endObj.getTime(),
        start: format(startObj, "yyyy-MM-dd'T'HH:mm:ssXXX"),
        end: format(endObj, "yyyy-MM-dd'T'HH:mm:ssXXX"),
      });

      if (!byDate[date]) byDate[date] = [];
      byDate[date].push(entry);
    });

    for (let date in byDate) {
      const spaces = byDate[date].sort((a, b) => a.startMs - b.startMs);
      const slots = slotsByDate[date] || [];

      spaces.forEach((space, i) => {
        if (slots.length === 0) {
          space.rowStart = HEADER_ROWS + 1;
          space.rowEnd = HEADER_ROWS + 2;
          return;
        }

        // Anchor to the slot nearest the open space's start, then extend down
        // to the last slot that begins before the open space ends.
        const startIdx = nearestIndex(slots, space.startMs);
        let endIdx = startIdx;
        slots.forEach((slot, idx) => {
          if (new Date(slot.start).getTime() < space.endMs) {
            endIdx = Math.max(endIdx, idx);
          }
        });

        // Never bleed into the next open space's starting row.
        const next = spaces[i + 1];
        if (next) {
          endIdx = Math.min(endIdx, nearestIndex(slots, next.startMs) - 1);
        }
        if (endIdx < startIdx) endIdx = startIdx;

        space.rowStart = startIdx + HEADER_ROWS + 1;
        space.rowEnd = endIdx + HEADER_ROWS + 2; // grid-row end line is exclusive
      });

      spaces.forEach(space => { delete space.startMs; delete space.endMs; });
    }

    return byDate;
  });

  config.addCollection("talks", function(collectionApi) {
    let sessions = collectionApi.getFilteredByGlob("src/_content/schedule/talks/*.md");
    sessions = sessions.filter(session => !(session.data?.hidden || session.hidden));
    sessions.sort((a, b) => {
      const aRaw = a.data?.start_datetime || a.start_datetime;
      const bRaw = b.data?.start_datetime || b.start_datetime;

      const aDate = parseDateTime(aRaw, timezone);
      const bDate = parseDateTime(bRaw, timezone);

      return aDate - bDate;
    });

    return sessions;
  });

  // Uncomment if needed in future
  // config.addCollection("tutorials", function(collectionApi) {
  //   let sessions = collectionApi.getFilteredByGlob("src/_content/schedule/tutorials/*.md");
  //   sessions = sessions.filter(session => !(session.data?.hidden || session.hidden));
  //   sessions.sort((a, b) => {
  //     const aRaw = a.data?.start_datetime || a.start_datetime;
  //     const bRaw = b.data?.start_datetime || b.start_datetime;
  //     const aDate = typeof aRaw === 'string' ? parseISO(aRaw) : aRaw;
  //     const bDate = typeof bRaw === 'string' ? parseISO(bRaw) : bRaw;
  //     return aDate - bDate;
  //   });

  //   return sessions;
  // });
};
