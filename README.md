# AnyCost Adaptor Generator

Generate CloudZero AnyCost Stream adaptors for any provider. Define your provider's API and billing shape in YAML (or walk through interactive prompts), and the generator produces a ready-to-customize Python project with authentication, API client, data transformation, and CloudZero upload wiring.

## Install

```bash
pip install .
```

For development (includes pytest):

```bash
pip install -e ".[dev]"
```

## Usage

Three ways to use the generator:

```bash
# From a YAML config
python -m anycost_generator generate --config config/examples/bfl_config.yaml --output ../bfl-adaptor

# Interactive prompts (builds config + generates)
python -m anycost_generator interactive

# Validate a config without generating
python -m anycost_generator validate --config config/examples/bfl_config.yaml
```

## Tiers

The generator selects templates based on your provider's billing complexity:

| Tier | Pattern | Examples |
|------|---------|----------|
| **tier1_credit** | Poll single endpoint, compute credit delta, convert to USD | BFL, Runware, Leonardo, Luma, ElevenLabs |
| **tier2_structured** | Multiple endpoints, structured line items, field mapping | Confluent, SumoLogic |
| **tier3_enterprise** | CSV processing or nested API, contract pricing, aggregation | Heroku, Splunk |

The tier is auto-detected from your config (presence of `credit_config`, `structured_config`, or `enterprise_config`), or set explicitly with `tier:`.

## Config Structure

Every config requires three sections:

```yaml
provider:
  name: "myprovider"              # Lowercase identifier
  display_name: "My Provider"
  service_type: "cloud"

api:
  base_url: "https://api.example.com/v1"
  auth_method: "api_key"          # api_key | basic_auth | bearer_token | bearer_jwt | oauth2

auth:
  required_env_vars:
    - "MYPROVIDER_API_KEY"
```

Plus one tier-specific section (`credit_config`, `structured_config`, or `enterprise_config`). See `config/schema_reference.yaml` for all fields, or browse `config/examples/` for working configs.

## Generated Output

```
your-provider-adaptor/
  anycost.py                        # CLI entry point (ready to use)
  pyproject.toml                    # Project config
  src/
    provider_config.py              # Auth + env var loading
    provider_client.py              # API client (customize data fetching)
    provider_transform.py           # Data -> CBF transformation (customize field mapping)
    provider_anycost_adaptor.py     # Orchestration (fetch -> transform -> upload)
    cloudzero.py                    # CloudZero client (ready to use)
  env/.env.example                  # Environment variable template
```

After generating, implement the TODO sections in `src/`, then:

```bash
cd ../your-provider-adaptor
cp env/.env.example env/.env        # Add credentials
pip install .
python anycost.py test              # Verify connections
python anycost.py myprovider --month 2025-01
```

## Examples

| Config | Tier | Notes |
|--------|------|-------|
| `config/examples/bfl_config.yaml` | tier1 | Credit polling with discount rate |
| `config/examples/leonardo_config.yaml` | tier1 | Multi-pool credit tracking |
| `config/examples/confluent_config.yaml` | tier2 | Structured billing with field mapping |
| `config/examples/heroku_config.yaml` | tier3 | Nested API with contract pricing |
| `config/examples/splunk_config.yaml` | tier3 | CSV file processing |

## Testing

```bash
pytest tests/
```

## Project Layout

```
anycost_generator/                  # Generator package
  cli/                              # CLI (generate, validate, interactive)
  config/                           # Pydantic schema + YAML loader
  engine/                           # Jinja2 renderer + orchestrator
  tiers/                            # Tier strategies + resolver
  validation/                       # Config + output validators
templates/                          # Jinja2 templates
  base/                             # Shared (anycost.py, pyproject.toml, etc.)
  src/                              # Per-tier conditional templates
  fragments/                        # Reusable includes (auth, transforms)
  static/                           # Copied verbatim (cloudzero.py)
config/examples/                    # Working configs for real providers
tests/                              # 59 tests across schema, resolver, renderer, e2e generation
```
