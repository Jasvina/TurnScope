const sampleEvents = [
  {
    version: '0.1.0',
    id: 'evt_001',
    type: 'session.started',
    occurred_at: '2026-04-21T00:00:00Z',
    session_id: 'sess_demo',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'session', origin: 'sample' },
    payload: { task: 'Design TurnScope launch repo' },
    attributes: { status: 'running' },
  },
  {
    version: '0.1.0',
    id: 'evt_002',
    type: 'turn.started',
    occurred_at: '2026-04-21T00:00:02Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'turn', origin: 'sample' },
    payload: { summary: 'Inspect repository state' },
    attributes: {},
  },
  {
    version: '0.1.0',
    id: 'evt_003',
    type: 'tool.called',
    occurred_at: '2026-04-21T00:00:04Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'tool', origin: 'sample' },
    payload: { tool: 'rg', arguments: ['--files'], target: 'repo' },
    attributes: { latency_ms: 42 },
  },
  {
    version: '0.1.0',
    id: 'evt_004',
    type: 'shell.started',
    occurred_at: '2026-04-21T00:00:07Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'shell', origin: 'sample' },
    payload: { shell_id: 'sh_001', command: 'rg --files' },
    attributes: { parent_shell_id: null },
  },
  {
    version: '0.1.0',
    id: 'evt_005',
    type: 'shell.finished',
    occurred_at: '2026-04-21T00:00:09Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'shell', origin: 'sample' },
    payload: { shell_id: 'sh_001', exit_code: 0 },
    attributes: { duration_ms: 210 },
  },
  {
    version: '0.1.0',
    id: 'evt_006',
    type: 'file.changed',
    occurred_at: '2026-04-21T00:00:15Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'diff', origin: 'sample' },
    payload: { path: 'README.md', change_kind: 'modified', summary: 'Added first milestone section' },
    attributes: { lines_added: 18, lines_removed: 2 },
  },
  {
    version: '0.1.0',
    id: 'evt_007',
    type: 'subagent.spawned',
    occurred_at: '2026-04-21T00:00:19Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'agent', origin: 'sample' },
    payload: { child_agent_id: 'verifier_01', role: 'verifier' },
    attributes: { parent_agent_id: 'lead' },
  },
  {
    version: '0.1.0',
    id: 'evt_008',
    type: 'approval.requested',
    occurred_at: '2026-04-21T00:00:24Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'approval', origin: 'sample' },
    payload: { kind: 'network', reason: 'push to GitHub' },
    attributes: { status: 'waiting' },
  },
  {
    version: '0.1.0',
    id: 'evt_009',
    type: 'approval.resolved',
    occurred_at: '2026-04-21T00:00:41Z',
    session_id: 'sess_demo',
    turn_id: 'turn_001',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'approval', origin: 'sample' },
    payload: { kind: 'network', decision: 'approved' },
    attributes: { wait_ms: 17000 },
  },
  {
    version: '0.1.0',
    id: 'evt_010',
    type: 'session.finished',
    occurred_at: '2026-04-21T00:00:48Z',
    session_id: 'sess_demo',
    agent_id: 'lead',
    source: { runtime: 'codex', component: 'session', origin: 'sample' },
    payload: { status: 'completed' },
    attributes: { total_events: 10 },
  },
];

const input = document.getElementById('event-input');
const stats = document.getElementById('stats');
const timeline = document.getElementById('timeline');
const timelineLabel = document.getElementById('timeline-label');
const processTree = document.getElementById('process-tree');
const diffList = document.getElementById('diff-list');
const agentGraph = document.getElementById('agent-graph');
const rawView = document.getElementById('raw-view');
const catalogList = document.getElementById('catalog-list');
const catalogLabel = document.getElementById('catalog-label');
const fileInput = document.getElementById('file-input');
const eventSearch = document.getElementById('event-search');
const eventTypeFilter = document.getElementById('event-type-filter');
const clearFilters = document.getElementById('clear-filters');
let loadedSessionEvents = {};
let loadedSessionSummaries = {};
let currentSessionEvents = [];
let visibleEvents = [];
let activeSessionId = null;
let activeEventIndex = 0;
const EMPTY_PRETTY = 'Awaiting session data';
const eventTypeOrder = {
  'session.started': 0,
  'turn.started': 10,
  'tool.called': 20,
  'shell.started': 30,
  'shell.output': 31,
  'shell.finished': 32,
  'tool.finished': 40,
  'file.changed': 50,
  'approval.requested': 60,
  'approval.resolved': 61,
  'subagent.spawned': 70,
  'error.raised': 80,
  'turn.finished': 90,
  'session.finished': 100,
};

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => {
    switch (char) {
      case '&':
        return '&amp;';
      case '<':
        return '&lt;';
      case '>':
        return '&gt;';
      case '"':
        return '&quot;';
      case "'":
        return '&#39;';
      default:
        return char;
    }
  });
}

