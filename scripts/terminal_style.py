"""
Terminal SVG style constants for skill-issue visual assets.

Sci-fi dystopian palette — danger reds, amber warnings, dark backgrounds.
The kind of terminal that knows something is wrong.
"""

# === COLORS ===

# Background — nearly black with a hint of blue
BACKGROUND = "#0a0a0f"

# Border — subtle, doesn't distract
BORDER = "#333333"
BORDER_WIDTH = 1

# Text colors
PROMPT = "#ff3366"       # Danger red — we're past green terminals
OUTPUT_TEXT = "#e0e0e0"  # Light gray, easy to read
MUTED_TEXT = "#666666"   # De-emphasized info

# Semantic highlights
SCORE_HIGHLIGHT = "#ff9900"  # Amber for scores, metrics, numbers
WEAK_NODE = "#ff3366"        # Red for weak/needs-work
GOOD_NODE = "#00ff88"        # Green for strong/mastered
WARNING = "#ff9900"          # Amber warnings
ERROR = "#ff3366"            # Red errors

# Glitch effect colors (for special effects)
GLITCH_CYAN = "#00ffff"
GLITCH_MAGENTA = "#ff00ff"

# === FONTS ===

# Font stack — JetBrains Mono preferred, fallbacks for broad support
FONT_FAMILY = "'JetBrains Mono', 'Fira Code', 'SF Mono', 'Consolas', 'Courier New', monospace"
FONT_SIZE = 14
LINE_HEIGHT = 1.4

# === TERMINAL WINDOW ===

# macOS-style window chrome
WINDOW_CHROME_HEIGHT = 32
WINDOW_BUTTON_RADIUS = 6
WINDOW_BUTTON_SPACING = 20
WINDOW_BUTTON_COLORS = {
    "close": "#ff5f57",
    "minimize": "#febc2e",
    "maximize": "#28c840",
}

# Padding inside terminal
TERMINAL_PADDING_X = 16
TERMINAL_PADDING_Y = 12

# Default terminal dimensions
DEFAULT_WIDTH = 700
DEFAULT_HEIGHT = 400

# Corner radius
BORDER_RADIUS = 8


# === SVG GENERATION HELPERS ===

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_terminal_header(width: int = DEFAULT_WIDTH) -> str:
    """Generate SVG for macOS-style terminal window header."""
    buttons = []
    start_x = 16
    cy = WINDOW_CHROME_HEIGHT // 2

    for i, (name, color) in enumerate(WINDOW_BUTTON_COLORS.items()):
        cx = start_x + i * WINDOW_BUTTON_SPACING
        buttons.append(
            f'<circle cx="{cx}" cy="{cy}" r="{WINDOW_BUTTON_RADIUS}" fill="{color}"/>'
        )

    return f"""
    <rect width="{width}" height="{WINDOW_CHROME_HEIGHT}" fill="#1a1a1f" rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}"/>
    <rect x="0" y="{WINDOW_CHROME_HEIGHT - BORDER_RADIUS}" width="{width}" height="{BORDER_RADIUS}" fill="#1a1a1f"/>
    {''.join(buttons)}
    """


def generate_terminal_body(
    content_lines: list[str],
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> str:
    """
    Generate SVG for terminal body with content.

    content_lines: List of (text, color) tuples or plain strings.
    """
    y_offset = WINDOW_CHROME_HEIGHT + TERMINAL_PADDING_Y + FONT_SIZE

    lines_svg = []
    for i, line in enumerate(content_lines):
        if isinstance(line, tuple):
            text, color = line
        else:
            text = line
            color = OUTPUT_TEXT

        # Escape XML special characters
        text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

        y = y_offset + i * (FONT_SIZE * LINE_HEIGHT)
        lines_svg.append(
            f'<text x="{TERMINAL_PADDING_X}" y="{y}" '
            f'font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}" '
            f'fill="{color}">{text}</text>'
        )

    body_y = WINDOW_CHROME_HEIGHT
    body_height = height - WINDOW_CHROME_HEIGHT

    return f"""
    <rect x="0" y="{body_y}" width="{width}" height="{body_height}" fill="{BACKGROUND}"/>
    <rect x="0" y="{height - BORDER_RADIUS}" width="{width}" height="{BORDER_RADIUS}" fill="{BACKGROUND}" rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}"/>
    {''.join(lines_svg)}
    """


def generate_terminal_svg(
    content_lines: list,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    title: str = "skill-issue",
) -> str:
    """
    Generate complete terminal SVG with header and content.

    Args:
        content_lines: List of strings or (text, color) tuples
        width: Terminal width in pixels
        height: Terminal height in pixels
        title: Window title (displayed in header)

    Returns:
        Complete SVG string
    """
    header = generate_terminal_header(width)
    body = generate_terminal_body(content_lines, width, height)

    # Title in header
    title_svg = (
        f'<text x="{width // 2}" y="{WINDOW_CHROME_HEIGHT // 2 + 5}" '
        f'font-family="{FONT_FAMILY}" font-size="12" fill="{MUTED_TEXT}" '
        f'text-anchor="middle">{title}</text>'
    )

    # Border
    border_svg = (
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'fill="none" stroke="{BORDER}" stroke-width="{BORDER_WIDTH}" '
        f'rx="{BORDER_RADIUS}" ry="{BORDER_RADIUS}"/>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
{header}
{title_svg}
{body}
{border_svg}
</svg>"""


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    # Demo: generate a sample terminal screenshot
    sample_content = [
        ("$ skill-issue graph show", PROMPT),
        ("", OUTPUT_TEXT),
        ("Knowledge Graph: machine-learning", OUTPUT_TEXT),
        ("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", MUTED_TEXT),
        ("", OUTPUT_TEXT),
        ("  backpropagation ████████░░ 82%", GOOD_NODE),
        ("  gradient_descent █████████░ 91%", GOOD_NODE),
        ("  neural_networks  ██████░░░░ 64%", WARNING),
        ("  transformers     ███░░░░░░░ 31%", WEAK_NODE),
        ("  attention        ██░░░░░░░░ 23%", WEAK_NODE),
    ]

    svg = generate_terminal_svg(sample_content, title="skill-issue — graph show")
    print(svg)
