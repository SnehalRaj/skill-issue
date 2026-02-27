#!/usr/bin/env python3
"""D3.js web visualization generator for the knowledge graph."""

import json
from skill_issue.knowledge_state import load_graph, get_all_nodes, get_weak_nodes


def generate_html(domain: str) -> str:
    """Generate self-contained HTML with D3.js force-directed graph."""
    graph = load_graph(domain)
    nodes_data = get_all_nodes(domain)
    weak_nodes = get_weak_nodes(domain, top_n=5)
    weak_ids = {n[0] for n in weak_nodes}

    # Build nodes and links for D3
    nodes = []
    links = []
    node_ids = {n["id"] for n in graph["nodes"]}

    for node_id, node_info, node_state in nodes_data:
        nodes.append({
            "id": node_id,
            "name": node_info["name"],
            "description": node_info["description"],
            "reuse_weight": node_info["reuse_weight"],
            "mastery": node_state["mastery"],
            "status": node_state["status"],
            "attempts": node_state["attempts"],
            "last_seen": node_state["last_seen"],
            "challenge_hooks": node_info.get("challenge_hooks", []),
            "is_priority": node_id in weak_ids,
        })

        # Add links for prerequisites and related
        for prereq in node_info.get("prerequisites", []):
            if prereq in node_ids:
                links.append({"source": prereq, "target": node_id, "type": "prerequisite"})
        for related in node_info.get("related", []):
            if related in node_ids and related != node_id:
                links.append({"source": node_id, "target": related, "type": "related"})

    # Deduplicate links
    seen_links = set()
    unique_links = []
    for link in links:
        key = tuple(sorted([link["source"], link["target"]])) + (link["type"],)
        if key not in seen_links:
            seen_links.add(key)
            unique_links.append(link)

    graph_data = json.dumps({"nodes": nodes, "links": unique_links})

    return HTML_TEMPLATE.replace("{{GRAPH_DATA}}", graph_data).replace("{{DOMAIN}}", domain)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph: {{DOMAIN}}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            overflow: hidden;
        }
        #container { display: flex; height: 100vh; }
        #graph { flex: 1; position: relative; }
        #sidebar {
            width: 320px;
            background: #161b22;
            border-left: 1px solid #30363d;
            padding: 20px;
            overflow-y: auto;
        }
        h1 { font-size: 18px; color: #58a6ff; margin-bottom: 8px; }
        h2 { font-size: 14px; color: #8b949e; margin: 16px 0 8px; text-transform: uppercase; }
        .node-info { display: none; }
        .node-info.active { display: block; }
        .node-name { font-size: 20px; font-weight: 600; color: #f0f6fc; margin-bottom: 4px; }
        .node-id { font-size: 12px; color: #8b949e; margin-bottom: 12px; }
        .stat { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #30363d; }
        .stat-label { color: #8b949e; }
        .stat-value { font-weight: 500; }
        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-mastered { background: #238636; color: #fff; }
        .status-strong { background: #1f6feb; color: #fff; }
        .status-developing { background: #9e6a03; color: #fff; }
        .status-weak { background: #da3633; color: #fff; }
        .challenge-hooks { margin-top: 16px; }
        .hook {
            background: #21262d;
            padding: 10px 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
            border-left: 3px solid #58a6ff;
        }
        .legend { margin-top: 20px; }
        .legend-item { display: flex; align-items: center; margin: 6px 0; font-size: 12px; }
        .legend-circle {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .instructions { font-size: 12px; color: #8b949e; margin-top: 20px; line-height: 1.5; }
        svg { width: 100%; height: 100%; }
        .link { stroke-opacity: 0.4; }
        .link-prerequisite { stroke: #58a6ff; }
        .link-related { stroke: #8b949e; stroke-dasharray: 4,4; }
        .node circle { cursor: pointer; stroke-width: 2px; }
        .node text {
            font-size: 10px;
            fill: #c9d1d9;
            pointer-events: none;
            text-anchor: middle;
            dominant-baseline: middle;
        }
        .node.priority circle { stroke: #f0883e !important; stroke-width: 3px; }
        .tooltip {
            position: absolute;
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.15s;
            max-width: 250px;
        }
        .tooltip.visible { opacity: 1; }
        .mastery-bar {
            height: 4px;
            background: #30363d;
            border-radius: 2px;
            margin-top: 4px;
        }
        .mastery-fill {
            height: 100%;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="graph">
            <div class="tooltip" id="tooltip"></div>
        </div>
        <div id="sidebar">
            <h1>Knowledge Graph</h1>
            <div style="color: #8b949e; font-size: 13px;">{{DOMAIN}}</div>

            <div id="default-info">
                <h2>Instructions</h2>
                <div class="instructions">
                    <strong>Click</strong> a node to see details<br>
                    <strong>Drag</strong> nodes to rearrange<br>
                    <strong>Hover</strong> for quick info
                </div>

                <h2>Legend</h2>
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-circle" style="background: #238636;"></div>
                        <span>Mastered (>85%)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-circle" style="background: #1f6feb;"></div>
                        <span>Strong (>70%)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-circle" style="background: #9e6a03;"></div>
                        <span>Developing (>40%)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-circle" style="background: #da3633;"></div>
                        <span>Weak (<40%)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-circle" style="background: #484f58;"></div>
                        <span>Unseen</span>
                    </div>
                    <div class="legend-item" style="margin-top: 12px;">
                        <div class="legend-circle" style="background: transparent; border: 2px solid #f0883e;"></div>
                        <span>Priority (focus here)</span>
                    </div>
                </div>
            </div>

            <div id="node-info" class="node-info">
                <h2>Selected Node</h2>
                <div class="node-name" id="info-name"></div>
                <div class="node-id" id="info-id"></div>
                <p id="info-description" style="font-size: 13px; line-height: 1.5; margin-bottom: 16px;"></p>

                <div class="stat">
                    <span class="stat-label">Status</span>
                    <span class="stat-value"><span id="info-status" class="status-badge"></span></span>
                </div>
                <div class="stat">
                    <span class="stat-label">Mastery</span>
                    <span class="stat-value" id="info-mastery"></span>
                </div>
                <div class="stat">
                    <span class="stat-label">Reuse Weight</span>
                    <span class="stat-value" id="info-weight"></span>
                </div>
                <div class="stat">
                    <span class="stat-label">Attempts</span>
                    <span class="stat-value" id="info-attempts"></span>
                </div>
                <div class="stat">
                    <span class="stat-label">Last Seen</span>
                    <span class="stat-value" id="info-lastseen"></span>
                </div>

                <div class="challenge-hooks">
                    <h2>Challenge Hooks</h2>
                    <div id="info-hooks"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const data = {{GRAPH_DATA}};

        const container = document.getElementById('graph');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const statusColor = (status) => ({
            'mastered': '#238636',
            'strong': '#1f6feb',
            'developing': '#9e6a03',
            'weak': '#da3633',
        }[status] || '#484f58');

        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g');

        // Zoom
        svg.call(d3.zoom()
            .scaleExtent([0.3, 3])
            .on('zoom', (event) => g.attr('transform', event.transform)));

        // Simulation
        const simulation = d3.forceSimulation(data.nodes)
            .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(d => 20 + d.reuse_weight * 20));

        // Links
        const link = g.append('g')
            .selectAll('line')
            .data(data.links)
            .join('line')
            .attr('class', d => `link link-${d.type}`)
            .attr('stroke-width', 1.5);

        // Nodes
        const node = g.append('g')
            .selectAll('g')
            .data(data.nodes)
            .join('g')
            .attr('class', d => `node ${d.is_priority ? 'priority' : ''}`)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        node.append('circle')
            .attr('r', d => 10 + d.reuse_weight * 15)
            .attr('fill', d => statusColor(d.status))
            .attr('stroke', d => d.is_priority ? '#f0883e' : statusColor(d.status));

        node.append('text')
            .attr('dy', d => 20 + d.reuse_weight * 15)
            .text(d => d.id.split('-').slice(0, 2).join('-'));

        // Tooltip
        const tooltip = document.getElementById('tooltip');

        node.on('mouseover', (event, d) => {
            tooltip.innerHTML = `
                <strong>${d.name}</strong><br>
                Mastery: ${(d.mastery * 100).toFixed(0)}%
                <div class="mastery-bar">
                    <div class="mastery-fill" style="width: ${d.mastery * 100}%; background: ${statusColor(d.status)};"></div>
                </div>
            `;
            tooltip.classList.add('visible');
        })
        .on('mousemove', (event) => {
            tooltip.style.left = (event.pageX + 10) + 'px';
            tooltip.style.top = (event.pageY - 10) + 'px';
        })
        .on('mouseout', () => {
            tooltip.classList.remove('visible');
        })
        .on('click', (event, d) => {
            showNodeInfo(d);
        });

        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });

        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }

        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }

        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }

        function showNodeInfo(d) {
            document.getElementById('default-info').style.display = 'none';
            document.getElementById('node-info').classList.add('active');

            document.getElementById('info-name').textContent = d.name;
            document.getElementById('info-id').textContent = d.id;
            document.getElementById('info-description').textContent = d.description;

            const statusEl = document.getElementById('info-status');
            statusEl.textContent = d.status;
            statusEl.className = `status-badge status-${d.status}`;

            document.getElementById('info-mastery').textContent = `${(d.mastery * 100).toFixed(0)}%`;
            document.getElementById('info-weight').textContent = d.reuse_weight.toFixed(2);
            document.getElementById('info-attempts').textContent = d.attempts;
            document.getElementById('info-lastseen').textContent = d.last_seen
                ? new Date(d.last_seen).toLocaleDateString()
                : 'Never';

            const hooksEl = document.getElementById('info-hooks');
            hooksEl.innerHTML = d.challenge_hooks.map(h => `<div class="hook">${h}</div>`).join('');
        }
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import sys
    domain = sys.argv[1] if len(sys.argv) > 1 else "quantum-ml"
    html = generate_html(domain)
    print(html)