function eventSortKey(event) {
  return `${String(event.occurred_at)}|${String(eventTypeOrder[event.type] ?? 999).padStart(3, '0')}|${event.id}`;
}

function toNdjson(events) {
  return events.map((event) => JSON.stringify(event)).join('\n');
}

function parseEvents(text) {
  const trimmed = text.trim();
  if (!trimmed) {
    return [];
  }
  if (trimmed.startsWith('[')) {
    return JSON.parse(trimmed);
  }
  return trimmed
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .sort((a, b) => eventSortKey(a).localeCompare(eventSortKey(b)));
}

function count(events, type) {
  return events.filter((event) => event.type === type).length;
}

function countLabel(value, singular, plural = `${singular}s`) {
  const countValue = Number(value || 0);
  return `${countValue} ${countValue === 1 ? singular : plural}`;
}

function searchableEventText(event) {
  return [
    event.type,
    event.occurred_at,
    event.session_id,
    event.turn_id,
    event.agent_id,
    event.source?.runtime,
    event.source?.component,
    detailText(event),
    JSON.stringify(event.payload || {}),
    JSON.stringify(event.attributes || {}),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
}

function populateEventTypeFilter(events) {
  const previous = eventTypeFilter.value;
  const types = Array.from(new Set(events.map((event) => event.type))).sort();
  eventTypeFilter.innerHTML = [
    '<option value="">All event types</option>',
    ...types.map((type) => `<option value="${type}">${type}</option>`),
  ].join('');
  eventTypeFilter.value = types.includes(previous) ? previous : '';
}

function filteredEvents() {
  const query = eventSearch.value.trim().toLowerCase();
  const selectedType = eventTypeFilter.value;
  return currentSessionEvents.filter((event) => {
    const matchesType = !selectedType || event.type === selectedType;
    const matchesQuery = !query || searchableEventText(event).includes(query);
    return matchesType && matchesQuery;
  });
}

function renderStats(events, summary) {
  const shellCount = count(events, 'shell.started');
  const fileCount = count(events, 'file.changed');
  const subagentCount = count(events, 'subagent.spawned');
  const droppedCount = Number(summary?.dropped_event_count || 0);
  const cards = summary
    ? [
        ['Session', summary.session_id || 'n/a'],
        ['Events', String(summary.event_count || 0)],
        ['Turns', String(summary.turn_count || 0)],
        ['Tools', String(summary.tool_call_count || 0)],
        ['Shells', String(summary.shell_count || shellCount)],
        ['Approvals', String(summary.approval_count || 0)],
        ['Files', String(summary.file_change_count || fileCount)],
        ['Delegations', String(summary.subagent_count || subagentCount)],
        ['Dropped', String(droppedCount)],
      ]
    : [
        ['Session', events[0]?.session_id || 'n/a'],
        ['Events', String(events.length)],
        ['Turns', String(count(events, 'turn.started'))],
        ['Tools', String(count(events, 'tool.called'))],
        ['Shells', String(shellCount)],
        ['Approvals', String(count(events, 'approval.requested'))],
        ['Files', String(fileCount)],
        ['Delegations', String(subagentCount)],
        ['Dropped', '0'],
      ];
  stats.innerHTML = cards
    .map(
      ([label, value]) => `
        <div class="stat">
          <small>${escapeHtml(label)}</small>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `,
    )
    .join('');
}

function humanType(type) {
  return String(type).replace('.', ' / ');
}

function detailText(event) {
  if (event.type === 'tool.called') {
    return `${event.payload.tool || event.payload.name} ${JSON.stringify(event.payload.arguments || event.payload.args || [])}`;
  }
  if (event.type === 'tool.finished') {
    return `${event.payload.tool || event.payload.name} finished`;
  }
  if (event.type === 'shell.started') {
    return event.payload.command;
  }
  if (event.type === 'shell.output') {
    return event.payload.delta || '(output chunk)';
  }
  if (event.type === 'shell.finished') {
    return `exit ${event.payload.exit_code}`;
  }
  if (event.type === 'file.changed') {
    return `${event.payload.path || '(multiple files)'} - ${event.payload.summary || event.payload.status || 'changed'}`;
  }
  if (event.type === 'subagent.spawned') {
    return `${event.payload.child_agent_id} (${event.payload.role || event.payload.tool || 'spawn_agent'})`;
  }
  if (event.type === 'approval.requested') {
    return `${event.payload.kind || 'approval'} / ${event.payload.reason || 'waiting'}`;
  }
  if (event.type === 'approval.resolved') {
    return `${event.payload.kind || 'approval'} / resolved`;
  }
  if (event.type === 'turn.started') {
    return event.payload.summary || 'turn started';
  }
  if (event.type === 'session.started') {
    return event.payload.task || 'session started';
  }
  if (event.type === 'turn.finished' || event.type === 'session.finished') {
    return event.payload.status || 'completed';
  }
  return JSON.stringify(event.payload);
}

function selectedVisibleEvent() {
  return visibleEvents[activeEventIndex] || visibleEvents[0] || null;
}

function renderTimeline(events, totalCount = events.length) {
  visibleEvents = events;
  activeEventIndex = 0;
  timelineLabel.textContent = totalCount === events.length ? `${events.length} events` : `${events.length}/${totalCount} events`;
  timeline.innerHTML = events.length
    ? events
        .map((event, index) => {
          const className = event.type.replace('.', '-');
          return `
            <button class="timeline-item ${className} ${index === 0 ? 'active' : ''}" data-event-index="${index}">
              <div class="timeline-meta">${escapeHtml(event.occurred_at)}<br />${escapeHtml(humanType(event.type))}</div>
              <div>
                <strong>${escapeHtml(detailText(event))}</strong>
                <div class="timeline-meta">agent: ${escapeHtml(event.agent_id || 'n/a')} | runtime: ${escapeHtml(event.source.runtime || 'n/a')}</div>
              </div>
            </button>
          `;
        })
        .join('')
    : `<div class="timeline-item"><div><strong>${EMPTY_PRETTY}</strong><div class="timeline-meta">Load a sample trace or paste NDJSON to begin.</div></div></div>`;
}

function renderProcessTree(events) {
  const started = events.filter((event) => event.type === 'shell.started');
  processTree.innerHTML = started.length
    ? started
        .map((event) => {
          const finished = events.find(
            (candidate) => candidate.type === 'shell.finished' && candidate.payload.shell_id === event.payload.shell_id,
          );
          const outputs = events.filter(
            (candidate) => candidate.type === 'shell.output' && candidate.payload.shell_id === event.payload.shell_id,
          );
          return `
            <div class="process-node">
              <strong>${escapeHtml(event.payload.command || '(no command)')}</strong>
              <small>shell id: ${escapeHtml(event.payload.shell_id || 'n/a')}</small>
              <small>parent shell: ${escapeHtml((event.attributes || {}).parent_shell_id || 'root')}</small>
              <small>exit: ${escapeHtml(finished ? finished.payload.exit_code : 'running')}</small>
              <small>output chunks: ${escapeHtml(outputs.length)}</small>
            </div>
          `;
        })
        .join('')
    : '<div class="process-node"><strong>No shell activity</strong><small>Commands will appear here when a session records shell launches.</small></div>';
}

function renderDiffs(events) {
  const diffs = events.filter((event) => event.type === 'file.changed');
  diffList.innerHTML = diffs.length
    ? diffs
        .map(
          (event) => `
            <div class="diff-item">
              <strong>${escapeHtml(event.payload.path || '(multiple files)')}</strong>
              <small>${escapeHtml(event.payload.summary || event.payload.status || 'change recorded')}</small>
              <small>changes: ${escapeHtml(event.payload.changes ? event.payload.changes.length : 1)}</small>
            </div>
          `,
        )
        .join('')
    : '<div class="diff-item"><strong>No file changes</strong><small>Diff evidence will surface here after the first edit event.</small></div>';
}

function renderAgentGraph(events) {
  const subagents = events.filter((event) => event.type === 'subagent.spawned');
  const lead = events.find((event) => event.agent_id)?.agent_id || 'lead';
  const nodes = [`<div class="agent-node lead"><strong>${escapeHtml(lead)}</strong><small>primary agent</small></div>`];
  subagents.forEach((event) => {
    nodes.push(
      `<div class="agent-node child"><strong>${escapeHtml(event.payload.child_agent_id || 'child agent')}</strong><small>${escapeHtml(event.payload.role || event.payload.tool || 'child agent')}</small></div>`,
    );
  });
  agentGraph.innerHTML = nodes.length
    ? nodes.join('')
    : '<div class="agent-node lead"><strong>No delegation yet</strong><small>Subagent hops will appear once a run fans out.</small></div>';
}

function renderRaw(events) {
  const event = selectedVisibleEvent();
  rawView.textContent = JSON.stringify(event || {}, null, 2);
}

function selectEvent(index) {
  activeEventIndex = index;
  const event = visibleEvents[index];
  rawView.textContent = JSON.stringify(event || {}, null, 2);
  Array.from(timeline.querySelectorAll('[data-event-index]')).forEach((node) => {
    node.classList.toggle('active', Number(node.getAttribute('data-event-index')) === index);
  });
}

function renderCatalog(indexData) {
  if (!indexData) {
    catalogLabel.textContent = 'No index loaded';
    catalogList.innerHTML = '<div class="catalog-item"><strong>Load a collector `index.json` or `*.summary.json` file.</strong><small>Session summaries will appear here for quick switching.</small></div>';
    return;
  }
  const sessions = Array.isArray(indexData.sessions) ? indexData.sessions : [indexData];
  const totalDropped = Number(
    indexData.dropped_event_count ??
      sessions.reduce((sum, session) => sum + Number(session.dropped_event_count || 0), 0),
  );
  catalogLabel.textContent = `${countLabel(sessions.length, 'session summary')} · ${countLabel(totalDropped, 'dropped invalid event')}`;
  catalogList.innerHTML = sessions
    .map(
      (session, position) => `
        <button class="catalog-item ${activeSessionId === (session.session_id || '') || (!activeSessionId && position === 0) ? 'active' : ''}" data-session-id="${session.session_id || ''}">
          <strong>${escapeHtml(session.session_id || 'unknown session')}</strong>
          <small>status: ${escapeHtml(session.status || 'unknown')}</small>
          <small>events: ${escapeHtml(session.event_count || 0)}</small>
          <small>turns: ${escapeHtml(session.turn_count || 0)}</small>
          <small>dropped invalid events: ${escapeHtml(session.dropped_event_count || 0)}</small>
          <small>bundle: ${escapeHtml(session.bundle_path || session.log_path || '(summary only)')}</small>
        </button>
      `,
    )
    .join('');
}

function applyEventFilters() {
  const events = filteredEvents();
  renderTimeline(events, currentSessionEvents.length);
  renderProcessTree(events);
  renderDiffs(events);
  renderAgentGraph(events);
  renderRaw(events);
}

function renderEvents(events, summary = null) {
  currentSessionEvents = events;
  renderStats(events, summary);
  populateEventTypeFilter(events);
  applyEventFilters();
}

function handleLoadedText(text) {
  const trimmed = text.trim();
  if (!trimmed) {
    return;
  }
  if (trimmed.startsWith('{')) {
    const parsed = JSON.parse(trimmed);
    if (parsed.kind === 'turnscope.session.pack' && Array.isArray(parsed.sessions)) {
      loadedSessionEvents = Object.fromEntries(
        parsed.sessions.map((session) => [session.summary.session_id, session.events]),
      );
      loadedSessionSummaries = Object.fromEntries(
        parsed.sessions.map((session) => [session.summary.session_id, session.summary]),
      );
      activeSessionId = parsed.sessions[0]?.summary?.session_id || null;
      renderCatalog({ sessions: parsed.sessions.map((session) => session.summary) });
      if (activeSessionId) {
        renderEvents(loadedSessionEvents[activeSessionId], parsed.sessions[0].summary);
      }
      return;
    }
    if (parsed.kind === 'turnscope.session.bundle' && parsed.summary && Array.isArray(parsed.events)) {
      loadedSessionEvents = { [parsed.summary.session_id]: parsed.events };
      loadedSessionSummaries = { [parsed.summary.session_id]: parsed.summary };
      activeSessionId = parsed.summary.session_id;
      renderCatalog({ sessions: [parsed.summary] });
      renderEvents(parsed.events, parsed.summary);
      return;
    }
    if (Array.isArray(parsed.sessions) || parsed.session_id) {
      loadedSessionEvents = {};
      loadedSessionSummaries = Array.isArray(parsed.sessions)
        ? Object.fromEntries(parsed.sessions.map((session) => [session.session_id, session]))
        : { [parsed.session_id]: parsed };
      activeSessionId = Array.isArray(parsed.sessions) ? parsed.sessions[0]?.session_id : parsed.session_id;
      renderCatalog(parsed);
      renderStats([], Array.isArray(parsed.sessions) ? parsed.sessions[0] : parsed);
      return;
    }
  }
  loadedSessionEvents = {};
  loadedSessionSummaries = {};
  activeSessionId = null;
  const events = parseEvents(trimmed);
  renderEvents(events);
}

document.getElementById('load-sample').addEventListener('click', () => {
  input.value = toNdjson(sampleEvents);
  loadedSessionEvents = { sess_demo: sampleEvents };
  loadedSessionSummaries = {
    sess_demo: {
      session_id: 'sess_demo',
      status: 'completed',
      event_count: sampleEvents.length,
      turn_count: 1,
      tool_call_count: 1,
      approval_count: 1,
      log_path: 'sample/in-memory',
    },
  };
  activeSessionId = 'sess_demo';
  renderCatalog({
    sessions: [
      {
        session_id: 'sess_demo',
        status: 'completed',
        event_count: sampleEvents.length,
        turn_count: 1,
        tool_call_count: 1,
        approval_count: 1,
        dropped_event_count: 0,
        log_path: 'sample/in-memory',
      },
    ],
  });
  renderEvents(sampleEvents);
});

document.getElementById('render-input').addEventListener('click', () => {
  try {
    handleLoadedText(input.value);
  } catch (error) {
    alert(`Could not parse input: ${error.message}`);
  }
});

document.getElementById('load-file').addEventListener('click', () => {
  fileInput.click();
});

fileInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }
  const text = await file.text();
  input.value = text;
  try {
    handleLoadedText(text);
  } catch (error) {
    alert(`Could not parse file: ${error.message}`);
  }
});

