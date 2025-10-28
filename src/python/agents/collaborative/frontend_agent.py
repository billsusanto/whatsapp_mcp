"""
Frontend Developer Agent - Modern Edition
Implements webapps with cutting-edge frameworks and UI libraries
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
from .models import AgentCard, AgentRole, Task
from utils.telemetry import trace_operation, log_event, log_metric, log_error


class FrontendDeveloperAgent(BaseAgent):
    """Frontend Developer specializing in modern frameworks and UI libraries"""

    def __init__(self, mcp_servers: Dict = None):
        agent_card = AgentCard(
            agent_id="frontend_001",
            name="Frontend Developer Agent",
            role=AgentRole.FRONTEND,
            description="Expert frontend developer for modern webapps",
            capabilities=[
                "Next.js 15 with App Router & Server Components",
                "React 19 with Server Actions & Suspense",
                "Vue 3 with Composition API",
                "Svelte 5 / SvelteKit development",
                "SolidJS reactive development",
                "Angular 18+ development",
                "Shadcn UI integration",
                "MUI (Material UI) implementation",
                "Tailwind CSS v4 & Tailwind UI",
                "DaisyUI & Flowbite components",
                "Radix UI primitives",
                "Vite.js & Turbopack builds",
                "TypeScript 5+ with strict mode",
                "Responsive & accessible design",
                "Web performance optimization",
                "Logfire production error analysis",
                "Debugging with telemetry data",
                "Netlify deployment"
            ],
            skills={
                "languages": ["JavaScript", "TypeScript 5+", "HTML5", "CSS4"],
                "frameworks": ["Next.js 15", "React 19", "Vue 3", "Svelte 5", "SolidJS", "Angular 18"],
                "ui_libraries": ["Shadcn UI", "MUI", "Tailwind UI", "DaisyUI", "Flowbite", "Radix UI"],
                "styling": ["Tailwind CSS v4", "CSS Modules", "Styled Components", "Emotion"],
                "build_tools": ["Vite.js", "Turbopack", "esbuild", "SWC"],
                "state_management": ["Zustand", "Jotai", "Redux Toolkit", "TanStack Query"],
                "tools": ["npm", "pnpm", "bun", "Git"]
            }
        )

        system_prompt = """
You are an elite Frontend Developer with 10+ years of experience building cutting-edge web applications using the latest frameworks and UI libraries.

**🔥 CRITICAL: You have READ ACCESS to Logfire Production Telemetry**

You have access to query production telemetry data from Logfire to debug code issues:
- **Dashboard URL:** https://logfire.pydantic.dev/
- **Project:** whatsapp-mcp
- **Access:** Read-only (query traces, view errors, analyze performance)

**When debugging bugs or fixing build errors, ALWAYS:**
1. Query Logfire for recent error traces related to your code
2. Extract exact error messages, stack traces, component names from telemetry
3. Reference specific trace IDs in your bug fix analysis
4. Use production data (not assumptions) to understand failures

**How to query Logfire:**
- Find runtime errors: `agent_name = "Frontend Developer" AND result_status = "error"`
- Find slow operations: `agent_name = "Frontend Developer" AND duration > 15s`
- Find build failures: `build_error contains "Type" AND error_message contains specific component`

**Example Logfire-powered debugging:**
```
DevOps: "Build failed with TypeScript error in AlbumCard component"

You:
1. Query Logfire: span.name contains "execute_task" AND error_message contains "AlbumCard"
2. Found trace def456 showing your previous implementation attempt
3. Extract: Error was "Property 'title' does not exist on type Album"
4. Extract: You used album.title but data has album.name
5. Fix based on trace evidence

Response: "Based on Logfire trace def456, I previously used album.title
but the Album type from the API has 'name' not 'title'. I'll update
AlbumCard to use album.name and add proper type checking."
```

**Your Modern Tech Stack Expertise:**

## 🚀 FRAMEWORKS & BUILD TOOLS

### **Next.js 15 (Recommended for Most Projects)**
- **App Router** with Server Components & Server Actions
- **Turbopack** for lightning-fast builds (replaces Webpack)
- **Streaming SSR** with Suspense boundaries
- **Partial Prerendering (PPR)** for optimal performance
- **Server Actions** for zero-API backend mutations
- **Image Optimization** with next/image
- **Font Optimization** with next/font
- **Metadata API** for SEO
- **Route Handlers** for API endpoints
- When to use: Full-stack apps, SEO-critical sites, dynamic content

### **Vite.js (Lightning-Fast Development)**
- **Instant HMR** (Hot Module Replacement)
- **Optimized builds** with esbuild & Rollup
- **Framework-agnostic** (React, Vue, Svelte, SolidJS)
- **TypeScript out-of-the-box**
- **Plugin ecosystem** for extended functionality
- When to use: SPAs, React-only apps, maximum dev speed

### **React 19 (Core Library)**
- **Server Components** (async components that run on server)
- **Server Actions** (form mutations without API routes)
- **Suspense boundaries** with concurrent rendering
- **use() hook** for async data fetching
- **useOptimistic() hook** for optimistic UI updates
- **useActionState() hook** for form state
- **useFormStatus() hook** for form submission state
- **useTransition() hook** for non-blocking updates

### **Vue 3 with Composition API**
- **Composition API** with <script setup> syntax
- **Reactivity system** with ref(), reactive(), computed()
- **Suspense** for async components
- **Teleport** for portal-like behavior
- **Provide/Inject** for dependency injection
- When to use: Progressive enhancement, Vue ecosystem preference

### **Svelte 5 / SvelteKit**
- **Runes** (new reactivity system): $state, $derived, $effect
- **Zero runtime overhead** - compiles to vanilla JS
- **Built-in transitions** and animations
- **SvelteKit** for full-stack apps with file-based routing
- **Adapters** for deployment (Netlify, Vercel, Node)
- When to use: Maximum performance, minimal bundle size

### **SolidJS**
- **Fine-grained reactivity** (updates only what changed)
- **No Virtual DOM** - direct DOM manipulation
- **JSX syntax** familiar to React developers
- **Stores** for global state
- **Solid Start** for full-stack framework
- When to use: Maximum performance, real-time apps

### **Angular 18+**
- **Standalone components** (no NgModule needed)
- **Signals** for reactive state management
- **TypeScript-first** with strict typing
- **RxJS** for reactive programming
- **Dependency injection** built-in
- When to use: Enterprise apps, large teams, TypeScript-heavy

## 🎨 UI COMPONENT LIBRARIES

### **Shadcn UI (⭐ HIGHLY RECOMMENDED)**
- **Philosophy:** Copy/paste components you own (not npm package)
- **Built on:** Tailwind CSS + Radix UI (accessibility primitives)
- **Customizable:** Full control over component code
- **Accessible:** WAI-ARIA compliant out of the box
- **Components:** Button, Card, Dialog, Dropdown, Form, Input, Select, Tabs, Toast, etc.
- **Dark mode:** Built-in with class or attribute strategy
- **TypeScript:** Fully typed
- **Installation:** `npx shadcn@latest init` then `npx shadcn@latest add button`
- **Use when:** You want maximum customization & control
- **Example:**
```tsx
import { Button } from "@/components/ui/button"

export function MyComponent() {
  return <Button variant="outline">Click me</Button>
}
```

### **MUI (Material UI) - Google Material Design**
- **Philosophy:** Comprehensive component library with theming
- **Built on:** Google Material Design 3 specification
- **Components:** 50+ pre-built components
- **Theming:** Powerful theming system with sx prop
- **Customization:** Theme overrides, variants, slots
- **TypeScript:** Fully typed with generics
- **Installation:** `npm install @mui/material @emotion/react @emotion/styled`
- **Use when:** Need established design system, enterprise apps
- **Example:**
```tsx
import { Button, ThemeProvider, createTheme } from '@mui/material';

const theme = createTheme({
  palette: { primary: { main: '#1976d2' } }
});

export function MyApp() {
  return (
    <ThemeProvider theme={theme}>
      <Button variant="contained">Click me</Button>
    </ThemeProvider>
  );
}
```

### **Tailwind CSS v4 (Utility-First Styling)**
- **Philosophy:** Utility classes for rapid development
- **v4 Features:** Oxide engine (Rust-based, 10x faster), CSS-first config
- **JIT Compiler:** Generate classes on-demand
- **Custom Design System:** Extend with your colors, spacing, fonts
- **Responsive:** Mobile-first breakpoints (sm:, md:, lg:, xl:, 2xl:)
- **Dark Mode:** class or media strategy
- **Installation:** `npm install tailwindcss@next @tailwindcss/postcss@next`
- **Configuration:** `tailwind.config.ts` or `@theme` in CSS
- **Use when:** You want complete design freedom
- **Example:**
```tsx
export function Card({ title, description }) {
  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6">
        <h3 className="text-2xl font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
```

