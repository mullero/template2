/**
 * Centralized user-facing strings. Every string rendered in JSX must be a named
 * export here — no hard-coded text in components. Localization / rebranding is a
 * single-file change.
 */

export const appStrings = {
  productName: 'machote',
  tagline: 'Multi-tenant SaaS starter',
} as const;

export const navStrings = {
  projects: 'Projects',
  signOut: 'Sign out',
  toggleTheme: 'Toggle theme',
} as const;

export const authStrings = {
  loginTitle: 'Sign in',
  emailLabel: 'Email',
  passwordLabel: 'Password',
  signInButton: 'Sign in',
  signInWithGoogle: 'Sign in with Google',
  forgotPassword: 'Forgot password?',
  loadingSession: 'Loading your session…',
  bootstrapTitle: 'Set up your workspace',
  bootstrapTenantLabel: 'Tenant ID',
  bootstrapButton: 'Create workspace',
  signInFailed: 'Sign in failed. Check your credentials and try again.',
} as const;

export const projectStrings = {
  pageTitle: 'Projects',
  empty: 'No projects yet. Create your first one.',
  nameLabel: 'Name',
  descriptionLabel: 'Description',
  statusLabel: 'Status',
  createButton: 'Create project',
  creating: 'Creating…',
  deleteButton: 'Delete',
  loadError: 'Could not load projects.',
  createError: 'Could not create the project.',
  deleteError: 'Could not delete the project.',
  columnName: 'Name',
  columnStatus: 'Status',
  columnCreated: 'Created',
  columnActions: 'Actions',
  totalKpi: 'Total projects',
  activeKpi: 'Active projects',
} as const;

export const commonStrings = {
  loading: 'Loading…',
  retry: 'Retry',
  cancel: 'Cancel',
  notFound: 'Page not found',
} as const;
