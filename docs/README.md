# Documentation

## Available Documentation

### 1. Power Analysis Guide
**File:** `Power_Analysis_Guide.md`

Comprehensive user guide covering:
- Quick start
- All workflows (statistical power, integrated planning)
- Segment analysis best practices
- Troubleshooting
- API reference

**Target audience:** Researchers, analysts, product teams

---

## Publishing to Confluence

### Using Python Script (Recommended)

```bash
# 1. Install dependencies
pip install atlassian-python-api markdown

# 2. Set environment variables
export CONFLUENCE_URL='https://yourcompany.atlassian.net'
export CONFLUENCE_USERNAME='your.email@company.com'
export CONFLUENCE_API_TOKEN='your-api-token'

# 3. Publish documentation
python scripts/publish_to_confluence.py \
    --space MYSPACE \
    --title "Power Analysis & Sample Planning Guide"
```

**Get API Token:** https://id.atlassian.com/manage-profile/security/api-tokens

**Optional Parameters:**
- `--parent-id PAGE_ID` - Nest under existing page
- `--file PATH` - Publish different Markdown file (default: `docs/Power_Analysis_Guide.md`)

### Manual Upload

1. Open Confluence space
2. Create new page or edit existing
3. Copy content from `Power_Analysis_Guide.md`
4. Paste as Markdown (Confluence will convert)
5. Adjust formatting as needed

---

## Maintenance

**Update documentation when:**
- New features added
- Workflows change
- Common questions arise
- Version updates

**Last updated:** 2026-05-23 (v3.0)