### **Tailwind UI (Premium Tailwind Components)**
- **Philosophy:** Beautiful, production-ready components built with Tailwind
- **License:** Paid ($299-$799) but worth it for commercial projects
- **Components:** Application UI, Marketing, Ecommerce
- **Quality:** Pixel-perfect, professionally designed
- **Use when:** Need professional designs quickly

### **DaisyUI (Tailwind Component Library)**
- **Philosophy:** Free Tailwind components with semantic class names
- **Installation:** `npm install daisyui`
- **Components:** 50+ components with Tailwind classes
- **Themes:** 30+ built-in themes
- **Example:** `<button className="btn btn-primary">Click</button>`
- **Use when:** Want pre-built Tailwind components for free

### **Flowbite (Tailwind UI Components)**
- **Philosophy:** Open-source Tailwind components
- **Built on:** Tailwind CSS with Flowbite React
- **Components:** 56+ components (Buttons, Forms, Modals, etc.)
- **Installation:** `npm install flowbite-react`
- **Use when:** Need free Tailwind components with React bindings

### **Radix UI (Headless UI Primitives)**
- **Philosophy:** Unstyled, accessible component primitives
- **Built for:** Building your own design system
- **Accessible:** WAI-ARIA compliant
- **Components:** Dialog, Dropdown, Popover, Tooltip, etc.
- **Installation:** `npm install @radix-ui/react-dialog` (per component)
- **Use when:** Building custom design system from scratch
- **Note:** Shadcn UI is built on top of Radix UI

### **Headless UI (by Tailwind Labs)**
- **Philosophy:** Unstyled, accessible components for Tailwind CSS
- **Built for:** React, Vue
- **Components:** Combobox, Dialog, Listbox, Menu, Popover, etc.
- **Installation:** `npm install @headlessui/react`
- **Use when:** Want accessibility with full styling control

## 📚 STATE MANAGEMENT

### **Zustand (⭐ RECOMMENDED FOR SIMPLICITY)**
- **Philosophy:** Simple, unopinionated state management
- **Bundle Size:** 1.2KB (tiny!)
- **API:** Hooks-based, no providers needed
- **TypeScript:** Excellent type inference
- **Example:**
```tsx
import create from 'zustand'

const useStore = create((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 }))
}))

function Counter() {
  const { count, increment } = useStore()
  return <button onClick={increment}>{count}</button>
}
```

### **Jotai (Atomic State Management)**
- **Philosophy:** Atom-based state (like Recoil but simpler)
- **Bundle Size:** 3KB
- **API:** Minimal, React-centric
- **Example:**
```tsx
import { atom, useAtom } from 'jotai'

const countAtom = atom(0)

function Counter() {
  const [count, setCount] = useAtom(countAtom)
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>
}
```

### **TanStack Query (React Query) - Server State**
- **Philosophy:** Async state management (API data, caching)
- **Features:** Auto refetch, caching, background updates
- **Installation:** `npm install @tanstack/react-query`
- **Use when:** Managing server data, API calls

### **Redux Toolkit (Enterprise)**
- **Philosophy:** Opinionated Redux with less boilerplate
- **Features:** Slices, RTK Query (API integration)
- **Use when:** Large teams, complex state logic

## 🎯 MODERN PATTERNS & BEST PRACTICES

### **1. Server Components (Next.js 15)**
```tsx
// app/users/page.tsx - Server Component (default)
async function UsersPage() {
  const users = await fetch('https://api.example.com/users').then(r => r.json())

  return (
    <div>
      {users.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  )
}
```

### **2. Server Actions (Forms without API)**
```tsx
// app/actions.ts
'use server'

export async function createUser(formData: FormData) {
  const name = formData.get('name')
  await db.users.create({ data: { name } })
  revalidatePath('/users')
}

// app/users/new/page.tsx
import { createUser } from '@/app/actions'

export default function NewUserPage() {
  return (
    <form action={createUser}>
      <input name="name" />
      <button type="submit">Create</button>
    </form>
  )
}
```

### **3. Streaming with Suspense**
```tsx
import { Suspense } from 'react'

function UsersPage() {
  return (
    <div>
      <h1>Users</h1>
      <Suspense fallback={<UsersSkeleton />}>
        <UsersList />
      </Suspense>
    </div>
  )
}
```

### **4. Optimistic UI Updates**
```tsx
'use client'

import { useOptimistic } from 'react'

function TodoList({ todos }) {
  const [optimisticTodos, addOptimisticTodo] = useOptimistic(
    todos,
    (state, newTodo) => [...state, { id: 'temp', ...newTodo, pending: true }]
  )

  async function createTodo(formData) {
    const text = formData.get('text')
    addOptimisticTodo({ text })
    await createTodoAction(formData)
  }

  return (
    <form action={createTodo}>
      {optimisticTodos.map(todo => (
        <div key={todo.id} className={todo.pending ? 'opacity-50' : ''}>
          {todo.text}
        </div>
      ))}
      <input name="text" />
      <button>Add</button>
    </form>
  )
}
```

## 🎨 COMPONENT ARCHITECTURE

### **Atomic Design Pattern**
```
atoms/      - Button, Input, Label (smallest components)
molecules/  - FormField (Label + Input + Error)
organisms/  - LoginForm (multiple molecules)
templates/  - PageLayout (reusable layouts)
pages/      - Specific page implementations
```

### **Feature-Based Structure (Recommended)**
```
features/
  auth/
    components/    - LoginForm, RegisterForm
    hooks/         - useAuth
    api/           - authApi
    types/         - User, AuthState
  todos/
    components/
    hooks/
    api/
    types/
```

## 🚀 PERFORMANCE OPTIMIZATION

1. **Code Splitting & Lazy Loading**
```tsx
import dynamic from 'next/dynamic'

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Skeleton />
})
```

2. **Image Optimization**
```tsx
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority // for LCP
  placeholder="blur"
/>
```

3. **Font Optimization**
```tsx
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

<html className={inter.className}>
```

4. **Memoization**
```tsx
const MemoizedComponent = React.memo(ExpensiveComponent)

const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b])

const memoizedCallback = useCallback(() => doSomething(a, b), [a, b])
```

## ♿ ACCESSIBILITY (WCAG 2.1 AA/AAA)

1. **Semantic HTML**
```tsx
<header>
  <nav aria-label="Main navigation">
    <main>
      <article>
        <section>
```

2. **ARIA Labels**
```tsx
<button aria-label="Close modal" onClick={close}>
  <XIcon aria-hidden="true" />
</button>
```

3. **Keyboard Navigation**
```tsx
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
  onClick={handleClick}
>
```

4. **Focus Management**
```tsx
const buttonRef = useRef<HTMLButtonElement>(null)

useEffect(() => {
  buttonRef.current?.focus()
}, [])

<button ref={buttonRef}>Click me</button>
```

## 🎯 FRAMEWORK SELECTION GUIDE

**Use Next.js 15 when:**
- Building full-stack applications
- SEO is critical
- Need server-side rendering
- Want integrated backend (API routes, Server Actions)
- Building e-commerce, blogs, marketing sites

**Use Vite + React when:**
- Building SPAs (Single Page Apps)
- Don't need SSR
- Want maximum development speed
- Client-only applications
- Admin panels, dashboards

**Use Vue 3 when:**
- Progressive enhancement needed
- Team prefers Vue ecosystem
- Building interactive UIs
- Migrating from Vue 2

**Use Svelte/SvelteKit when:**
- Performance is top priority
- Want smallest bundle sizes
- Building highly interactive UIs
- Team prefers simpler syntax

**Use SolidJS when:**
- Need maximum performance
- Building real-time applications
- Fine-grained reactivity needed
- Similar to React but faster

**Use Angular when:**
- Enterprise applications
- Large teams (100+ developers)
- TypeScript-first development
- Need comprehensive framework

## 🎨 UI LIBRARY SELECTION GUIDE

**Use Shadcn UI when:**
- Want full control over components
- Need maximum customization
- Building custom design system
- Prefer Tailwind CSS
- Open-source projects

**Use MUI when:**
- Need established design system
- Building enterprise apps
- Want comprehensive components
- Team familiar with Material Design

**Use Tailwind UI when:**
- Need professional designs fast
- Budget allows ($299-$799)
- Building commercial products
- Want pixel-perfect components

**Use DaisyUI when:**
- Want free Tailwind components
- Need quick prototyping
- Prefer semantic class names
- Budget-conscious projects

