# Contributing to Roguelike

Thank you for considering contributing to this project. The following guidelines are established to maintain the quality and consistency of the project.

## Development Environment Setup

1. Clone the repository and set up the development environment:

```bash
git clone https://github.com/your-username/roguelike.git
cd roguelike
poetry install
```

2. Install pre-commit hooks:

```bash
poetry run pre-commit install
```

## Coding Standards

### Python Code Style

- All new code must include **type hints**
- Code must be formatted with `black` with a line length limit of 120 characters
- Imports must be sorted using `isort`
- Must follow `flake8` rules

### Commit Message Guidelines

Commit messages should follow this format:

```
[type]: Brief description

Detailed description (if needed)
```

Types to use:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes only
- `style`: Changes that do not affect code behavior (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Changes to build process or tools

### Pull Request Process

1. Create a new branch for your feature or bug fix
2. Implement changes and add or update tests
3. Ensure all tests pass
4. Create a pull request

## Testing

- Always add tests for new features
- Ensure existing tests don't fail
- Run tests using `pytest`:

```bash
poetry run pytest
```

## Documentation

- Add appropriate documentation for new features
- Write docstrings in Google format
- Update `README.md` for significant changes

## Debugging and Logging

- Debug information is recorded in `logs/debug.log`
- Errors are recorded in `logs/error.log`
- Set appropriate log levels:
  - `DEBUG`: Detailed debug information
  - `INFO`: General information
  - `WARNING`: Warnings
  - `ERROR`: Errors
  - `CRITICAL`: Critical errors

## Questions and Issues

- Create an Issue for bugs
- Use Discussions for questions
- Contact maintainers directly for security vulnerabilities 