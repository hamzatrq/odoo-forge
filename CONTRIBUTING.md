# Contributing to OdooForge

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or pip
- **Docker** and **Docker Compose** (for integration testing)

### Clone & Install

```bash
git clone https://github.com/hamzatrq/odoo-forge.git
cd odooforge

# Install with dev dependencies
uv sync --group dev

# Or with pip
pip install -e ".[dev]"
```

### Running Locally

```bash
# Start the MCP server
uv run odooforge

# Start an Odoo instance (optional, for integration testing)
docker compose -f docker/docker-compose.yml up -d
```

## Testing

### Run All Tests

```bash
uv run pytest tests/ -v
```

### Run Specific Test Suites

```bash
# Unit tests only
uv run pytest tests/test_tools.py tests/test_utils.py -v

# Edge case tests
uv run pytest tests/test_edge_cases.py -v

# Connection tests
uv run pytest tests/test_xmlrpc.py tests/test_docker.py -v
```

### Writing Tests

- All tests go in `tests/`
- Use `pytest` with `pytest-asyncio` for async tests
- Mock external dependencies (Docker, XML-RPC, PostgreSQL)
- See `tests/test_edge_cases.py` for comprehensive examples

## Project Structure

```
src/odooforge/
├── server.py              # MCP server entry point (79 tools, 5 resources, 4 prompts)
├── config.py              # Environment configuration
├── connections/           # External service clients
│   ├── docker_client.py   # Docker Compose management
│   ├── xmlrpc_client.py   # Odoo XML-RPC interface
│   └── pg_client.py       # PostgreSQL direct connection
├── tools/                 # Tool implementations (one file per category)
│   ├── records.py         # CRUD operations
│   ├── modules.py         # Module management
│   ├── schema.py          # Custom fields/models
│   ├── views.py           # View modification
│   ├── reports.py         # QWeb reports
│   ├── planning.py        # Requirements analysis & solution design
│   ├── workflows.py       # Business setup & feature creation
│   ├── codegen.py         # Addon code generation
│   └── ...                # 11 more tool files
├── knowledge/             # Domain knowledge (MCP resources)
│   ├── knowledge_base.py  # Singleton KB with modules, blueprints, patterns
│   └── data/              # Structured knowledge data
├── planning/              # Planning engine
│   ├── requirement_parser.py  # NL → structured requirements
│   └── solution_designer.py   # Requirements → implementation plan
├── workflows/             # Workflow orchestration
│   ├── setup_business.py  # Full business deployment plans
│   ├── create_feature.py  # Custom feature step plans
│   ├── create_dashboard.py # Dashboard creation plans
│   └── setup_integration.py # Integration setup plans
├── codegen/               # Code generation engine
│   ├── addon_builder.py   # Orchestrates full addon generation
│   ├── model_gen.py       # Python model file generation
│   ├── view_gen.py        # XML view generation
│   └── security_gen.py    # Access rules & security groups
├── utils/                 # Shared utilities
│   ├── validators.py      # Input validation
│   ├── errors.py          # Custom error types
│   ├── xpath_builder.py   # XPath generation
│   ├── qweb_builder.py    # QWeb template helpers
│   └── ...
└── verification/          # Post-operation verification
    ├── state_cache.py     # Live model/field cache
    └── verify_*.py        # Per-category verifiers
```

## Making Changes

### Adding a New Tool

1. Create or edit a file in `src/odooforge/tools/`
2. Register the tool in `src/odooforge/server.py`
3. Add tests in `tests/`
4. Document in `docs/tools/`

### Code Style

- Use type hints for all function signatures
- Write docstrings with `Args:` sections for tool parameters
- Return `dict[str, Any]` with `status` key from all tools
- Use `validate_model_name()` and `validate_db_name()` for input validation
- Custom fields must start with `x_`, custom models with `x_`

### Commit Messages

Use conventional commits:

```
feat: add new bulk import tool
fix: correct view reset for base views
docs: add automation tool reference
test: add edge cases for schema creation
```

## Pull Request Process

1. Fork the repo and create a feature branch
2. Make your changes with tests
3. Ensure all tests pass: `uv run pytest tests/ -v`
4. Update documentation if needed
5. Submit a PR with a clear description

## Reporting Issues

- Use [GitHub Issues](https://github.com/hamzatrq/odoo-forge/issues)
- Include: Odoo version, Python version, steps to reproduce
- For tool errors, include the full error response

## Code of Conduct

Be respectful, constructive, and inclusive. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).
