# Phase 4: Agent Enhancement for GitHub

This phase is **optional** but recommended for optimal GitHub bot performance. It enhances each agent with GitHub-specific context and prompts.

---

## 📋 Overview

**Status:** Optional Enhancement
**Time Required:** 1 hour
**Complexity:** Low
**Impact:** Medium-High (improves agent quality and GitHub-specific responses)

### What This Phase Does

Enhances the 5 specialized agents with GitHub-aware capabilities:
- Adds repository context to agent prompts
- Provides PR/Issue details to agents
- Includes GitHub MCP tool guidance
- Optimizes responses for GitHub workflows

---

## 🎯 Why Enhance Agents?

### Without Enhancements (Current State)
Agents work but don't know they're on GitHub:
```
User: "@droid fix the CSS"
Designer: "I'll create a design specification..."
```
- ✅ Functional
- ⚠️ Generic responses
- ⚠️ May not mention GitHub-specific features
- ⚠️ Might not reference PR context

### With Enhancements
Agents are GitHub-aware:
```
User: "@droid fix the CSS"
Designer: "I'll analyze the CSS files in this PR (#42) and create
a design specification. I can see you're working on responsive
layout fixes in owner/repo."
```
- ✅ Context-aware
- ✅ References specific PR/Issue
- ✅ Mentions repository name
- ✅ Understands GitHub workflow

---

## 🔧 What Needs Enhancement

### Agent Files to Modify

```
src/python/agents/collaborative/
├── designer_agent.py        - UI/UX Designer
├── frontend_agent.py        - Frontend Developer
├── code_reviewer_agent.py   - Code Reviewer
├── qa_agent.py             - QA Engineer
└── devops_agent.py         - DevOps Engineer
```

### Enhancement Areas

1. **System Prompts** - Add GitHub context
2. **Tool Awareness** - Explain GitHub MCP tools
3. **Repository Context** - Provide repo/PR details
4. **Workflow Optimization** - GitHub-specific guidance

---

## 📝 Implementation Guide

### Step 1: Modify Base Agent Class

**File:** `src/python/agents/collaborative/base_agent.py`

**Add method to accept GitHub context:**

```python
class BaseAgent:
    def __init__(
        self,
        mcp_servers: Dict,
        github_context: Optional[Dict] = None  # NEW
    ):
        self.mcp_servers = mcp_servers
        self.github_context = github_context  # NEW

        # ... existing code ...

    def _build_system_prompt(self) -> str:
        """Build system prompt with GitHub context if available"""
        base_prompt = self._get_base_system_prompt()

        # Add GitHub context if present
        if self.github_context:
            github_addendum = self._get_github_context_prompt()
            return f"{base_prompt}\n\n{github_addendum}"

        return base_prompt

    def _get_github_context_prompt(self) -> str:
        """Generate GitHub-specific context prompt"""
        if not self.github_context:
            return ""

        repo = self.github_context.get("repository", {}).get("full_name", "")
        context_type = self.github_context.get("type")

        if context_type == "pull_request":
            pr = self.github_context.get("pull_request", {})
            pr_number = pr.get("number")
            pr_title = pr.get("title", "")

            return f"""
# GitHub Context

You are currently working on a GitHub Pull Request:
- Repository: {repo}
- PR Number: #{pr_number}
- PR Title: {pr_title}
- Author: {pr.get("author", "unknown")}

## Available GitHub Tools

You have access to GitHub MCP tools:
- `repos.get_file(path, ref)` - Read file contents from repository
- `repos.update_file(path, content, message, branch)` - Modify files
- `repos.create_file(path, content, message, branch)` - Create new files
- `repos.create_branch(branch_name, from_branch)` - Create feature branch
- `pull_requests.open(head, base, title, body)` - Create pull request

## Workflow

When you complete your work:
1. Create a new branch (e.g., `droid/fix-{pr_number}-{timestamp}`)
2. Make your changes on that branch
3. Create a PR with a descriptive title and detailed body
4. Reference the original issue/PR in your PR description

Current repository: {repo}
"""
        else:  # issue
            issue = self.github_context.get("issue", {})
            issue_number = issue.get("number")
            issue_title = issue.get("title", "")

            return f"""
# GitHub Context

You are currently working on a GitHub Issue:
- Repository: {repo}
- Issue Number: #{issue_number}
- Issue Title: {issue_title}
- Labels: {", ".join(issue.get("labels", []))}

Your task is to create a solution that can be implemented via a Pull Request.

Available GitHub tools and workflow are the same as for PRs.
"""
```

---

### Step 2: Enhance Designer Agent