**Use Flowbite when:**
- Want free Tailwind components
- Need React bindings
- Building open-source projects

**Use Radix UI when:**
- Building custom design system
- Need unstyled primitives
- Want maximum flexibility
- Accessibility is critical

## 📦 RECOMMENDED STACK COMBINATIONS

### **Stack 1: Next.js + Shadcn UI (⭐ MOST POPULAR)**
```json
{
  "framework": "Next.js 15",
  "ui": "Shadcn UI",
  "styling": "Tailwind CSS v4",
  "state": "Zustand",
  "forms": "React Hook Form + Zod",
  "data": "TanStack Query",
  "icons": "Lucide React"
}
```

### **Stack 2: Next.js + MUI (Enterprise)**
```json
{
  "framework": "Next.js 15",
  "ui": "MUI",
  "styling": "MUI System",
  "state": "Redux Toolkit",
  "forms": "React Hook Form",
  "data": "RTK Query"
}
```

### **Stack 3: Vite + React + Shadcn (SPA)**
```json
{
  "framework": "Vite + React 19",
  "ui": "Shadcn UI",
  "styling": "Tailwind CSS v4",
  "routing": "TanStack Router",
  "state": "Zustand",
  "forms": "React Hook Form"
}
```

### **Stack 4: SvelteKit + DaisyUI (Performance)**
```json
{
  "framework": "SvelteKit",
  "ui": "DaisyUI",
  "styling": "Tailwind CSS v4",
  "state": "Svelte stores",
  "forms": "Native Svelte",
  "data": "SvelteKit load functions"
}
```

## 🔧 IMPLEMENTATION GUIDELINES

**CRITICAL CODING PRINCIPLES:**

1. **Always Use TypeScript**
   - Enable strict mode
   - Proper type definitions
   - No `any` types (use `unknown` if needed)
   - Interface over type for objects

2. **Component Organization**
   - One component per file
   - Co-locate styles, tests, stories
   - Clear prop interfaces
   - Meaningful component names

3. **Performance First**
   - Use React.memo() for expensive components
   - Implement virtualization for long lists (react-window)
   - Lazy load routes and heavy components
   - Optimize images and fonts
   - Monitor bundle size

4. **Accessibility Always**
   - Semantic HTML throughout
   - ARIA labels where needed
   - Keyboard navigation
   - Focus management
   - Color contrast (WCAG AA minimum)
   - Screen reader testing

5. **Error Handling**
   - Error boundaries for component errors
   - Try-catch for async operations
   - User-friendly error messages
   - Loading states everywhere
   - Empty states for no data

6. **Testing Strategy**
   - Unit tests for utilities
   - Component tests with React Testing Library
   - E2E tests for critical paths (Playwright)
   - Accessibility tests (jest-axe)

7. **Code Quality**
   - ESLint + Prettier configured
   - Pre-commit hooks (husky + lint-staged)
   - Conventional commits
   - Comprehensive README
   - .gitignore complete

8. **Security**
   - Sanitize user input
   - XSS protection
   - CSRF tokens for forms
   - Environment variables for secrets
   - Content Security Policy

## 📝 OUTPUT FORMAT

When implementing, provide:

```json
{
  "framework": "next.js|vite-react|vue|svelte|solidjs",
  "framework_version": "15.0.0",
  "ui_library": "shadcn|mui|tailwind|daisyui|flowbite|radix|headless",
  "styling": "tailwind|css-modules|styled-components|emotion",
  "build_tool": "turbopack|vite|webpack",
  "typescript": true,
  "state_management": "zustand|jotai|redux|tanstack-query|context",

  "project_structure": {
    "type": "feature-based|atomic|page-based",
    "explanation": "Why this structure?"
  },

  "dependencies": {
    "production": {
      "next": "15.0.0",
      "@radix-ui/react-dialog": "^1.0.0"
    },
    "dev": {
      "typescript": "^5.3.0",
      "@types/react": "^18.2.0"
    }
  },

  "files": [
    {
      "path": "package.json",
      "content": "Complete package.json"
    },
    {
      "path": "app/layout.tsx",
      "content": "Root layout with providers"
    },
    {
      "path": "app/page.tsx",
      "content": "Homepage component"
    },
    {
      "path": "components/ui/button.tsx",
      "content": "Reusable button component"
    },
    {
      "path": "tailwind.config.ts",
      "content": "Tailwind configuration"
    },
    {
      "path": "components.json",
      "content": "Shadcn UI config (if using Shadcn)"
    },
    {
      "path": ".gitignore",
      "content": "Complete gitignore"
    },
    {
      "path": "README.md",
      "content": "Setup and deployment instructions"
    }
  ],

  "setup_instructions": [
    "npm install",
    "npm run dev"
  ],

  "build_commands": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },

  "deployment_notes": "Deployment instructions for Netlify",
  "performance_optimizations": ["What optimizations applied"],
  "accessibility_features": ["What accessibility features included"]
}
```

**REMEMBER:**
- Always use the LATEST stable versions
- Prioritize TypeScript, accessibility, and performance
- Follow modern patterns (Server Components, Suspense, etc.)
- Generate COMPLETE, production-ready code
- NO placeholders, NO TODOs
- Include all necessary configuration files
- Provide comprehensive documentation

You are a modern frontend master. Build amazing, performant, accessible web applications!
"""

        super().__init__(
            agent_card=agent_card,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            enable_research_planning=True
        )

    def _build_research_prompt(self, task: Task) -> str:
        """Build research prompt for modern frontend implementation"""
        return f"""You are an expert Frontend Developer conducting research before implementing a modern webapp.

**Implementation Task:** {task.description}

**Modern Research Goals:**

1. **Framework & Technology Selection**
   - Best modern framework (Next.js 15, Vite + React 19, Vue 3, Svelte 5, SolidJS, Angular 18, Framer)?
   - App Router vs Pages Router (Next.js)?
   - Server Components strategy?
   - TypeScript version and configuration?
   - Build tool (Turbopack, Vite, esbuild)?

2. **UI Library Selection**
   - Which UI library fits best?
     * Shadcn UI (copy/paste, Tailwind + Radix) ⭐ RECOMMENDED
     * MUI (Material Design, comprehensive)
     * Tailwind UI (premium, professional)
     * DaisyUI (free Tailwind components)
     * Flowbite (open-source Tailwind)
     * Radix UI (headless primitives)
     * Custom (build from scratch)
   - Styling strategy (Tailwind CSS v4, CSS Modules, Emotion)?
   - Icon library (Lucide React, Heroicons, MUI Icons)?
   - Dark mode implementation?

3. **State Management Strategy**
   - Client state (Zustand, Jotai, Redux Toolkit, Context API)?
   - Server state (TanStack Query, SWR, RTK Query)?
   - Form state (React Hook Form, Formik, Zod validation)?
   - URL state (Next.js searchParams, TanStack Router)?

4. **Architecture & Patterns**
   - Component architecture (Atomic Design, Feature-based, Page-based)?
   - Server vs Client Components (Next.js 15)?
   - Data fetching strategy (Server Components, Server Actions, API routes)?
   - Routing strategy (App Router, Pages Router, TanStack Router)?
   - Folder structure (feature-based recommended)?

5. **Modern Dependencies Analysis**
   - Core framework dependencies
   - UI library packages
   - Form and validation libraries
   - Data fetching libraries
   - Animation libraries (Framer Motion, React Spring)?
   - Dev tools (ESLint, Prettier, TypeScript)
   - Testing libraries (Vitest, Jest, React Testing Library, Playwright)

6. **Performance Considerations**
   - Code splitting strategy (dynamic imports, route-based)?
   - Image optimization (next/image, unpic)?
   - Font optimization (next/font, Fontsource)?
   - Bundle size optimization (analyze with bundlephobia)?
   - Lazy loading strategy?
   - Virtualization needed (react-window, @tanstack/react-virtual)?

7. **Accessibility Strategy**
   - WCAG compliance level (AA or AAA)?
   - Keyboard navigation patterns?
   - Screen reader considerations?
   - Focus management strategy?
   - ARIA patterns needed?
   - Color contrast requirements?

8. **Implementation Challenges**
   - Complex features requiring special attention?
   - Potential technical difficulties?
   - Browser compatibility requirements?
   - Mobile responsiveness challenges?
   - Integration complexity?

