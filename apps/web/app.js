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
    payload: { name: 'rg', args: ['--files'], target: 'repo' },
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

function toNdjson(events) {
  return events.map((event) => JSON.stringify(event)).join('\n');
}

function parseEvents(text) {
  return text
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line))
    .sort((a, b) => a.occurred_at.localeCompare(b.occurred_at));
}

function count(events, type) {
  return events.filter((event) => event.type === type).length;
}

function renderStats(events) {
  const cards = [
    ['Session', events[0]?.session_id || 'n/a'],
    ['Events', String(events.length)],
    ['Turns', String(count(events, 'turn.started'))],
    ['Tools', String(count(events, 'tool.called'))],
    ['Approvals', String(count(events, 'approval.requested'))],
  ];
  stats.innerHTML = cards
    .map(
      ([label, value]) => `
        <div class="stat">
          <small>${label}</small>
          <strong>${value}</strong>
        </div>
      `,
    )
    .join('');
}

function humanType(type) {
  return type.replace('.', ' / ');
}

function detailText(event) {
  if (event.type === 'tool.called') {
    return `${event.payload.name} ${JSON.stringify(event.payload.args || [])}`;
  }
  if (event.type === 'shell.started') {
    return event.payload.command;
  }
  if (event.type === 'shell.finished') {
    return `exit ${event.payload.exit_code}`;
  }
  if (event.type === 'file.changed') {
    return `${event.payload.path} - ${event.payload.summary}`;
  }
  if (event.type === 'subagent.spawned') {
    return `${event.payload.child_agent_id} (${event.payload.role})`;
  }
  if (event.type === 'approval.requested') {
    return `${event.payload.kind} / ${event.payload.reason}`;
  }
  if (event.type === 'approval.resolved') {
    return `${event.payload.kind} / ${event.payload.decision}`;
  }
  if (event.type === 'turn.started') {
    return event.payload.summary || 'turn started';
  }
  if (event.type === 'session.started') {
    return event.payload.task || 'session started';
  }
  return JSON.stringify(event.payload);
}

function renderTimeline(events) {
  timelineLabel.textContent = `${events.length} events`;
  timeline.innerHTML = events
    .map((event) => {
      const className = event.type.replace('.', '-');
      return `
        <div class="timeline-item ${className}">
          <div class="timeline-meta">${event.occurred_at}<br />${humanType(event.type)}</div>
          <div>
            <strong>${detailText(event)}</strong>
            <div class="timeline-meta">agent: ${event.agent_id || 'n/a'} | runtime: ${event.source.runtime}</div>
          </div>
        </div>
      `;
    })
    .join('');
}

function renderProcessTree(events) {
  const shells = events.filter((event) => event.type === 'shell.started' || event.type === 'shell.finished');
  if (!shells.length) {
    processTree.innerHTML = '<div class="process-node"><strong>No shell activity</strong></div>';
    return;
  }
  const started = events.filter((event) => event.type === 'shell.started');
  processTree.innerHTML = started
    .map((event) => {
      const finished = events.find(
        (candidate) => candidate.type === 'shell.finished' && candidate.payload.shell_id === event.payload.shell_id,
      );
      return `
        <div class="process-node">
          <strong>${event.payload.command}</strong>
          <small>shell id: ${event.payload.shell_id}</small>
          <small>parent shell: ${event.attributes.parent_shell_id || 'root'}</small>
          <small>exit: ${finished ? finished.payload.exit_code : 'running'}</small>
        </div>
      `;
    })
    .join('');
}

function renderDiffs(events) {
  const diffs = events.filter((event) => event.type === 'file.changed');
  diffList.innerHTML = diffs.length
    ? diffs
        .map(
          (event) => `
            <div class="diff-item">
              <strong>${event.payload.path}</strong>
              <small>${event.payload.summary}</small>
              <small>+${event.attributes.lines_added || 0} / -${event.attributes.lines_removed || 0}</small>
            </div>
          `,
        )
        .join('')
    : '<div class="diff-item"><strong>No file changes</strong></div>';
}

function renderAgentGraph(events) {
  const subagents = events.filter((event) => event.type === 'subagent.spawned');
  const lead = events.find((event) => event.agent_id)?.agent_id || 'lead';
  const nodes = [`<div class="agent-node lead"><strong>${lead}</strong><small>primary agent</small></div>`];
  subagents.forEach((event) => {
    nodes.push(
      `<div class="agent-node child"><strong>${event.payload.child_agent_id}</strong><small>${event.payload.role}</small></div>`,
    );
  });
  agentGraph.innerHTML = nodes.join('');
}

function renderRaw(events) {
  rawView.textContent = JSON.stringify(events[0] || {}, null, 2);
}

function render(events) {
  renderStats(events);
  renderTimeline(events);
  renderProcessTree(events);
  renderDiffs(events);
  renderAgentGraph(events);
  renderRaw(events);
}

document.getElementById('load-sample').addEventListener('click', () => {
  input.value = toNdjson(sampleEvents);
  render(sampleEvents);
});

document.getElementById('render-input').addEventListener('click', () => {
  try {
    const events = parseEvents(input.value);
    render(events);
  } catch (error) {
    alert(`Could not parse input: ${error.message}`);
  }
});

input.value = toNdjson(sampleEvents);
render(sampleEvents);
