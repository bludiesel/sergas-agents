---
name: skill-creator
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
license: Complete terms in LICENSE.txt
---

# Skill Creator - Interactive Skill Development Guide

Use this skill when creating custom Claude skills that package specialized instructions, scripts, and resources for reusable workflows.

## When to Use

- Building custom skills for domain-specific workflows
- Creating reusable automation patterns
- Packaging specialized knowledge for repeated use
- Extending Claude's capabilities with new tool combinations

## Six-Phase Creation Process

### Phase 1: Understand Concrete Examples

**Objective**: Gather real use cases before abstracting into a skill.

**Process**:
1. Ask user for 2-3 concrete examples of tasks they want to automate
2. Request sample inputs, outputs, and context
3. Validate understanding by summarizing each example
4. Identify common patterns across examples

**Questions to Ask**:
- "What specific task are you trying to accomplish?"
- "Can you provide an example of the input and desired output?"
- "What context or resources are needed?"
- "Are there variations of this task?"

**Best Practices**:
- Don't overwhelm with too many questions
- Focus on concrete, real examples first
- Avoid premature abstraction

### Phase 2: Plan Reusable Contents

**Objective**: Identify what scripts, references, and assets to create.

**Analysis Framework**:
For each example, determine:
- **Scripts**: Deterministic operations that can be automated (data processing, file manipulation, API calls)
- **References**: Knowledge documents that provide context (best practices, documentation, patterns)
- **Assets**: Templates or resources used in output (HTML templates, CSS, images)

**Resource Types**:

**Scripts Directory** (`scripts/`):
- Single-purpose executable scripts
- Deterministic, repeatable operations
- Avoid code generation; enable execution
- Examples: `rotate_pdf.py`, `init_skill.py`, `package_skill.py`

**References Directory** (`references/`):
- Detailed documentation loaded selectively
- Best practices, API docs, pattern guides
- Use grep patterns for large files
- Examples: `api_reference.md`, `best_practices.md`

**Assets Directory** (`assets/`):
- Used in output, not loaded to context
- Templates, fonts, images, starter code
- Examples: `template.html`, `logo.png`, `starter-project/`

### Phase 3: Initialize Skill

**Objective**: Generate skill template structure.

**Process**:
1. Create skill directory: `.claude/skills/skill-name/`
2. Generate SKILL.md with YAML frontmatter
3. Create subdirectories as needed (scripts/, references/, assets/)

**SKILL.md Template**:
```yaml
---
name: skill-name
description: "Clear description with trigger keywords. Use when [specific use case]. Essential for [specific workflow]."
license: Complete terms in LICENSE.txt
---

# Skill Name - Brief Title

Short introduction explaining what this skill does.

## When to Use

- Bullet points of specific use cases
- Clear trigger scenarios
- Examples of when to activate

## Core Workflow

1. Step-by-step process
2. With clear instructions
3. And expected outcomes

## Key Features

- Feature 1 with description
- Feature 2 with description
- Feature 3 with description

## Best Practices

- Best practice 1
- Best practice 2
- Best practice 3

## Examples

### Example 1: Common Use Case
[Detailed example with inputs and outputs]

### Example 2: Advanced Use Case
[Detailed example with variations]
```

**Naming Conventions**:
- Skill name: lowercase, hyphenated (e.g., `zoho-crm-analysis`)
- Directory: match skill name exactly
- SKILL.md: uppercase, required
- Subdirectories: lowercase (scripts/, references/, assets/)

### Phase 4: Write Skill Content

**Objective**: Write instructions for another Claude instance.

**Writing Guidelines**:

**Voice**: Imperative/infinitive form
- ✅ "To accomplish X, do Y"
- ✅ "Use this tool when..."
- ❌ "You should do X"
- ❌ "If you need to do X"

**Structure**:
1. Start with overview and when to use
2. Define core workflow step-by-step
3. Explain key features and capabilities
4. Provide concrete examples
5. Include best practices and edge cases

**Progressive Disclosure**:
- **Tier 1 (Metadata)**: Name + description (~100 words)
  - Always loaded, determines triggering
  - Clear use case keywords

- **Tier 2 (SKILL.md)**: Main instructions (<5,000 words)
  - Loaded when skill triggers
  - Procedural workflow guidance

- **Tier 3 (Resources)**: Scripts, references, assets
  - Loaded as needed
  - Scripts execute without loading
  - References loaded selectively

**Quality Checklist**:
- [ ] Clear, triggerable description
- [ ] Imperative voice throughout
- [ ] Step-by-step workflow
- [ ] Concrete examples included
- [ ] Best practices documented
- [ ] Under 5,000 words
- [ ] No duplication between SKILL.md and references
- [ ] Resources properly organized

### Phase 5: Create Supporting Resources

**Objective**: Build scripts, references, and assets.

**Script Development**:
```python
# Example: Helper script structure
#!/usr/bin/env python3
"""
Brief description of what this script does.
"""

import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Script description")
    parser.add_argument("input", help="Input description")
    parser.add_argument("--option", help="Option description")

    args = parser.parse_args()

    # Script logic here
    result = process(args.input)
    print(result)

if __name__ == "__main__":
    main()
```

**Reference Documentation**:
- Organize by topic or use case
- Include code examples
- Link to external resources
- Keep focused and scannable

**Asset Organization**:
- Group related assets in subdirectories
- Document asset usage in SKILL.md
- Include README for complex asset structures

### Phase 6: Test and Iterate

**Objective**: Validate skill with real tasks and refine.

**Testing Process**:
1. Test skill with original examples
2. Try edge cases and variations
3. Monitor what works and what's inefficient
4. Refine based on actual usage patterns