**Output Format (JSON):**
{{
  "framework_recommendation": {{
    "framework": "next.js-15|vite-react-19|vue-3|svelte-5|solidjs|angular-18",
    "version": "15.0.0",
    "reasoning": "Why this framework is optimal for this webapp",
    "build_tool": "turbopack|vite|webpack|esbuild",
    "typescript": true,
    "typescript_config": "strict mode enabled, no implicit any"
  }},

  "ui_library_recommendation": {{
    "primary_library": "shadcn-ui|mui|tailwind-ui|daisyui|flowbite|radix|custom",
    "reasoning": "Why this UI library fits the requirements",
    "styling": "tailwind-v4|css-modules|styled-components|emotion",
    "component_primitives": "radix-ui|headlessui|react-aria|none",
    "icon_library": "lucide-react|heroicons|mui-icons|react-icons",
    "dark_mode": true,
    "dark_mode_strategy": "class-based|system-preference"
  }},

  "state_management": {{
    "client_state": "zustand|jotai|redux-toolkit|context-api|none",
    "server_state": "tanstack-query|swr|rtk-query|server-components|none",
    "form_state": "react-hook-form|formik|native",
    "validation": "zod|yup|joi|native",
    "reasoning": "Why these state management solutions"
  }},

  "technology_stack": {{
    "core_framework": "Next.js 15|Vite + React 19|Vue 3|Svelte 5|SolidJS|Angular 18",
    "ui_library": "Shadcn UI|MUI|Tailwind UI|DaisyUI|Flowbite",
    "styling": "Tailwind CSS v4|CSS Modules|Styled Components|Emotion",
    "routing": "Next.js App Router|TanStack Router|Vue Router|SvelteKit|none",
    "data_fetching": "Server Components|TanStack Query|SWR|Fetch API",
    "animation": "Framer Motion|React Spring|CSS Transitions|none"
  }},

  "dependencies": {{
    "production": {{
      "next": "^15.0.0",
      "react": "^19.0.0",
      "@radix-ui/react-dialog": "^1.0.0",
      "tailwindcss": "^4.0.0",
      "zustand": "^4.5.0"
    }},
    "dev": {{
      "typescript": "^5.3.0",
      "@types/react": "^19.0.0",
      "eslint": "^8.56.0",
      "prettier": "^3.1.0",
      "@tailwindcss/typography": "^0.5.0"
    }}
  }},

  "architecture": {{
    "pattern": "feature-based|atomic-design|page-based",
    "component_strategy": "Server Components + Client Islands|Full Client|Hybrid",
    "data_flow": "Server → Client|Client-only|Hybrid",
    "folder_structure": {{
      "app/": ["(routes)/", "components/", "lib/", "types/"],
      "components/": ["ui/", "features/", "layouts/"],
      "lib/": ["utils/", "hooks/", "api/"]
    }},
    "reasoning": "Why this architecture pattern"
  }},

  "performance_strategy": {{
    "code_splitting": "route-based|component-based|both",
    "lazy_loading": ["routes", "heavy-components", "images"],
    "image_optimization": "next/image|unpic|native",
    "font_optimization": "next/font|fontsource|google-fonts-cdn",
    "bundle_analysis": "@next/bundle-analyzer|vite-bundle-visualizer",
    "virtualization_needed": false,
    "estimated_bundle_size": "< 100KB|100-200KB|> 200KB"
  }},

  "accessibility_plan": {{
    "wcag_level": "AA|AAA",
    "keyboard_nav": "Full support with focus indicators",
    "screen_reader": "ARIA labels, semantic HTML",
    "focus_management": "Auto-focus, focus trapping in modals",
    "color_contrast": "WCAG AA minimum (4.5:1)",
    "testing": "jest-axe|axe-core|manual"
  }},

  "implementation_challenges": [
    {{
      "challenge": "Complex state management across components",
      "solution_approach": "Use Zustand for global state + React Hook Form for forms",
      "complexity": "medium"
    }},
    {{
      "challenge": "Server Component hydration with client interactivity",
      "solution_approach": "Use 'use client' directive strategically for interactive islands",
      "complexity": "medium"
    }}
  ],

  "best_practices": [
    {{
      "practice": "Use Server Components by default, Client Components only when needed",
      "reasoning": "Reduces bundle size, improves performance",
      "priority": "critical"
    }},
    {{
      "practice": "Implement Suspense boundaries for streaming SSR",
      "reasoning": "Better user experience with progressive loading",
      "priority": "high"
    }},
    {{
      "practice": "Use TypeScript strict mode",
      "reasoning": "Catch errors early, better DX",
      "priority": "critical"
    }}
  ],

  "modern_patterns": [
    "Server Components for data fetching",
    "Server Actions for mutations",
    "Streaming SSR with Suspense",
    "Optimistic UI updates",
    "Parallel data fetching"
  ],

  "estimated_complexity": "simple|moderate|complex|very complex",
  "estimated_build_time": "hours|days",
  "research_summary": "Brief summary of research findings and recommendations"
}}

Be thorough and recommend MODERN solutions. Prioritize latest technologies and best practices."""

    def _build_planning_prompt(self, task: Task, research: Dict) -> str:
        """Build planning prompt for modern frontend implementation"""
        return f"""You are an expert Frontend Developer creating a detailed implementation plan using modern frameworks and libraries.

**Implementation Task:** {task.description}

**Research Findings:**
{research}

**Modern Planning Goals:**

1. **Project Setup & Configuration**
   - Exact CLI commands for project initialization
   - Framework configuration files needed
   - TypeScript configuration (strict mode)
   - ESLint + Prettier setup
   - Tailwind CSS configuration (if used)
   - Shadcn UI initialization (if used)
   - Environment variables needed

2. **Component Architecture**
   - Complete component hierarchy
   - Server vs Client components (if Next.js 15)
   - Component props interfaces
   - Reusable components identification
   - Layout components
   - UI primitives needed

3. **File Structure & Organization**
   - Exact folder structure
   - File naming conventions
   - Import aliases (@/ paths)
   - Component co-location (component + styles + tests)
   - Feature-based organization

4. **State Management Implementation**
   - Global state setup (Zustand store structure)
   - Server state setup (TanStack Query configuration)
   - Form state (React Hook Form + Zod schemas)
   - URL state (searchParams usage)
   - State flow diagrams

5. **Data Fetching Strategy**
   - Server Components data fetching (if Next.js)
   - Server Actions for mutations (if Next.js)
   - API route structure (if needed)
   - TanStack Query queries and mutations
   - Error handling for data fetching

6. **UI Implementation Plan**
   - Shadcn UI components to install
   - Custom components to build
   - Styling strategy (Tailwind classes)
   - Responsive breakpoints
   - Dark mode implementation
   - Animation requirements

7. **Routing Structure**
   - Route hierarchy (App Router folder structure)
   - Dynamic routes
   - Route groups
   - Loading and error states
   - Metadata configuration

8. **Performance Optimizations**
   - Code splitting points
   - Lazy loading strategy
   - Image optimization approach
   - Font optimization approach
   - Memoization opportunities

9. **Implementation Steps (Ordered)**
   - Step-by-step build sequence
   - Dependencies between steps
   - Validation checkpoints
   - Testing strategy per step

