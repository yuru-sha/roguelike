# Roguelike Game

A classic roguelike game implemented in Python using TCOD library, featuring traditional dungeon crawling gameplay with modern programming practices.

## Features

- Traditional roguelike gameplay mechanics
- Procedurally generated dungeons
- Turn-based combat system
- Item and inventory management
- Save/Load game functionality
- Entity Component System (ECS) architecture

## Requirements

- Python 3.12 or higher
- Poetry (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yuru-sha/roguelike.git
cd roguelike
```

2. Install dependencies using Poetry:
```bash
poetry install
```

## Running the Game

To start the game:

```bash
poetry run roguelike
```

## Development

### Project Structure

```
src/roguelike/
├── core/           # Core game engine and systems
├── game/           # Game logic and mechanics
├── world/          # World generation and management
├── ui/             # User interface components
├── data/           # Game data and assets
└── utils/          # Utility functions
```

### Development Tools

- **Black**: Code formatting
- **MyPy**: Static type checking
- **Flake8**: Code linting
- **isort**: Import sorting
- **pytest**: Testing framework

### Running Tests

```bash
poetry run pytest
```

### Code Style

This project follows strict Python coding standards:
- Type hints are required for all functions
- Maximum line length is 120 characters
- Code is formatted using Black
- Imports are sorted using isort

## Acknowledgments

- **Project Planning**: yuru-sha - Project planner and concept creator
- **Development & Documentation**: Cursor AI - Main development and documentation
- **TCOD Library**: For providing the core roguelike functionality
- **Original Rogue**: For inspiring this project and the roguelike genre

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 