**File:** `src/python/agents/collaborative/designer_agent.py`

**Modify the `__init__` method:**

```python
def __init__(self, mcp_servers: Dict, github_context: Optional[Dict] = None):
    super().__init__(
        agent_id="designer_001",
        name="UI/UX Designer",
        role=AgentRole.DESIGNER,
        mcp_servers=mcp_servers,
        github_context=github_context  # Pass to base class
    )
```

**Enhance the system prompt:**

```python
def _get_base_system_prompt(self) -> str:
    """Get the base system prompt (before GitHub context)"""
    base = """
You are a UI/UX Designer specializing in modern web applications.

# Core Responsibilities
- Create comprehensive design specifications
- Define color schemes, typography, spacing
- Ensure accessibility (WCAG 2.1 AA compliance)
- Review frontend implementations for design fidelity
- Provide specific, actionable design guidance

# Design Philosophy
- Mobile-first, responsive design
- Clean, modern aesthetics
- Consistent design systems
- User-centric approach

... (rest of existing prompt) ...
"""

    # If on GitHub, add GitHub-specific guidance
    if self.github_context:
        base += """

# GitHub Workflow Notes
- When reviewing code, reference specific files and line numbers
- Mention the PR number in your feedback
- If you find design issues, be specific about which components need changes
- Use markdown formatting for clear communication in GitHub comments
"""

    return base
```

---

### Step 3: Enhance Frontend Agent

**File:** `src/python/agents/collaborative/frontend_agent.py`

**Key additions:**

```python
def _get_base_system_prompt(self) -> str:
    base = """
You are a Frontend Developer specializing in React, Next.js, and modern web development.

... (existing prompt) ...
"""

    if self.github_context:
        base += """

# GitHub Development Workflow

When implementing features:
1. **Read Existing Code**: Use `repos.get_file()` to understand current codebase
2. **Create Feature Branch**: Use `repos.create_branch()`
   - Format: `droid/feature-{short-description}-{timestamp}`
   - Base from main/master branch
3. **Implement Changes**: Use `repos.update_file()` or `repos.create_file()`
4. **Create PR**: Use `pull_requests.open()` with:
   - Clear title: "[Droid] Add feature: {description}"
   - Detailed body explaining changes
   - Reference original issue/PR

## Example PR Body Format

```markdown
## Summary
Brief overview of changes made.

## Changes Made
- Added new component: `ComponentName`
- Updated styles in `file.css`
- Fixed responsive layout issues

## Testing
- Tested on Chrome, Firefox, Safari
- Verified mobile responsiveness
- Checked accessibility

Fixes #{issue_number}

