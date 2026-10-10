# MUCHackatonFinal

Our team's project for the MUC Hackathon.

## Overview

_Short description of the problem we're solving and our approach. (TBD)_

## Features

- _Feature 1 (TBD)_
- _Feature 2 (TBD)_
- _Feature 3 (TBD)_

## Tech Stack

_List languages, frameworks, and services used. (TBD)_

## Getting Started

### Prerequisites

- Git
- _Other requirements (TBD)_

### Installation

```bash
git clone https://github.com/aldfjla/MUCHackatonFinal.git
cd MUCHackatonFinal
# install dependencies (TBD)
```

### Running

```bash
cd agent && uv sync --all-extras
uv run arena play case:P01 --agent confident -v   # needs ARENA_API_KEY in agent/.env
```

## Project Structure

```
.
├── .claude/    # Claude Code settings and hooks
├── .entire/    # Entire session tracking config
└── README.md
```

## Development Notes

This repo uses [Claude Code](https://claude.com/claude-code) with Entire session tracking. The hooks in `.claude/settings.json` only run if the `entire` CLI is installed; otherwise they are skipped.

## Team

- _Name — role (TBD)_

## License

_TBD_
