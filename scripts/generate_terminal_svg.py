#!/usr/bin/env python3
"""Generate SVG screenshots of terminal output for README."""

import subprocess
import html


def terminal_to_svg(output: str, title: str = "Terminal", width: int = 700) -> str:
    """Convert terminal output to an SVG image with a macOS-style window chrome."""
    lines = output.split('\n')
    line_height = 20
    padding = 20
    header_height = 40
    height = header_height + (len(lines) * line_height) + (padding * 2)

    # ANSI color mapping
    colors = {
        'default': '#c9d1d9',
        'green': '#22c55e',
        'yellow': '#eab308',
        'red': '#ef4444',
        'blue': '#3b82f6',
        'magenta': '#a855f7',
        'cyan': '#06b6d4',
        'gray': '#6b7280',
        'orange': '#f97316',
    }

    def parse_ansi(text: str) -> list:
        """Parse ANSI codes and return list of (text, color) tuples."""
        import re
        parts = []
        current_color = 'default'

        # Pattern for ANSI escape codes
        ansi_pattern = re.compile(r'\x1b\[([0-9;]*)m')

        last_end = 0
        for match in ansi_pattern.finditer(text):
            # Add text before this escape code
            if match.start() > last_end:
                parts.append((text[last_end:match.start()], current_color))

            # Parse the escape code
            code = match.group(1)
            if code in ('0', ''):
                current_color = 'default'
            elif code == '32' or code == '1;32':
                current_color = 'green'
            elif code == '33' or code == '1;33':
                current_color = 'yellow'
            elif code == '31' or code == '1;31':
                current_color = 'red'
            elif code == '34' or code == '1;34':
                current_color = 'blue'
            elif code == '35' or code == '1;35':
                current_color = 'magenta'
            elif code == '36' or code == '1;36':
                current_color = 'cyan'
            elif code == '90' or code == '37':
                current_color = 'gray'

            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            parts.append((text[last_end:], current_color))

        return parts if parts else [(text, 'default')]

    def render_line(text: str, y: int) -> str:
        """Render a single line with color support."""
        # Handle Unicode block characters for progress bars
        text = text.replace('█', '█').replace('░', '░')

        # Simple colored rendering based on content patterns
        x = padding
        spans = []

        # Color [GOOD] green, [WEAK] orange
        if '[GOOD]' in text:
            text = text.replace('[GOOD]', '<tspan fill="#22c55e">[GOOD]</tspan>')
        if '[WEAK]' in text:
            text = text.replace('[WEAK]', '<tspan fill="#f97316">[WEAK]</tspan>')

        # Color the progress bars
        text = text.replace('████', '<tspan fill="#22c55e">████</tspan>')
        text = text.replace('███', '<tspan fill="#22c55e">███</tspan>')
        text = text.replace('██', '<tspan fill="#22c55e">██</tspan>')
        text = text.replace('█', '<tspan fill="#22c55e">█</tspan>')
        text = text.replace('░', '<tspan fill="#374151">░</tspan>')

        # Color priority arrows
        text = text.replace('▶', '<tspan fill="#eab308">▶</tspan>')

        # Color header lines
        if text.startswith('Knowledge Graph:') or text.startswith('Priority Queue'):
            text = f'<tspan fill="#a855f7">{text}</tspan>'
        if '=====' in text or '-----' in text:
            text = f'<tspan fill="#6b7280">{text}</tspan>'

        # Color stats output
        if '🧠' in text or 'skill-issue' in text:
            text = f'<tspan fill="#a855f7">{text}</tspan>'
        if 'Level:' in text or 'Streak:' in text or 'Accuracy:' in text:
            parts = text.split(':')
            if len(parts) == 2:
                text = f'<tspan fill="#6b7280">{parts[0]}:</tspan><tspan fill="#22c55e">{parts[1]}</tspan>'
        if '🔥' in text:
            text = text.replace('🔥', '<tspan fill="#f97316">🔥</tspan>')

        return f'  <text x="{x}" y="{y}" fill="{colors["default"]}">{html.escape(text) if "<tspan" not in text else text}</text>'

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '  <defs>',
        '    <linearGradient id="header-grad" x1="0%" y1="0%" x2="0%" y2="100%">',
        '      <stop offset="0%" style="stop-color:#3d3d3d"/>',
        '      <stop offset="100%" style="stop-color:#2d2d2d"/>',
        '    </linearGradient>',
        '  </defs>',
        '',
        '  <!-- Window background -->',
        f'  <rect width="{width}" height="{height}" rx="8" fill="#1a1b26"/>',
        '',
        '  <!-- Window header -->',
        f'  <rect width="{width}" height="{header_height}" rx="8" fill="url(#header-grad)"/>',
        f'  <rect y="{header_height - 8}" width="{width}" height="8" fill="url(#header-grad)"/>',
        '',
        '  <!-- Traffic lights -->',
        '  <circle cx="20" cy="20" r="6" fill="#ff5f57"/>',
        '  <circle cx="40" cy="20" r="6" fill="#febc2e"/>',
        '  <circle cx="60" cy="20" r="6" fill="#28c840"/>',
        '',
        '  <!-- Title -->',
        f'  <text x="{width // 2}" y="25" text-anchor="middle" fill="#808080" font-family="SF Mono, Monaco, monospace" font-size="13">{html.escape(title)}</text>',
        '',
        '  <!-- Terminal content -->',
        f'  <g font-family="SF Mono, Monaco, Consolas, monospace" font-size="13">',
    ]

    y = header_height + padding + 15
    for line in lines:
        # Escape HTML but preserve our tspan tags
        safe_line = html.escape(line)
        # Re-apply coloring after escaping
        if '[GOOD]' in safe_line:
            safe_line = safe_line.replace('[GOOD]', '<tspan fill="#22c55e">[GOOD]</tspan>')
        if '[WEAK]' in safe_line:
            safe_line = safe_line.replace('[WEAK]', '<tspan fill="#f97316">[WEAK]</tspan>')
        if '▶' in line:
            safe_line = safe_line.replace('▶', '<tspan fill="#eab308">▶</tspan>')
        if safe_line.startswith('Knowledge Graph:') or safe_line.startswith('Priority Queue'):
            safe_line = f'<tspan fill="#a855f7">{safe_line}</tspan>'
        if '=====' in safe_line or '-----' in safe_line:
            safe_line = f'<tspan fill="#4b5563">{safe_line}</tspan>'
        if '🧠' in safe_line:
            safe_line = f'<tspan fill="#a855f7">{safe_line}</tspan>'

        svg_lines.append(f'    <text x="{padding}" y="{y}" fill="{colors["default"]}">{safe_line}</text>')
        y += line_height

    svg_lines.extend([
        '  </g>',
        '</svg>',
    ])

    return '\n'.join(svg_lines)


def main():
    import os

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
