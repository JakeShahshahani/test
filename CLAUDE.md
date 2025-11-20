# CLAUDE.md - AI Assistant Guide

> **Repository**: JakeShahshahani/test
> **Last Updated**: 2025-11-20
> **Status**: Initial setup

This document provides guidance for AI assistants (like Claude) working with this codebase. It covers the repository structure, development workflows, conventions, and best practices.

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Structure](#codebase-structure)
3. [Development Workflow](#development-workflow)
4. [Coding Conventions](#coding-conventions)
5. [Testing Strategy](#testing-strategy)
6. [Common Tasks](#common-tasks)
7. [AI Assistant Guidelines](#ai-assistant-guidelines)
8. [Troubleshooting](#troubleshooting)

---

## Repository Overview

### Purpose
<!-- Update this section as the project develops -->
This repository is currently in its initial setup phase. The purpose and goals will be documented here as development progresses.

### Technology Stack
<!-- Update as technologies are adopted -->
- **Language**: TBD
- **Framework**: TBD
- **Build Tool**: TBD
- **Package Manager**: TBD
- **Testing Framework**: TBD

### Key Dependencies
<!-- List major dependencies as they're added -->
None yet - repository is in initial setup phase.

---

## Codebase Structure

### Directory Layout
```
.
├── .git/              # Git repository metadata
└── CLAUDE.md          # This file
```

### Recommended Structure
As the project grows, consider organizing code with the following structure:

```
.
├── src/               # Source code
│   ├── components/    # Reusable components
│   ├── utils/         # Utility functions
│   ├── services/      # Business logic/services
│   └── config/        # Configuration files
├── tests/             # Test files
├── docs/              # Documentation
├── scripts/           # Build/deployment scripts
├── .github/           # GitHub workflows and configs
├── package.json       # Dependencies (if Node.js)
├── README.md          # Project readme
└── CLAUDE.md          # This file
```

---

## Development Workflow

### Git Branching Strategy

**Main Branches:**
- `main` / `master` - Production-ready code
- `develop` - Integration branch for features

**Supporting Branches:**
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes
- `claude/*` - AI assistant working branches (ephemeral)

### Commit Message Guidelines

Follow conventional commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add user authentication system

Implement JWT-based authentication with login and registration endpoints

Closes #123
```

### Pull Request Process

1. Create a feature branch from `develop`
2. Make changes and commit with clear messages
3. Push to remote and create a PR
4. Ensure all tests pass
5. Request review from team members
6. Address feedback and merge when approved

---

## Coding Conventions

### General Principles

1. **Readability First**: Code should be self-documenting
2. **DRY (Don't Repeat Yourself)**: Extract common logic into reusable functions
3. **SOLID Principles**: Follow object-oriented design principles
4. **Consistent Naming**: Use clear, descriptive names

### Naming Conventions

**Variables & Functions:**
```
// Use camelCase for variables and functions
const userName = "John";
function getUserData() { }
```

**Classes:**
```
// Use PascalCase for classes
class UserService { }
```

**Constants:**
```
// Use UPPER_SNAKE_CASE for constants
const MAX_RETRY_ATTEMPTS = 3;
```

**Files:**
- Source files: lowercase with hyphens (e.g., `user-service.js`)
- Component files: PascalCase (e.g., `UserProfile.jsx`)
- Test files: `*.test.js` or `*.spec.js`

### Code Style

<!-- Update based on actual linters/formatters used -->
- Use a linter (ESLint, Pylint, etc.) to enforce consistency
- Use a formatter (Prettier, Black, etc.) for automatic formatting
- Configure pre-commit hooks to run linters/formatters

### Comments & Documentation

```javascript
/**
 * Calculates the total price including tax
 * @param {number} basePrice - The base price before tax
 * @param {number} taxRate - Tax rate as a decimal (e.g., 0.08 for 8%)
 * @returns {number} Total price including tax
 */
function calculateTotal(basePrice, taxRate) {
  return basePrice * (1 + taxRate);
}
```

**When to Comment:**
- Complex algorithms or business logic
- Non-obvious design decisions
- Public APIs and interfaces
- TODO items (use `// TODO: description`)

**When NOT to Comment:**
- Self-explanatory code
- Redundant descriptions of what code does

---

## Testing Strategy

### Test Levels

1. **Unit Tests**: Test individual functions/components in isolation
2. **Integration Tests**: Test interactions between components
3. **E2E Tests**: Test complete user workflows

### Test Organization

```
tests/
├── unit/
│   ├── utils.test.js
│   └── services.test.js
├── integration/
│   └── api.test.js
└── e2e/
    └── user-flow.test.js
```

### Testing Guidelines

- **Coverage Goal**: Aim for 80%+ code coverage
- **Test Naming**: Describe what's being tested and expected outcome
  ```javascript
  test('should return user data when valid ID is provided', () => {
    // test implementation
  });
  ```
- **Arrange-Act-Assert**: Structure tests clearly
  ```javascript
  test('example test', () => {
    // Arrange: Set up test data
    const input = 5;

    // Act: Execute the function
    const result = double(input);

    // Assert: Verify the result
    expect(result).toBe(10);
  });
  ```

### Running Tests

```bash
# Run all tests
npm test  # or equivalent

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test path/to/test.js

# Run in watch mode
npm test -- --watch
```

---

## Common Tasks

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd test

# Install dependencies
# (command depends on package manager)

# Run development server
# (command TBD)
```

### Adding a New Feature

1. Create feature branch: `git checkout -b feature/feature-name`
2. Implement feature with tests
3. Run tests: `npm test`
4. Commit changes: `git commit -m "feat: add feature description"`
5. Push: `git push -u origin feature/feature-name`
6. Create pull request

### Debugging

<!-- Update with project-specific debugging tools -->
- Use debugger statements or IDE debugging tools
- Check logs in appropriate locations
- Use browser DevTools for frontend issues

### Building for Production

```bash
# Build command (TBD based on build tool)
npm run build

# Verify build
# (verification steps TBD)
```

---

## AI Assistant Guidelines

### When Working on This Codebase

**DO:**
- ✅ Read existing code before making changes
- ✅ Follow established patterns and conventions
- ✅ Write tests for new functionality
- ✅ Update documentation when making significant changes
- ✅ Use descriptive commit messages
- ✅ Check for security vulnerabilities (SQL injection, XSS, etc.)
- ✅ Prefer editing existing files over creating new ones
- ✅ Use TodoWrite tool to track multi-step tasks
- ✅ Ask for clarification when requirements are ambiguous

**DON'T:**
- ❌ Make breaking changes without discussion
- ❌ Skip writing tests
- ❌ Commit commented-out code
- ❌ Use overly clever or obscure code
- ❌ Ignore linter warnings
- ❌ Create unnecessary files
- ❌ Push directly to main/master branch
- ❌ Commit sensitive data (API keys, passwords, etc.)

### Code Review Checklist

Before submitting changes, verify:

- [ ] Code follows project conventions
- [ ] All tests pass
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] No sensitive data in commits
- [ ] Commit messages are clear and descriptive
- [ ] Code is readable and maintainable

### Security Considerations

**Always check for:**
- Input validation and sanitization
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) attacks
- CSRF (Cross-Site Request Forgery) protection
- Authentication and authorization issues
- Secure handling of sensitive data
- Proper error handling (don't expose internals)

**Example - Input Validation:**
```javascript
// BAD - Direct use of user input
const query = `SELECT * FROM users WHERE id = ${userId}`;

// GOOD - Parameterized query
const query = 'SELECT * FROM users WHERE id = ?';
db.execute(query, [userId]);
```

### Performance Considerations

- Avoid N+1 queries in database operations
- Use pagination for large datasets
- Implement caching where appropriate
- Optimize loops and iterations
- Lazy load resources when possible

### Accessibility

- Use semantic HTML
- Provide alt text for images
- Ensure keyboard navigation works
- Maintain proper heading hierarchy
- Test with screen readers

---

## Troubleshooting

### Common Issues

<!-- Add common issues and solutions as they're discovered -->

**Issue**: Repository is empty
**Solution**: This is a new repository. Start by adding project files and configuration.

---

### Getting Help

- Check existing documentation in `docs/`
- Review closed issues on GitHub
- Check commit history for context: `git log`
- Ask repository maintainers for clarification

---

## Project Evolution

### Next Steps for Repository Setup

As this repository develops, consider:

1. **Choose Tech Stack**: Decide on programming language and framework
2. **Add Configuration**: Set up linters, formatters, and build tools
3. **Create Directory Structure**: Organize code according to the recommended structure
4. **Set Up CI/CD**: Add GitHub Actions or similar for automated testing
5. **Add Pre-commit Hooks**: Ensure code quality before commits
6. **Create Templates**: Add issue and PR templates
7. **Document Setup**: Create detailed setup instructions in README.md
8. **Update This File**: Keep CLAUDE.md in sync with project evolution

### Maintaining This Document

This file should be updated when:
- New conventions are established
- Technology stack changes
- Directory structure is modified
- New development tools are adopted
- Common patterns emerge that should be documented

**Assigned Maintainer**: Repository owner and contributors

---

## Appendix

### Useful Commands

```bash
# Git
git status                    # Check current status
git log --oneline            # View commit history
git branch -a                # List all branches
git diff                     # View changes

# Development (update as project tools are chosen)
# npm install                # Install dependencies
# npm run dev                # Start development server
# npm test                   # Run tests
# npm run build              # Build for production
```

### Resources

- [Git Documentation](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

**Document Version**: 1.0.0
**Last Modified**: 2025-11-20
**Contributors**: AI Assistant (Claude)