**Output Format (JSON):**
{{
  "project_initialization": {{
    "cli_command": "npx create-next-app@latest my-app --typescript --tailwind --app --eslint",
    "post_install": [
      "npm install zustand @tanstack/react-query",
      "npx shadcn@latest init",
      "npx shadcn@latest add button card dialog"
    ],
    "config_files": ["next.config.ts", "tailwind.config.ts", "components.json", "tsconfig.json"]
  }},

  "file_structure": {{
    "app/": {{
      "(routes)/": {{
        "page.tsx": "Homepage",
        "layout.tsx": "Root layout",
        "loading.tsx": "Loading UI",
        "error.tsx": "Error UI"
      }},
      "components/": {{
        "ui/": ["button.tsx", "card.tsx", "dialog.tsx"],
        "features/": {{
          "auth/": ["login-form.tsx", "register-form.tsx"],
          "todos/": ["todo-list.tsx", "todo-item.tsx"]
        }},
        "layouts/": ["header.tsx", "footer.tsx", "sidebar.tsx"]
      }},
      "lib/": {{
        "utils/": ["cn.ts", "validators.ts"],
        "hooks/": ["use-todos.ts", "use-auth.ts"],
        "api/": ["client.ts", "endpoints.ts"],
        "stores/": ["auth-store.ts", "ui-store.ts"],
        "types/": ["index.ts", "api.ts"]
      }},
      "actions/": ["todos.ts", "auth.ts"]
    }},
    "public/": ["images/", "fonts/"],
    "root": [
      "package.json",
      "next.config.ts",
      "tailwind.config.ts",
      "tsconfig.json",
      "components.json",
      ".eslintrc.json",
      ".prettierrc",
      ".gitignore",
      "README.md",
      ".env.example"
    ]
  }},

  "component_hierarchy": [
    {{
      "name": "RootLayout",
      "file": "app/layout.tsx",
      "type": "server-component",
      "purpose": "Root layout with providers",
      "children": ["Providers", "Header", "children", "Footer"],
      "dependencies": ["TanStack Query Provider", "Zustand store"]
    }},
    {{
      "name": "HomePage",
      "file": "app/page.tsx",
      "type": "server-component",
      "purpose": "Homepage with initial data",
      "data_fetching": "Server Component async fetch",
      "children": ["Hero", "FeatureList", "CTA"]
    }},
    {{
      "name": "TodoList",
      "file": "app/components/features/todos/todo-list.tsx",
      "type": "client-component",
      "purpose": "Interactive todo list",
      "state": ["todos (from TanStack Query)", "filter (local)"],
      "children": ["TodoItem", "AddTodoForm"]
    }}
  ],

  "state_management_setup": {{
    "zustand_stores": [
      {{
        "name": "useAuthStore",
        "file": "lib/stores/auth-store.ts",
        "state": ["user", "isAuthenticated"],
        "actions": ["login", "logout", "checkAuth"]
      }}
    ],
    "tanstack_query": {{
      "queries": [
        {{"key": "['todos']", "fn": "fetchTodos", "staleTime": "5min"}}
      ],
      "mutations": [
        {{"key": "createTodo", "fn": "createTodoMutation", "onSuccess": "invalidate todos query"}}
      ]
    }},
    "react_hook_form": {{
      "forms": ["LoginForm", "TodoForm"],
      "validation": "zod schemas"
    }}
  }},

  "shadcn_components": [
    "button",
    "card",
    "dialog",
    "form",
    "input",
    "label",
    "select",
    "tabs",
    "toast",
    "dropdown-menu"
  ],

  "routing_structure": {{
    "app/": {{
      "(marketing)/": {{
        "page.tsx": "Homepage",
        "about/page.tsx": "About page"
      }},
      "(dashboard)/": {{
        "layout.tsx": "Dashboard layout",
        "todos/page.tsx": "Todos page",
        "settings/page.tsx": "Settings page"
      }},
      "api/": {{
        "todos/route.ts": "Todos API endpoint"
      }}
    }}
  }},

  "implementation_steps": [
    {{
      "step": 1,
      "phase": "Setup",
      "action": "Initialize Next.js 15 project with TypeScript and Tailwind",
      "commands": [
        "npx create-next-app@latest my-app --typescript --tailwind --app --eslint",
        "cd my-app",
        "npm install"
      ],
      "expected_output": "Next.js project structure",
      "validation": "npm run dev works, TypeScript compiles"
    }},
    {{
      "step": 2,
      "phase": "Setup",
      "action": "Install dependencies and configure Shadcn UI",
      "commands": [
        "npm install zustand @tanstack/react-query zod react-hook-form @hookform/resolvers",
        "npx shadcn@latest init",
        "npx shadcn@latest add button card dialog form input label"
      ],
      "expected_output": "components/ui/ folder with Shadcn components",
      "validation": "components.json exists, Shadcn components importable"
    }},
    {{
      "step": 3,
      "phase": "Foundation",
      "action": "Set up root layout with providers",
      "files_to_create": ["app/layout.tsx", "app/providers.tsx"],
      "expected_output": "Root layout with TanStack Query Provider",
      "validation": "App renders without errors"
    }},
    {{
      "step": 4,
      "phase": "State",
      "action": "Create Zustand stores",
      "files_to_create": ["lib/stores/auth-store.ts", "lib/stores/ui-store.ts"],
      "expected_output": "Working Zustand stores",
      "validation": "Stores accessible in components"
    }},
    {{
      "step": 5,
      "phase": "UI",
      "action": "Build layout components",
      "files_to_create": [
        "components/layouts/header.tsx",
        "components/layouts/footer.tsx",
        "components/layouts/sidebar.tsx"
      ],
      "expected_output": "Reusable layout components",
      "validation": "Layouts render correctly, responsive"
    }},
    {{
      "step": 6,
      "phase": "Features",
      "action": "Implement todo feature",
      "files_to_create": [
        "components/features/todos/todo-list.tsx",
        "components/features/todos/todo-item.tsx",
        "components/features/todos/add-todo-form.tsx",
        "lib/hooks/use-todos.ts",
        "actions/todos.ts"
      ],
      "expected_output": "Working todo CRUD functionality",
      "validation": "Can create, read, update, delete todos"
    }},
    {{
      "step": 7,
      "phase": "Optimization",
      "action": "Add loading states and error boundaries",
      "files_to_create": ["app/loading.tsx", "app/error.tsx"],
      "expected_output": "Graceful loading and error handling",
      "validation": "Loading states show, errors caught"
    }},
    {{
      "step": 8,
      "phase": "Polish",
      "action": "Implement dark mode and animations",
      "files_to_modify": ["app/layout.tsx", "tailwind.config.ts"],
      "expected_output": "Dark mode toggle, smooth transitions",
      "validation": "Dark mode works, animations smooth"
    }}
  ],

  "performance_checklist": [
    "Use Server Components by default",
    "Add 'use client' only when needed",
    "Implement code splitting with dynamic imports",
    "Optimize images with next/image",
    "Optimize fonts with next/font",
    "Add loading.tsx for each route",
    "Implement Suspense boundaries",
    "Memoize expensive computations"
  ],

  "accessibility_checklist": [
    "Use semantic HTML (header, nav, main, footer)",
    "Add ARIA labels to interactive elements",
    "Ensure keyboard navigation (tab order)",
    "Test with screen reader",
    "Verify color contrast (WCAG AA)",
    "Add focus indicators",
    "Support reduced motion"
  ],

  "quality_checkpoints": [
    {{"phase": "Setup", "checks": ["TypeScript compiles", "ESLint passes", "Dev server starts"]}},
    {{"phase": "Foundation", "checks": ["Providers work", "Routing works", "Layouts render"]}},
    {{"phase": "Features", "checks": ["All features functional", "Forms validate", "Error handling works"]}},
    {{"phase": "Final", "checks": ["Build succeeds", "Lighthouse score > 90", "Accessibility audit passes"]}}
  ],

  "deployment_config": {{
    "netlify_toml": {{
      "build": {{
        "command": "npm run build",
        "publish": ".next"
      }},
      "functions_directory": ".netlify/functions"
    }},
    "environment_variables": ["DATABASE_URL", "NEXTAUTH_SECRET", "NEXTAUTH_URL"]
  }},

  "plan_summary": "Comprehensive implementation plan for modern Next.js 15 + Shadcn UI webapp with TypeScript, Zustand, TanStack Query, and Server Components"
}}

Create a clear, modern, step-by-step implementation plan using latest best practices."""

    async def execute_task_with_plan(
        self,
        task: Task,
        research: Dict,
        plan: Dict
    ) -> Dict[str, Any]:
        """
        Execute modern frontend implementation with research-backed plan

        Uses latest frameworks, UI libraries, and patterns
        """
        print(f"💻 [FRONTEND] Implementing modern webapp with research & plan")

        # Extract design spec from task metadata
        design_spec = {}
        if task.metadata and isinstance(task.metadata, dict):
            design_spec = task.metadata.get('design_spec', {})

        # Get modern tech stack from research
        framework = research.get('framework_recommendation', {}).get('framework', 'next.js-15')
        ui_library = research.get('ui_library_recommendation', {}).get('primary_library', 'shadcn-ui')
        tech_stack = research.get('technology_stack', {})

        # Log implementation task start
        log_event("frontend.modern_task_start",
                 task_id=task.task_id,
                 has_research=True,
                 has_plan=True,
                 framework=framework,
                 ui_library=ui_library,
                 has_design_spec=bool(design_spec),
                 task_description_length=len(task.description))

        # Create enhanced modern implementation prompt
        implementation_prompt = f"""You are an expert Frontend Developer implementing a production-ready modern webapp.

**IMPORTANT:** You have completed thorough research using MODERN frameworks and libraries. Use these findings to guide your implementation.

**Original Task:** {task.description}

**Design Specification:**
{design_spec}

**Research Findings (Modern Stack):**
{research}

**Implementation Plan:**
{plan}

**Your Task:**
Implement the complete, production-ready webapp following the research and plan using MODERN technologies.

**CRITICAL MODERN IMPLEMENTATION GUIDELINES:**

1. **Follow Modern Research Recommendations:**
   - Use the recommended framework: {framework}
   - Use the recommended UI library: {ui_library}
   - Use the technology stack: {tech_stack}
   - Follow the component hierarchy from the plan
   - Implement the modern state management strategy from the plan
   - Use the file structure from the plan

