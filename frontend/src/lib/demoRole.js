export const DEMO_ROLES = [
  {
    value: "admin",
    label: "Admin",
    blurb: "Full demo access",
  },
  {
    value: "engineer",
    label: "Engineer",
    blurb: "Owns SOP improvements",
  },
  {
    value: "supervisor",
    label: "Supervisor",
    blurb: "Tracks alerts and sessions",
  },
  {
    value: "operator",
    label: "Operator",
    blurb: "Read-only floor view",
  },
];

export const DEFAULT_DEMO_ROLE = DEMO_ROLES[0].value;
const STORAGE_KEY = "vision-sop-demo-role";

export function getDemoRole() {
  if (typeof window === "undefined") return DEFAULT_DEMO_ROLE;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return DEMO_ROLES.some((role) => role.value === stored) ? stored : DEFAULT_DEMO_ROLE;
}

export function setDemoRole(role) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, role);
}

export function getDemoRoleMeta(role) {
  return DEMO_ROLES.find((item) => item.value === role) || DEMO_ROLES[0];
}