🤖 Generated with [Droid Bot](https://github.com/billsusanto/whatsapp_mcp)
```

Remember: You're working in repository {repo_name} on {pr_or_issue}.
"""

    return base
```

---

### Step 4: Enhance Code Reviewer Agent

**File:** `src/python/agents/collaborative/code_reviewer_agent.py`

```python
def _get_base_system_prompt(self) -> str:
    base = """
You are a Senior Code Reviewer specializing in security, performance, and best practices.

... (existing prompt) ...
"""

    if self.github_context:
        repo = self.github_context.get("repository", {}).get("full_name", "")
        base += f"""

# GitHub Code Review Guidelines

When reviewing code from {repo}:

1. **File-Level Feedback**
   - Reference specific files: "In `src/components/Button.tsx:42`..."
   - Link to GitHub's file view when possible

2. **Security Checks**
   - Look for exposed secrets or API keys
   - Check for SQL injection vulnerabilities
   - Verify input sanitization
   - Review authentication/authorization

3. **Performance Considerations**
   - Identify unnecessary re-renders (React)
   - Check for memory leaks
   - Review bundle size implications

4. **GitHub-Specific Issues**
   - Ensure `.gitignore` is proper
   - Check for large files (>100MB warning)
   - Verify CI/CD compatibility

5. **Documentation**
   - README.md updates if needed
   - Code comments for complex logic
   - TypeScript types and interfaces

## Review Output Format

Provide scores (1-10) for:
- Security: {score}/10
- Performance: {score}/10
- Code Quality: {score}/10
- Best Practices: {score}/10
**Overall: {average}/10**

Critical issues: {list if any}
Suggestions: {list improvements}
"""

    return base
```

---

### Step 5: Enhance QA Engineer Agent

**File:** `src/python/agents/collaborative/qa_agent.py`

```python
def _get_base_system_prompt(self) -> str:
    base = """
You are a QA Engineer specializing in functional, usability, and accessibility testing.

... (existing prompt) ...
"""

    if self.github_context:
        base += """

# GitHub QA Workflow

When testing changes in this PR:

1. **Read the PR Description**
   - Understand what was changed
   - Review the stated objectives
   - Check if changes align with issue requirements

2. **Test Plan Creation**
   - List all functionality to test
   - Include edge cases
   - Consider different browsers/devices
   - Document expected vs actual behavior

3. **Accessibility Testing**
   - Keyboard navigation
   - Screen reader compatibility
   - ARIA labels
   - Color contrast ratios
   - Focus management

4. **Report Format**
   Use this structure:

   ```markdown
   ## QA Test Report

   ### Tests Passed ✅
   - Feature X works as expected
   - Responsive on mobile devices
   - Keyboard navigation functional

   ### Issues Found ❌
   - Issue 1: Description (Severity: High/Medium/Low)
   - Issue 2: Description

   ### Recommendations 💡
   - Consider adding loading states
   - Could improve error messaging

   ### Accessibility Score: {score}/10
   ### Overall Quality: {score}/10
   ```

Remember: You're testing changes for PR #{pr_number} in {repo}.
"""

    return base
```

---

### Step 6: Enhance DevOps Agent

**File:** `src/python/agents/collaborative/devops_agent.py`

```python
def _get_base_system_prompt(self) -> str:
    base = """
You are a DevOps Engineer specializing in deployment, CI/CD, and infrastructure.

... (existing prompt) ...
"""

    if self.github_context:
        base += """

# GitHub DevOps Workflow

For deploying changes from this GitHub repository:

1. **Pre-Deployment Checks**
   - Verify all files are committed
   - Check for environment variables needed
   - Review dependencies in package.json
   - Ensure build scripts are present

2. **Netlify Deployment**
   - Use Netlify MCP tools for deployment
   - Monitor build logs for errors
   - Verify successful deployment
   - Test the deployed URL

3. **GitHub Integration**
   - When deployment succeeds, comment on PR with live URL
   - Include deployment details (time, commit hash, build time)
   - If deployment fails, analyze logs and report specific errors

4. **Error Handling**
   - If build fails, read build logs via Netlify API
   - Identify the root cause (missing deps, syntax errors, etc.)
   - Request fixes from Frontend Developer agent via A2A protocol
   - Retry deployment after fixes

5. **Success Notification Format**
   ```markdown
   ## 🚀 Deployment Successful!

   - **Live URL**: https://your-app.netlify.app
   - **Deploy Time**: {timestamp}
   - **Build Time**: {duration}
   - **Commit**: {short_sha}

   ### Verification
   - ✅ Build succeeded
   - ✅ Site is accessible
   - ✅ No console errors

   Ready for review and testing!
   ```

Current repository: {repo}
Current PR: #{pr_number}
"""

    return base
```

---

### Step 7: Update Orchestrator to Pass Context

**File:** `src/python/agents/collaborative/orchestrator.py`

**Modify `_get_agent()` method:**

```python
async def _get_agent(self, agent_type: str):
    """
    Get or create an agent on-demand with GitHub context
    """
    # ... existing code ...

    # Create new agent instance WITH github_context
    print(f"🚀 Spinning up {agent_type} agent...")

    if agent_type == "designer":
        agent = DesignerAgent(
            self.mcp_servers,
            github_context=self.github_context  # NEW
        )
    elif agent_type == "frontend":
        agent = FrontendDeveloperAgent(
            self.mcp_servers,
            github_context=self.github_context  # NEW
        )
    elif agent_type == "code_reviewer":
        agent = CodeReviewerAgent(
            self.mcp_servers,
            github_context=self.github_context  # NEW
        )
    elif agent_type == "qa":
        agent = QAEngineerAgent(
            self.mcp_servers,
            github_context=self.github_context  # NEW
        )
    elif agent_type == "devops":
        agent = DevOpsEngineerAgent(
            self.mcp_servers,
            github_context=self.github_context  # NEW
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # ... rest of existing code ...
```

---

## 🧪 Testing Enhancements

### Test 1: Verify Context Passing

```python
# Create test script: test_agent_context.py
import sys
sys.path.insert(0, 'src/python')

from agents.collaborative.designer_agent import DesignerAgent

# Mock GitHub context
github_context = {
    "type": "pull_request",
    "repository": {
        "full_name": "test-user/test-repo"
    },
    "pull_request": {
        "number": 42,
        "title": "Fix responsive CSS layout",
        "author": "test-user"
    }
}

# Create agent with context
agent = DesignerAgent(
    mcp_servers={},
    github_context=github_context
)

# Check if context is in system prompt
system_prompt = agent._build_system_prompt()

assert "test-user/test-repo" in system_prompt, "Repository not in prompt"
assert "#42" in system_prompt, "PR number not in prompt"
assert "repos.get_file" in system_prompt, "GitHub tools not mentioned"

print("✅ All context tests passed!")
```

### Test 2: Verify Agent Responses

```python
# Test that agents mention GitHub context in responses
# Run a simple task and verify response includes repo/PR info
```

---

## 📊 Impact Analysis

### Before Enhancement
```
Designer Agent Response:
"I'll create a modern design specification with a clean color palette,
responsive layout, and accessibility features."
```
- Generic
- No context
- Could be for any platform

### After Enhancement
```
Designer Agent Response:
"I'll create a modern design specification for PR #42 in test-user/test-repo.
I'll use repos.get_file() to review the existing CSS structure, then provide
specific recommendations for the responsive layout fixes mentioned in the PR
title. I'll ensure the design maintains consistency with your repository's
existing components."
```
- Context-aware
- Mentions specific PR
- References GitHub tools
- Shows understanding of task

---

## ⚖️ Cost-Benefit Analysis

### Benefits (Why You Should Do This)
- ✅ **Better Context**: Agents understand they're on GitHub
- ✅ **Clearer Communication**: References specific PRs/Issues
- ✅ **Tool Awareness**: Agents know how to use GitHub MCP
- ✅ **Professional Output**: GitHub-formatted responses
- ✅ **Reduced Errors**: Fewer misunderstandings about workflow

### Costs (Why You Might Skip)
- ⏱️ **Time**: 1 hour of modifications
- 🧪 **Testing**: Need to verify each agent
- 📝 **Maintenance**: More code to maintain
- 🐛 **Risk**: Small chance of introducing bugs

### Recommendation
**Do it if:**
- You want production-quality bot
- You plan to use this heavily
- You value agent quality over speed

**Skip it if:**
- You want to test basic functionality first
- Time-constrained
- Will enhance later based on real usage

---

## 🚀 Quick Implementation (30 minutes)

If you want minimal enhancements for maximum impact:

### Priority 1: Frontend Agent (10 mins)
- Most important for PR creation
- Add GitHub workflow guidance
- Include PR body template

### Priority 2: DevOps Agent (10 mins)
- Critical for deployment success
- Add error reporting format
- Include success notification template

### Priority 3: Code Reviewer (10 mins)
- Improves review quality
- Adds GitHub-specific checks
- Better formatted feedback

**Skip:** Designer and QA for now (less critical for MVP)

---

## 📝 Implementation Checklist

- [ ] Modify `base_agent.py` to accept `github_context`
- [ ] Add `_get_github_context_prompt()` method
- [ ] Update `designer_agent.py`
- [ ] Update `frontend_agent.py`
- [ ] Update `code_reviewer_agent.py`
- [ ] Update `qa_agent.py`
- [ ] Update `devops_agent.py`
- [ ] Modify orchestrator's `_get_agent()` method
- [ ] Test context passing
- [ ] Verify agent responses include GitHub context
- [ ] Deploy and test on real PR

---

## 🎯 Success Criteria

After enhancements, agents should:
- ✅ Reference specific PR/Issue numbers
- ✅ Mention repository name
- ✅ Explain GitHub MCP tools they'll use
- ✅ Format output for GitHub (markdown)
- ✅ Include GitHub-specific recommendations
- ✅ Create well-formatted PRs with detailed descriptions

---

## 📚 Additional Resources

- **GitHub MCP Documentation**: Check agent SDK docs for available tools
- **Example Prompts**: See existing agent system prompts
- **Testing Guide**: `TESTING_GITHUB_BOT.md`

---

## 💡 Future Enhancements

After Phase 4, you could add:
- **GitHub Actions integration** - Trigger workflows
- **Review Comments** - Post line-specific feedback
- **Status Checks** - Add PR status checks
- **Labels & Assignees** - Auto-assign PRs
- **Merge Automation** - Auto-merge when approved

---

## ✅ Decision Time

**Option A: Implement Now** (1 hour)
- Complete all 5 agents
- Full GitHub awareness
- Best quality output

**Option B: Implement Priority Agents** (30 mins)
- Frontend + DevOps + Code Reviewer only
- Good enough for MVP
- Enhance others later

**Option C: Skip for Now**
- Test basic functionality first
- Enhance based on real usage patterns
- Faster to production

**Recommendation:** Option B (Priority agents in 30 mins) - Best balance of quality and speed.

---

**Ready to enhance?** Let me know which option you prefer! 🚀