**Iteration Triggers**:
- User asks follow-up questions → add to SKILL.md
- Repeated manual operations → create script
- Frequent context switching → add reference doc
- Output quality issues → improve examples

**Quality Validation**:
Before finalizing:
- [ ] Skill triggers appropriately
- [ ] Instructions are clear and actionable
- [ ] Scripts execute correctly
- [ ] References load selectively
- [ ] Assets produce expected output
- [ ] Examples cover common cases
- [ ] Naming follows conventions

## Skill Anatomy Reference

### Required Files

**SKILL.md** (Required)
- YAML frontmatter with name, description, license
- Markdown instructions for Claude
- Under 5,000 words recommended

### Optional Directories

**scripts/** (Optional)
- Executable Python, Bash, or Node scripts
- Must be deterministic and repeatable
- Should avoid generating code, focus on execution

**references/** (Optional)
- Detailed documentation files
- Loaded selectively based on need
- Can be large (use grep patterns)

**assets/** (Optional)
- Templates, images, starter projects
- Not loaded to context
- Used in output generation

## Advanced Patterns

### Multi-Phase Workflows

For complex skills with distinct phases:

```markdown
## Phase 1: Analysis
[Instructions for analysis phase]

## Phase 2: Planning
[Instructions for planning phase]

## Phase 3: Implementation
[Instructions for implementation phase]

## Phase 4: Validation
[Instructions for validation phase]
```

### Quality Standards

For skills requiring specific quality bars:

```markdown
## Quality Requirements
- Zero errors in [specific aspect]
- Mandatory validation step
- Required recalculation/verification
- Industry-specific conventions

## Validation Checklist
- [ ] Requirement 1 verified
- [ ] Requirement 2 verified
- [ ] Requirement 3 verified
```

### Tool Integration

For skills combining multiple tools:

```markdown
## Tool Stack
- Primary tool: [purpose]
- Secondary tool: [purpose]
- Validation tool: [purpose]

## Tool Sequence
1. Use Tool A for [operation]
2. Validate with Tool B
3. Format with Tool C
4. Output with Tool D
```

## Examples

### Example 1: Simple Workflow Skill

**Use Case**: Automating report generation

```yaml
---
name: weekly-report-generator
description: "Generate standardized weekly status reports with progress, plans, and problems format. Use when creating team updates or project status reports."
license: MIT
---

## When to Use
- Creating weekly team status updates
- Generating project progress reports
- Documenting achievements and blockers

## Core Workflow
1. Gather data from user (progress, plans, problems)
2. Format using 3P template
3. Generate markdown report
4. Optionally export to PDF

## Template Structure
**Progress**: What was accomplished
**Plans**: What's coming next
**Problems**: Current blockers and risks
```

### Example 2: Complex Technical Skill

**Use Case**: Building API integration tools

```yaml
---
name: api-client-builder
description: "Build robust API client libraries with authentication, error handling, and retry logic. Use when creating API wrappers or integration clients."
license: Apache 2.0
---

## When to Use
- Building API integration clients
- Creating SDK wrappers
- Implementing API authentication flows

## Core Workflow
1. Research API documentation (references/api_patterns.md)
2. Design client architecture
3. Implement authentication layer
4. Build request/response handling
5. Add error handling and retries
6. Generate tests (scripts/generate_tests.py)

## Scripts
- `scripts/generate_tests.py` - Auto-generate API tests
- `scripts/validate_client.py` - Validate client implementation

## References
- `references/api_patterns.md` - Common API design patterns
- `references/auth_methods.md` - Authentication methods guide
```

## Best Practices

### Do's
✅ Start with concrete examples before abstracting
✅ Write for another Claude instance, not for humans
✅ Use imperative voice for instructions
✅ Keep SKILL.md under 5,000 words
✅ Organize resources by purpose (scripts, references, assets)
✅ Include validation and quality checks
✅ Iterate based on real usage

### Don'ts
❌ Don't overwhelm with too many questions upfront
❌ Don't duplicate content between SKILL.md and references
❌ Don't use conversational voice ("you should", "if you want")
❌ Don't create scripts that just generate code
❌ Don't load assets to context (use in output only)
❌ Don't abstract too early without concrete examples

## Troubleshooting

**Skill doesn't trigger**
→ Check description has clear trigger keywords
→ Ensure use case matches user query patterns

**Instructions unclear**
→ Add more concrete examples
→ Break complex steps into smaller sub-steps
→ Use imperative voice consistently

**Resources not loading**
→ Verify file paths are correct
→ Check directory structure matches conventions
→ Ensure YAML frontmatter is valid

**Script execution fails**
→ Test scripts independently
→ Add error handling and validation
→ Include clear usage documentation

## Skill Quality Checklist

Before finalizing any skill:

**Metadata**:
- [ ] Name is lowercase, hyphenated
- [ ] Description includes trigger keywords
- [ ] Description under 100 words
- [ ] Use case is explicit

**Content**:
- [ ] SKILL.md under 5,000 words
- [ ] Imperative voice throughout
- [ ] Step-by-step workflow defined
- [ ] Concrete examples included
- [ ] Best practices documented

**Resources**:
- [ ] Scripts are single-purpose and deterministic
- [ ] References organized by topic
- [ ] Assets used in output only
- [ ] All file paths are correct

**Testing**:
- [ ] Tested with original examples
- [ ] Edge cases considered
- [ ] Validation steps included
- [ ] Quality standards defined

## Related Skills

- **template-skill**: Basic template for quick skill creation
- **mcp-builder**: Building MCP integrations for external APIs
- **webapp-testing**: Testing and validation patterns

## Resources

- Official Skills Documentation: https://docs.claude.com/skills
- Skills Repository: https://github.com/anthropics/skills
- Best Practices Guide: https://docs.claude.com/skills/best-practices
