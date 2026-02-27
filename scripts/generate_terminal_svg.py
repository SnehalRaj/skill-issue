#!/usr/bin/env python3
"""Generate SVG screenshots of terminal output for README.

Uses the danger palette from terminal_style.py for consistent visual identity.
"""

import subprocess
import html
import os
import sys

# Add scripts dir to path for import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from terminal_style import (
    BACKGROUND,
    PROMPT,
    OUTPUT_TEXT,
    MUTED_TEXT,
    SCORE_HIGHLIGHT,
    WEAK_NODE,
    GOOD_NODE,
    WARNING,
    FONT_FAMILY,
    WINDOW_BUTTON_COLORS,
    BORDER_RADIUS,
)


def terminal_to_svg(output: str, title: str = "Terminal", width: int = 700) -> str:
    """Convert terminal output to an SVG image with macOS-style window chrome.

    Uses the sci-fi dystopian danger palette from terminal_style.py.
    """
    lines = output.split('\n')
    line_height = 20
    padding = 20
    header_height = 40
    height = header_height + (len(lines) * line_height) + (padding * 2)

    # Color mapping using danger palette
    colors = {
        'default': OUTPUT_TEXT,
        'green': GOOD_NODE,
        'yellow': WARNING,
        'red': WEAK_NODE,
        'blue': '#3b82f6',
        'magenta': SCORE_HIGHLIGHT,  # Use amber for emphasis
        'cyan': '#06b6d4',
        'gray': MUTED_TEXT,
        'orange': WARNING,
        'prompt': PROMPT,
    }

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '  <defs>',
        '    <linearGradient id="header-grad" x1="0%" y1="0%" x2="0%" y2="100%">',
        '      <stop offset="0%" style="stop-color:#1a1a1f"/>',
        '      <stop offset="100%" style="stop-color:#0f0f12"/>',
        '    </linearGradient>',
        '  </defs>',
        '',
        '  <!-- Window background with danger palette -->',
        f'  <rect width="{width}" height="{height}" rx="{BORDER_RADIUS}" fill="{BACKGROUND}"/>',
        '',
        '  <!-- Window header -->',
        f'  <rect width="{width}" height="{header_height}" rx="{BORDER_RADIUS}" fill="url(#header-grad)"/>',
        f'  <rect y="{header_height - BORDER_RADIUS}" width="{width}" height="{BORDER_RADIUS}" fill="url(#header-grad)"/>',
        '',
        '  <!-- Traffic lights -->',
        f'  <circle cx="20" cy="20" r="6" fill="{WINDOW_BUTTON_COLORS["close"]}"/>',
        f'  <circle cx="40" cy="20" r="6" fill="{WINDOW_BUTTON_COLORS["minimize"]}"/>',
        f'  <circle cx="60" cy="20" r="6" fill="{WINDOW_BUTTON_COLORS["maximize"]}"/>',
        '',
        '  <!-- Title -->',
        f'  <text x="{width // 2}" y="25" text-anchor="middle" fill="{MUTED_TEXT}" font-family="{FONT_FAMILY}" font-size="12">{html.escape(title)}</text>',
        '',
        '  <!-- Terminal content -->',
        f'  <g font-family="{FONT_FAMILY}" font-size="13">',
    ]

    y = header_height + padding + 15
    for line in lines:
        # Escape HTML first
        safe_line = html.escape(line)

        # Apply danger palette coloring

        # [GOOD] = green, [WEAK] = danger red
        if '[GOOD]' in safe_line:
            safe_line = safe_line.replace('[GOOD]', f'<tspan fill="{GOOD_NODE}">[GOOD]</tspan>')
        if '[WEAK]' in safe_line:
            safe_line = safe_line.replace('[WEAK]', f'<tspan fill="{WEAK_NODE}">[WEAK]</tspan>')

        # Priority arrows = amber warning
        if '▶' in line:
            safe_line = safe_line.replace('▶', f'<tspan fill="{WARNING}">▶</tspan>')

        # Headers = amber for emphasis
        if safe_line.startswith('Knowledge Graph:') or safe_line.startswith('Priority Queue'):
            safe_line = f'<tspan fill="{SCORE_HIGHLIGHT}">{safe_line}</tspan>'

        # Separators = muted
        if '=====' in safe_line or '-----' in safe_line:
            safe_line = f'<tspan fill="{MUTED_TEXT}">{safe_line}</tspan>'

        # Stats with brain emoji = amber
        if '🧠' in safe_line:
            safe_line = f'<tspan fill="{SCORE_HIGHLIGHT}">{safe_line}</tspan>'

        # Progress bars: full blocks = green, empty = muted
        safe_line = safe_line.replace('█', f'<tspan fill="{GOOD_NODE}">█</tspan>')
        safe_line = safe_line.replace('░', f'<tspan fill="{MUTED_TEXT}">░</tspan>')

        svg_lines.append(f'    <text x="{padding}" y="{y}" fill="{colors["default"]}">{safe_line}</text>')
        y += line_height

    svg_lines.extend([
        '  </g>',
        '</svg>',
    ])

    return '\n'.join(svg_lines)


def main():
    assets_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    screenshots_dir = os.path.join(assets_dir, 'assets', 'screenshots')
    os.makedirs(screenshots_dir, exist_ok=True)

    # Generate graph show screenshot
    result = subprocess.run(
        ['skill-issue', 'graph', 'show', '--domain', 'machine-learning'],
        capture_output=True, text=True
    )
    graph_svg = terminal_to_svg(result.stdout.strip(), 'skill-issue graph show --domain machine-learning')
    with open(os.path.join(screenshots_dir, 'graph-show.svg'), 'w') as f:
        f.write(graph_svg)
    print(f"Generated: {screenshots_dir}/graph-show.svg")

    # Generate stats screenshot
    result = subprocess.run(
        ['skill-issue', 'stats'],
        capture_output=True, text=True
    )
    stats_svg = terminal_to_svg(result.stdout.strip(), 'skill-issue stats', width=500)
    with open(os.path.join(screenshots_dir, 'stats.svg'), 'w') as f:
        f.write(stats_svg)
    print(f"Generated: {screenshots_dir}/stats.svg")

    # Generate weak nodes screenshot
    result = subprocess.run(
        ['skill-issue', 'graph', 'weak', '--domain', 'machine-learning'],
        capture_output=True, text=True
    )
    weak_svg = terminal_to_svg(result.stdout.strip(), 'skill-issue graph weak --domain machine-learning', width=600)
    with open(os.path.join(screenshots_dir, 'graph-weak.svg'), 'w') as f:
        f.write(weak_svg)
    print(f"Generated: {screenshots_dir}/graph-weak.svg")


if __name__ == '__main__':
    main()