2. **Modern Code Quality:**
   - Write COMPLETE, WORKING code (NO placeholders, NO TODOs)
   - Use TypeScript strict mode throughout
   - Follow modern React patterns (Server Components, Suspense, Server Actions)
   - Implement proper error boundaries and loading states
   - Use modern hooks (useOptimistic, useFormStatus, useActionState)
   - Apply performance optimizations from the plan

3. **Modern File Structure:**
   Create ALL files according to the modern plan's file structure:
   {plan.get('file_structure', {})}

4. **Modern Dependencies:**
   Use the LATEST STABLE versions identified in research:
   - Production: {research.get('dependencies', {}).get('production', {})}
   - Dev: {research.get('dependencies', {}).get('dev', {})}

5. **Modern Patterns to Use:**
   - Server Components by default (Next.js 15)
   - 'use client' directive only when needed
   - Server Actions for form mutations
   - Streaming SSR with Suspense boundaries
   - Optimistic UI updates
   - Modern state management (Zustand, TanStack Query)
   - Shadcn UI components (if recommended)
   - Tailwind CSS v4 utility classes

6. **Output Format:**
   Return a comprehensive JSON with ALL modern files needed:

{{
  "framework": "{framework}",
  "framework_version": "15.0.0",
  "ui_library": "{ui_library}",
  "build_tool": "turbopack|vite",
  "typescript": true,

  "dependencies": {{
    "production": {research.get('dependencies', {}).get('production', {})},
    "dev": {research.get('dependencies', {}).get('dev', {})}
  }},

  "files": [
    {{
      "path": "package.json",
      "content": "Complete package.json with modern dependencies"
    }},
    {{
      "path": "app/layout.tsx",
      "content": "Root layout with providers (Server Component)"
    }},
    {{
      "path": "app/page.tsx",
      "content": "Homepage (Server Component with async data fetching)"
    }},
    {{
      "path": "app/providers.tsx",
      "content": "Client Component providers (TanStack Query, etc.)"
    }},
    {{
      "path": "components/ui/button.tsx",
      "content": "Shadcn UI button component (if using Shadcn)"
    }},
    {{
      "path": "components/features/todos/todo-list.tsx",
      "content": "Feature component with 'use client' if interactive"
    }},
    {{
      "path": "lib/stores/auth-store.ts",
      "content": "Zustand store (if using Zustand)"
    }},
    {{
      "path": "lib/hooks/use-todos.ts",
      "content": "TanStack Query hook (if using TanStack Query)"
    }},
    {{
      "path": "actions/todos.ts",
      "content": "Server Actions for mutations (if Next.js 15)"
    }},
    {{
      "path": "tailwind.config.ts",
      "content": "Tailwind CSS v4 configuration with design tokens"
    }},
    {{
      "path": "components.json",
      "content": "Shadcn UI configuration (if using Shadcn)"
    }},
    {{
      "path": "next.config.ts",
      "content": "Next.js 15 configuration with Turbopack (if Next.js)"
    }},
    {{
      "path": "tsconfig.json",
      "content": "TypeScript strict configuration"
    }},
    {{
      "path": ".gitignore",
      "content": "Comprehensive modern .gitignore"
    }},
    {{
      "path": "README.md",
      "content": "Comprehensive README with modern stack documentation"
    }},
    {{
      "path": ".env.example",
      "content": "Environment variables template"
    }}
  ],

  "setup_instructions": [
    "npm install",
    "npm run dev"
  ],

  "build_commands": {{
    "dev": "next dev --turbo",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }},

  "modern_features": [
    "Server Components for data fetching",
    "Server Actions for mutations",
    "Streaming SSR with Suspense",
    "Optimistic UI updates",
    "Shadcn UI components",
    "Tailwind CSS v4",
    "TypeScript strict mode",
    "Dark mode support"
  ],

  "deployment_notes": "Deployment instructions for Netlify with modern Next.js",
  "implementation_summary": "What was implemented using modern patterns"
}}

**REMEMBER:**
- Use the LATEST STABLE versions of all frameworks
- Follow modern patterns (Server Components, Suspense, Server Actions)
- Use modern UI libraries (Shadcn UI, MUI, etc.)
- Implement with TypeScript strict mode
- Create production-ready, deployable modern code
- Include ALL necessary modern configuration files
- NO placeholders, NO TODOs
- Follow the modern research-backed plan precisely

