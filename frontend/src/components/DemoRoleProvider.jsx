import { createContext, useContext, useMemo, useState } from "react";
import { getDemoRole, setDemoRole } from "../lib/demoRole.js";

const DemoRoleContext = createContext(null);

export function DemoRoleProvider({ children }) {
  const [role, setRoleState] = useState(getDemoRole);

  const value = useMemo(
    () => ({
      role,
      setRole(nextRole) {
        setDemoRole(nextRole);
        setRoleState(nextRole);
      },
    }),
    [role]
  );

  return <DemoRoleContext.Provider value={value}>{children}</DemoRoleContext.Provider>;
}

export function useDemoRole() {
  const context = useContext(DemoRoleContext);
  if (!context) {
    throw new Error("useDemoRole must be used within DemoRoleProvider");
  }
  return context;
}
