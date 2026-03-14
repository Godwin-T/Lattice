import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLogin } from "../api/hooks";

export default function Login() {
  const navigate = useNavigate();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate(
      { email, password },
      {
        onSuccess: () => navigate("/"),
      }
    );
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 shadow-[var(--shadow)]">
        <h1 className="text-2xl font-semibold">Welcome back</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">Login to access your LatticeAI dashboard.</p>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full rounded-xl border border-[var(--border)] bg-transparent px-4 py-3"
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="w-full rounded-xl border border-[var(--border)] bg-transparent px-4 py-3"
            required
          />
          <button
            type="submit"
            className="w-full rounded-xl bg-[var(--primary)] px-4 py-3 font-medium text-white"
            disabled={login.isPending}
          >
            {login.isPending ? "Signing in..." : "Sign in"}
          </button>
        </form>
        {login.isError && (
          <p className="mt-3 text-sm text-[var(--danger)]">Invalid credentials or server error.</p>
        )}
      </div>
    </div>
  );
}