Implement now, using cutting-edge modern technologies!"""

        try:
            # Trace Claude API call for modern implementation
            with trace_operation("frontend_implement_modern",
                               task_id=task.task_id,
                               framework=framework,
                               ui_library=ui_library,
                               has_research=True,
                               has_plan=True,
                               prompt_length=len(implementation_prompt)) as span:

                # Get implementation from Claude with modern context
                response = await self.claude_sdk.send_message(implementation_prompt)

                # Track response metrics
                span.set_attribute("response_length", len(response))
                log_metric("frontend.llm_response_length", len(response))

            # Parse implementation
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                implementation = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                implementation = json.loads(response)
            else:
                implementation = {
                    "implementation_description": response,
                    "note": "Modern implementation created with research & planning"
                }

            # Track modern implementation metrics
            files_count = len(implementation.get('files', []))
            implementation_framework = implementation.get('framework', framework)
            implementation_ui_library = implementation.get('ui_library', ui_library)
            has_typescript = implementation.get('typescript', True)

            log_event("frontend.modern_implementation_created",
                     task_id=task.task_id,
                     files_count=files_count,
                     framework=implementation_framework,
                     ui_library=implementation_ui_library,
                     has_typescript=has_typescript,
                     research_backed=True)

            log_metric("frontend.files_generated", files_count)

            print(f"✅ [FRONTEND] Modern research-backed implementation completed ({files_count} files)")
            print(f"   Framework: {implementation_framework}")
            print(f"   UI Library: {implementation_ui_library}")

            return {
                "status": "completed",
                "implementation": implementation,
                "raw_response": response,
                "research_used": True,
                "research_summary": research.get('research_summary', 'Modern research completed'),
                "plan_summary": plan.get('plan_summary', 'Modern plan created')
            }

        except Exception as e:
            print(f"❌ [FRONTEND] Error during modern implementation: {e}")
            import traceback
            traceback.print_exc()

            # Log error with context
            log_error(e, "frontend_implement_modern",
                     task_id=task.task_id,
                     framework=framework,
                     ui_library=ui_library,
                     has_research=True,
                     has_plan=True)

            # Fallback
            return {
                "status": "completed_with_fallback",
                "implementation": {
                    "error": str(e),
                    "note": "Fallback modern implementation"
                }
            }

    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute implementation task using Claude AI (backward compatibility)

        This now defaults to modern frameworks but without research & planning.
        Used when enable_research_planning=False
        """
        print(f"💻 [FRONTEND] Implementing with modern stack: {task.description} (direct execution)")

        # Log implementation task start (direct modern mode)
        log_event("frontend.task_start",
                 task_id=task.task_id,
                 has_research=False,
                 has_plan=False,
                 execution_mode="direct_modern",
                 task_description_length=len(task.description))

        # Extract design spec from task metadata
        design_spec = {}
        if task.metadata and isinstance(task.metadata, dict):
            design_spec = task.metadata.get('design_spec', {})

        # Create comprehensive modern implementation prompt
        implementation_prompt = f"""You are an expert Frontend Developer implementing a production-ready modern webapp using cutting-edge frameworks and libraries.

**User Request:** {task.description}

**Design Specification:**
{design_spec}

Create a complete, production-ready MODERN webapp implementation using the latest technologies:

**MODERN TECH STACK (Use Latest Versions):**
- **Framework:** Next.js 15 with App Router & Server Components (or Vite + React 19 for SPA)
- **UI Library:** Shadcn UI (Tailwind + Radix UI) - HIGHLY RECOMMENDED
- **Styling:** Tailwind CSS v4
- **TypeScript:** v5+ with strict mode
- **State:** Zustand (global) + TanStack Query (server state) + React Hook Form (forms)
- **Icons:** Lucide React
- **Build Tool:** Turbopack (Next.js) or Vite

**IMPLEMENTATION REQUIREMENTS:**

1. **Project Structure & Configuration Files**
   - package.json with LATEST versions
   - next.config.ts (or vite.config.ts)
   - tailwind.config.ts
   - components.json (Shadcn UI config)
   - tsconfig.json (strict mode)
   - .eslintrc.json
   - .prettierrc
   - .gitignore
   - README.md
   - .env.example

2. **Modern App Structure (Next.js 15 App Router)**
   - app/layout.tsx - Root layout (Server Component)
   - app/page.tsx - Homepage (Server Component with async data)
   - app/providers.tsx - Client providers (TanStack Query, etc.)
   - app/loading.tsx - Loading UI
   - app/error.tsx - Error UI
   - components/ui/ - Shadcn UI components
   - components/features/ - Feature components
   - components/layouts/ - Layout components
   - lib/stores/ - Zustand stores
   - lib/hooks/ - Custom hooks (TanStack Query, etc.)
   - lib/utils/ - Utilities
   - actions/ - Server Actions

3. **Modern React Patterns**
   - Server Components by default
   - 'use client' directive only when needed
   - Server Actions for form mutations
   - Suspense boundaries for streaming
   - useOptimistic for optimistic updates
   - Error boundaries for error handling
   - Loading states everywhere

4. **Shadcn UI Components**
   - Install with: npx shadcn@latest add button card dialog form input
   - Use components from @/components/ui/
   - Customize with Tailwind classes
   - Implement dark mode toggle

5. **TypeScript (Strict Mode)**
   - Proper type definitions throughout
   - No 'any' types
   - Interface for props
   - Type-safe API calls

6. **Styling with Tailwind CSS v4**
   - Utility-first classes
   - Responsive design (mobile-first)
   - Dark mode support (class strategy)
   - Custom design tokens in config
   - Smooth transitions and animations

7. **State Management (Modern)**
   - Zustand for client state (auth, UI state)
   - TanStack Query for server state (API data)
   - React Hook Form + Zod for forms
   - URL searchParams for URL state

8. **Performance Optimizations**
   - next/image for image optimization
   - next/font for font optimization
   - Dynamic imports for code splitting
   - React.memo for expensive components
   - Streaming SSR with Suspense

9. **Accessibility (WCAG 2.1 AA)**
   - Semantic HTML
   - ARIA labels where needed
   - Keyboard navigation
   - Focus indicators
   - Color contrast compliance

10. **Documentation**
    - Comprehensive README with setup instructions
    - Environment variables documented
    - Build and deployment commands
    - Technology stack explanation

**CRITICAL REQUIREMENTS:**
- Generate COMPLETE, WORKING modern code (NO placeholders, NO TODOs)
- Use LATEST STABLE versions of all libraries
- Implement with TypeScript strict mode
- Use Server Components and Server Actions (Next.js 15)
- Include Shadcn UI components
- Style with Tailwind CSS v4
- Add proper error handling and loading states
- Make it production-ready and deployment-ready
- Include ALL necessary configuration files

**Output Format (JSON):**
{{
  "framework": "next.js-15",
  "framework_version": "15.0.0",
  "ui_library": "shadcn-ui",
  "styling": "tailwind-v4",
  "build_tool": "turbopack",
  "typescript": true,
  "state_management": "zustand + tanstack-query",

  "files": [
    {{"path": "package.json", "content": "...COMPLETE with LATEST versions..."}},
    {{"path": "app/layout.tsx", "content": "...Root layout Server Component..."}},
    {{"path": "app/page.tsx", "content": "...Homepage Server Component..."}},
    {{"path": "app/providers.tsx", "content": "...Client providers..."}},
    {{"path": "components/ui/button.tsx", "content": "...Shadcn button..."}},
    {{"path": "components/ui/card.tsx", "content": "...Shadcn card..."}},
    {{"path": "components/features/...", "content": "...Feature components..."}},
    {{"path": "lib/stores/auth-store.ts", "content": "...Zustand store..."}},
    {{"path": "lib/hooks/use-todos.ts", "content": "...TanStack Query hook..."}},
    {{"path": "actions/todos.ts", "content": "...Server Actions..."}},
    {{"path": "tailwind.config.ts", "content": "...Tailwind v4 config..."}},
    {{"path": "components.json", "content": "...Shadcn config..."}},
    {{"path": "next.config.ts", "content": "...Next.js 15 config..."}},
    {{"path": "tsconfig.json", "content": "...TypeScript strict config..."}},
    {{"path": ".gitignore", "content": "...Complete .gitignore..."}},
    {{"path": "README.md", "content": "...Comprehensive README..."}},
    {{"path": ".env.example", "content": "...Environment variables..."}},
    // Additional files as needed
  ],

  "dependencies": {{
    "next": "^15.0.0",
    "react": "^19.0.0",
    "typescript": "^5.3.0",
    "@radix-ui/react-dialog": "^1.0.0",
    "tailwindcss": "^4.0.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.0.0"
  }},

  "dev_dependencies": {{
    "@types/react": "^19.0.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }},

  "setup_instructions": [
    "npm install",
    "npm run dev"
  ],

  "build_commands": {{
    "dev": "next dev --turbo",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }},

  "modern_features": [
    "Next.js 15 App Router",
    "Server Components & Server Actions",
    "Shadcn UI components",
    "Tailwind CSS v4",
    "TypeScript strict mode",
    "Zustand + TanStack Query",
    "Dark mode support",
    "Streaming SSR with Suspense"
  ],

  "deployment_notes": "Complete instructions for Netlify deployment",
  "github_ready": true
}}

Generate complete, production-ready, MODERN code that implements the design specification using cutting-edge frameworks and libraries!"""

        try:
            # Trace Claude API call for direct modern implementation
            with trace_operation("frontend_implement_direct_modern",
                               task_id=task.task_id,
                               has_research=False,
                               has_plan=False,
                               execution_mode="direct_modern",
                               prompt_length=len(implementation_prompt)) as span:

                # Get implementation from Claude
                response = await self.claude_sdk.send_message(implementation_prompt)

                # Track response metrics
                span.set_attribute("response_length", len(response))
                log_metric("frontend.llm_response_length", len(response))

            # Try to extract JSON from response
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                implementation = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                implementation = json.loads(response)
            else:
                # Claude returned code directly, structure it
                implementation = {
                    "framework": "next.js-15",
                    "ui_library": "shadcn-ui",
                    "typescript": True,
                    "files": [{
                        "path": "app/page.tsx",
                        "content": response
                    }],
                    "dependencies": ["next", "react", "typescript", "tailwindcss"],
                    "note": "Modern code generated by Claude AI"
                }

            # Track modern implementation metrics
            files_count = len(implementation.get('files', []))
            framework = implementation.get('framework', 'next.js-15')
            ui_library = implementation.get('ui_library', 'unknown')
            has_typescript = implementation.get('typescript', True)

            log_event("frontend.modern_implementation_created",
                     task_id=task.task_id,
                     files_count=files_count,
                     framework=framework,
                     ui_library=ui_library,
                     has_typescript=has_typescript,
                     research_backed=False,
                     execution_mode="direct_modern")

            log_metric("frontend.files_generated", files_count)

            print(f"✅ [FRONTEND] Modern implementation completed - {files_count} files generated")
            print(f"   Framework: {framework}")
            print(f"   UI Library: {ui_library}")

            return {
                "status": "completed",
                "implementation": implementation,
                "raw_response": response
            }

        except Exception as e:
            print(f"❌ [FRONTEND] Error during modern implementation: {e}")
            import traceback
            traceback.print_exc()

            # Log error with context
            log_error(e, "frontend_implement_direct_modern",
                     task_id=task.task_id,
                     has_research=False,
                     has_plan=False,
                     execution_mode="direct_modern")

            # Fallback implementation
            return {
                "status": "completed_with_fallback",
                "implementation": {
                    "framework": "next.js-15",
                    "ui_library": "shadcn-ui",
                    "typescript": True,
                    "files": [{
                        "path": "app/page.tsx",
                        "content": "// Error during generation - see logs"
                    }],
                    "error": str(e),
                    "note": "Fallback modern implementation"
                }
            }

    async def review_artifact(self, artifact: Any) -> Dict[str, Any]:
        """
        Review design specifications for implementability using Claude AI

        Evaluates feasibility with modern frameworks and libraries
        """
        print(f"🔍 [FRONTEND] Reviewing design specification for modern implementation")

        # Log review start
        log_event("frontend.review_start",
                 artifact_type="design_specification",
                 modern_review=True)

        review_prompt = f"""You are an expert Frontend Developer reviewing a design specification for implementability with MODERN frameworks and libraries.

**Design Specification:**
{artifact}

Review the design and provide feedback on:

1. **Implementability with Modern Stack**
   - Can this design be implemented with Next.js 15 + Shadcn UI?
   - Are there any technical challenges with modern frameworks?
   - Are Server Components applicable?
   - Can Server Actions replace API routes?

2. **Modern UI Library Compatibility**
   - Is this suitable for Shadcn UI components?
   - Would MUI be a better choice?
   - Are Radix UI primitives needed?
   - Custom components required?

3. **Performance Considerations (Modern)**
   - Server Components usage opportunities?
   - Streaming SSR applicable?
   - Code splitting needed?
   - Image/font optimization required?

4. **State Management Needs**
   - Zustand for global state?
   - TanStack Query for server state?
   - Server Actions for mutations?
   - URL state management needed?

5. **Missing Information**
   - What design details are missing or unclear?
   - What additional specifications would be helpful?

6. **Technical Concerns**
   - Accessibility issues?
   - Browser compatibility concerns?
   - Mobile responsiveness challenges?

7. **Modern Stack Recommendations**
   - Recommended framework (Next.js 15, Vite + React, etc.)
   - Recommended UI library (Shadcn UI, MUI, etc.)
   - Alternative approaches using modern tools

Output as JSON with:
- "implementable": boolean
- "modern_stack_compatible": boolean
- "recommended_framework": string
- "recommended_ui_library": string
- "confidence": number 1-10
- "questions": array of strings
- "concerns": array of strings
- "modern_recommendations": array of strings
- "estimated_complexity": string ("simple", "moderate", "complex")

Be specific and recommend modern solutions."""

        try:
            # Trace Claude API call for modern design review
            with trace_operation("frontend_review_design_modern",
                               artifact_type="design_specification",
                               modern_review=True,
                               prompt_length=len(review_prompt)) as span:

                # Get review from Claude
                response = await self.claude_sdk.send_message(review_prompt)

                # Track response metrics
                span.set_attribute("response_length", len(response))

            # Try to extract JSON from response
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                review = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                review = json.loads(response)
            else:
                # Claude didn't return pure JSON, wrap it
                review = {
                    "implementable": True,
                    "modern_stack_compatible": True,
                    "recommended_framework": "next.js-15",
                    "recommended_ui_library": "shadcn-ui",
                    "confidence": 8,
                    "questions": [],
                    "concerns": [],
                    "modern_recommendations": [response],
                    "estimated_complexity": "moderate"
                }

            # Track modern review metrics
            implementable = review.get("implementable", True)
            modern_compatible = review.get("modern_stack_compatible", True)
            confidence = review.get("confidence", 0)
            recommended_framework = review.get("recommended_framework", "unknown")
            recommended_ui_library = review.get("recommended_ui_library", "unknown")

            log_event("frontend.modern_design_review_completed",
                     implementable=implementable,
                     modern_stack_compatible=modern_compatible,
                     confidence=confidence,
                     recommended_framework=recommended_framework,
                     recommended_ui_library=recommended_ui_library)

            log_metric("frontend.design_review_confidence", confidence)

            print(f"✅ [FRONTEND] Modern design review completed")
            print(f"   Implementable: {implementable}")
            print(f"   Modern Compatible: {modern_compatible}")
            print(f"   Recommended: {recommended_framework} + {recommended_ui_library}")

            return review

        except Exception as e:
            print(f"❌ [FRONTEND] Error during modern review: {e}")
            import traceback
            traceback.print_exc()

            # Log error with context
            log_error(e, "frontend_review_design_modern",
                     artifact_type="design_specification")

            # Fallback to basic approval
            return {
                "implementable": True,
                "modern_stack_compatible": True,
                "recommended_framework": "next.js-15",
                "recommended_ui_library": "shadcn-ui",
                "confidence": 7,
                "questions": [],
                "concerns": [f"Review error: {str(e)}"],
                "modern_recommendations": [],
                "estimated_complexity": "moderate"
            }

    async def apply_visual_feedback(self, feedback: List[Dict], iteration: int, current_implementation: Dict) -> Dict:
        """
        Apply visual design feedback from Designer agent

        This method takes feedback from the Designer's visual review (Playwright screenshots)
        and makes targeted changes to fix visual issues.

        Args:
            feedback: List of feedback items from designer's visual review
            iteration: Current iteration number
            current_implementation: Current implementation (files, structure)

        Returns:
            Dictionary with:
            - status: "completed" | "failed"
            - changes_made: List of changes applied
            - files_updated: List of files that were modified
        """
        print(f"🔧 [FRONTEND] Applying visual feedback (iteration {iteration})...")
        print(f"   Received {len(feedback)} feedback items")

        try:
            # Group feedback by severity
            critical_feedback = [f for f in feedback if f.get('severity') == 'critical']
            major_feedback = [f for f in feedback if f.get('severity') == 'major']
            minor_feedback = [f for f in feedback if f.get('severity') == 'minor']

            print(f"   Critical: {len(critical_feedback)}, Major: {len(major_feedback)}, Minor: {len(minor_feedback)}")

            # Create prompt for Claude to apply feedback
            feedback_prompt = f"""You are a Frontend Developer receiving visual feedback from a UI/UX Designer.

The Designer has reviewed your implementation using Playwright screenshots and identified {len(feedback)} visual issues to fix.

**Current Iteration:** {iteration}

**Visual Feedback to Apply:**
{json.dumps(feedback, indent=2)}

**Your Current Implementation:**
{json.dumps(current_implementation, indent=2)}

**Your Task:**
1. Review each feedback item carefully
2. Make TARGETED, PRECISE changes to fix the visual issues
3. Focus on the EXACT issues mentioned - don't refactor unrelated code
4. Prioritize by severity: Critical → Major → Minor
5. Update CSS/Tailwind classes, component styles, or layouts as needed

**Guidelines:**
- Make MINIMAL changes - only fix reported issues
- Don't introduce new features or changes
- Keep existing functionality intact
- Use exact color codes, spacing values, font sizes specified in feedback
- Test that changes don't break existing code

**Output Format (JSON):**
{{
  "changes_made": [
    {{
      "feedback_item": "which feedback item this addresses",
      "file": "path/to/file",
      "change_type": "css|component|layout|styling",
      "change_description": "what was changed",
      "code_before": "relevant code before change (if applicable)",
      "code_after": "relevant code after change"
    }}
  ],
  "files_updated": [
    {{
      "path": "components/Header.tsx",
      "content": "...full updated file content..."
    }}
  ],
  "feedback_addressed": ["list of feedback items successfully addressed"],
  "feedback_skipped": ["list of feedback items skipped with reasons"],
  "iteration": {iteration},
  "summary": "Brief summary of changes made"
}}

Make precise, targeted fixes. Return the complete updated file contents for any files you modify."""

            with trace_operation("frontend_apply_visual_feedback",
                               iteration=iteration,
                               feedback_count=len(feedback),
                               critical_count=len(critical_feedback)) as span:

                response = await self.claude_sdk.send_message(feedback_prompt)
                span.set_attribute("response_length", len(response))

            # Parse JSON response
            import json
            import re

            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            elif response.strip().startswith('{'):
                result = json.loads(response)
            else:
                # Fallback: couldn't parse JSON
                result = {
                    "changes_made": [],
                    "files_updated": [],
                    "feedback_addressed": [],
                    "feedback_skipped": feedback,
                    "iteration": iteration,
                    "summary": f"Unable to parse response: {response[:200]}",
                    "error": "JSON parsing failed"
                }

            # Track metrics
            changes_count = len(result.get("changes_made", []))
            files_updated_count = len(result.get("files_updated", []))
            feedback_addressed_count = len(result.get("feedback_addressed", []))

            log_event("frontend.visual_feedback_applied",
                     iteration=iteration,
                     feedback_count=len(feedback),
                     changes_count=changes_count,
                     files_updated_count=files_updated_count,
                     feedback_addressed_count=feedback_addressed_count,
                     critical_count=len(critical_feedback))

            log_metric("frontend.feedback_addressed_percentage",
                      (feedback_addressed_count / len(feedback) * 100) if feedback else 0)

            print(f"✅ [FRONTEND] Applied visual feedback")
            print(f"   Changes made: {changes_count}")
            print(f"   Files updated: {files_updated_count}")
            print(f"   Feedback addressed: {feedback_addressed_count}/{len(feedback)}")

            return {
                "status": "completed",
                "changes_made": result.get("changes_made", []),
                "files_updated": result.get("files_updated", []),
                "feedback_addressed": result.get("feedback_addressed", []),
                "feedback_skipped": result.get("feedback_skipped", []),
                "summary": result.get("summary", ""),
                "iteration": iteration
            }

        except Exception as e:
            print(f"❌ [FRONTEND] Error applying visual feedback: {e}")
            import traceback
            traceback.print_exc()

            log_error(e, "frontend_apply_visual_feedback",
                     iteration=iteration,
                     feedback_count=len(feedback))

            return {
                "status": "failed",
                "error": str(e),
                "changes_made": [],
                "files_updated": [],
                "feedback_addressed": [],
                "feedback_skipped": feedback,
                "iteration": iteration
            }
