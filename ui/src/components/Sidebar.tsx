import { BarChart3, KeyRound, LayoutDashboard, LogOut, Settings, Users, FolderKanban, FlaskConical, Tag } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { useLogout } from "../api/hooks";

const navItems = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/usage", label: "Usage", icon: BarChart3 },
  { to: "/requests", label: "Requests", icon: Users },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/pricing", label: "Pricing", icon: Tag },
  { to: "/test-keys", label: "Test Keys", icon: FlaskConical },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/keys", label: "API Keys", icon: KeyRound }
];

export default function Sidebar() {
  const logout = useLogout();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout.mutate(undefined, {
      onSuccess: () => navigate("/login")
    });
  };

  return (
    <aside className="flex h-full w-64 flex-col gap-6 border-r border-[var(--border)] bg-[var(--surface)] p-6">
      <div className="text-lg font-semibold">LatticeAI</div>
      <nav className="flex flex-1 flex-col gap-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                isActive ? "bg-[var(--surface-2)] text-[var(--primary)]" : "text-[var(--muted)] hover:text-[var(--text)]"
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <button
        onClick={handleLogout}
        className="flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-[var(--muted)] hover:text-[var(--text)]"
      >
        <LogOut size={18} />
        Logout
      </button>
    </aside>
  );
}
