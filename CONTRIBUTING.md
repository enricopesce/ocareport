# Contributing to ocareport

Thank you for your interest in contributing to ocareport! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/ocareport.git
   cd ocareport
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Development Workflow

1. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure tests pass:
   ```bash
   pytest test_ocareport.py -v
   ```

3. Commit your changes with a descriptive message:
   ```bash
   git commit -m "Add feature: brief description"
   ```

4. Push to your fork and create a Pull Request

## Code Style

- Follow PEP 8 guidelines for Python code
- Use meaningful variable and function names
- Add docstrings to functions and modules
- Keep functions focused and concise

## Testing

- All new features should include tests
- Run the test suite before submitting:
  ```bash
  pytest test_ocareport.py -v
  ```
- Ensure existing tests still pass

## Reporting Issues

When reporting issues, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, OCI SDK version)
- Any relevant error messages

## Pull Request Guidelines

- Keep PRs focused on a single change
- Update documentation if needed
- Add tests for new functionality
- Ensure all tests pass
- Write clear commit messages

## Questions?

Feel free to open an issue for any questions about contributing.

Thank you for helping improve ocareport!
