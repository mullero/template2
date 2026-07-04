/**
 * Centralized user-facing strings. Every string rendered in JSX must be a named
 * export here — no hard-coded text in components. Localization / rebranding is a
 * single-file change.
 */

export const appStrings = {
  productName: 'App Skeleton',
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

export const documentStrings = {
  pageTitle: 'Documents',
  uploadButton: 'Upload document',
  uploading: 'Uploading…',
  empty: 'No documents yet. Upload one to start extraction.',
  pendingReviewTab: 'Pending review',
  allTab: 'All',
  reviewBanner: (count: number): string =>
    count === 1 ? '1 document awaiting review' : `${count} documents awaiting review`,
  acceptButton: 'Accept',
  rejectButton: 'Reject',
  duplicateNotice: 'This document was already uploaded.',
  loadError: 'Could not load documents.',
  uploadError: 'Could not upload the document.',
  columnName: 'File',
  columnStatus: 'Status',
  columnConfidence: 'Confidence',
  columnCreated: 'Created',
  columnActions: 'Actions',
} as const;

export const jobStrings = {
  activeJobs: (count: number): string =>
    count === 1 ? '1 background job running…' : `${count} background jobs running…`,
} as const;

export const navStringsExtra = {
  documents: 'Documents',
} as const;