catalogList.addEventListener('click', (event) => {
  const target = event.target.closest('[data-session-id]');
  if (!target) {
    return;
  }
  const sessionId = target.getAttribute('data-session-id');
  if (!sessionId) {
    return;
  }
  activeSessionId = sessionId;
  if (loadedSessionEvents[sessionId]) {
    const sessions = Array.from(catalogList.querySelectorAll('[data-session-id]'));
    sessions.forEach((node) => node.classList.toggle('active', node.getAttribute('data-session-id') === sessionId));
    renderEvents(loadedSessionEvents[sessionId], loadedSessionSummaries[sessionId] || null);
  }
});

timeline.addEventListener('click', (event) => {
  const target = event.target.closest('[data-event-index]');
  if (!target) {
    return;
  }
  selectEvent(Number(target.getAttribute('data-event-index')));
});

eventSearch.addEventListener('input', applyEventFilters);
eventTypeFilter.addEventListener('change', applyEventFilters);
clearFilters.addEventListener('click', () => {
  eventSearch.value = '';
  eventTypeFilter.value = '';
  applyEventFilters();
});

input.value = toNdjson(sampleEvents);
loadedSessionEvents = { sess_demo: sampleEvents };
loadedSessionSummaries = {
  sess_demo: {
    session_id: 'sess_demo',
    status: 'completed',
    event_count: sampleEvents.length,
    turn_count: 1,
    tool_call_count: 1,
    approval_count: 1,
    dropped_event_count: 0,
    log_path: 'sample/in-memory',
  },
};
activeSessionId = 'sess_demo';
renderCatalog({
  sessions: [
    {
      session_id: 'sess_demo',
      status: 'completed',
      event_count: sampleEvents.length,
      turn_count: 1,
      tool_call_count: 1,
      approval_count: 1,
      dropped_event_count: 0,
      log_path: 'sample/in-memory',
    },
  ],
});
renderEvents(sampleEvents);
