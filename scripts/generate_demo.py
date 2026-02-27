#!/usr/bin/env python3
"""Generate a synthetic asciinema cast file for the demo GIF."""

import json
import os
import subprocess
import time

def create_asciicast(output_path: str):
    """Create a synthetic asciicast v2 file showing skill-issue in action."""

    # Get real CLI output
    stats_result = subprocess.run(['skill-issue', 'stats'], capture_output=True, text=True)
    graph_result = subprocess.run(['skill-issue', 'graph', 'show', '--domain', 'machine-learning'],
                                   capture_output=True, text=True)

    # Header
    header = {
        "version": 2,
        "width": 80,
        "height": 30,
        "timestamp": int(time.time()),
        "env": {"SHELL": "/bin/zsh", "TERM": "xterm-256color"},
        "title": "skill-issue demo"
    }

    events = []
    t = 0.0

    def type_text(text: str, base_delay: float = 0.05) -> float:
        """Simulate typing with realistic delays."""
        nonlocal t
        for char in text:
            events.append([t, "o", char])
            t += base_delay + (0.02 if char in ' -' else 0)
        return t

    def output(text: str, delay: float = 0.0) -> float:
        """Output text immediately."""
        nonlocal t
        t += delay
        events.append([t, "o", text])
        return t

    def newline():
        output("\r\n")

    def wait(seconds: float):
        nonlocal t
        t += seconds

    # Scene 1: Show prompt and run stats
    output("$ ")
    wait(0.5)
    type_text("skill-issue stats")
    newline()
    wait(0.3)

    # Output stats with slight delay between lines
    for line in stats_result.stdout.split('\n'):
        output(line)
        newline()
        wait(0.05)

    wait(1.0)
    output("\r\n$ ")
    wait(0.5)

    # Scene 2: Show knowledge graph
    type_text("skill-issue graph show --domain machine-learning")
    newline()
    wait(0.3)

    for line in graph_result.stdout.split('\n'):
        output(line)
        newline()
        wait(0.03)

    wait(1.5)
    output("\r\n$ ")
    wait(0.3)
    type_text("# Your AI writes code. Does your brain keep up?")
    newline()
    wait(2.0)

    # Write the cast file
    with open(output_path, 'w') as f:
        f.write(json.dumps(header) + '\n')
        for event in events:
            f.write(json.dumps(event) + '\n')

    return output_path


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    demo_dir = os.path.join(project_dir, 'assets', 'demo')
    os.makedirs(demo_dir, exist_ok=True)

    cast_path = os.path.join(demo_dir, 'skill-issue-demo.cast')
    gif_path = os.path.join(demo_dir, 'skill-issue-demo.gif')

    print("Generating asciicast...")
    create_asciicast(cast_path)
    print(f"Created: {cast_path}")

    # Try to convert to GIF using agg
    try:
        result = subprocess.run(
            ['agg', '--font-family', 'SF Mono,Monaco,monospace',
             '--theme', 'dracula', cast_path, gif_path],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Created: {gif_path}")
        else:
            print(f"agg failed: {result.stderr}")
            print("Cast file ready for manual conversion with agg or asciinema-agg")
    except FileNotFoundError:
        print("agg not found. Cast file ready for manual conversion.")


if __name__ == '__main__':
    main()
