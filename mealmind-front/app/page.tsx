"use client";

import { useEffect, useMemo, useState } from "react";

const PINK = "rgb(247,93,247)";

type Sex = "male" | "female";
type Goal = "lose_fat" | "maintain" | "gain";
type Activity = "low" | "medium" | "high";

type ProfileIn = {
  sex: Sex;
  age: number;
  height_cm: number;
  weight_kg: number;
  goal: Goal;
  activity_level: Activity;
  budget_kzt_per_day: number;
};

type ProfileOut = ProfileIn & { user_id: string };

type ProductOut = {
  id: string;
  name: string;
  kcal_per_100g: number;
  protein_per_100g: number;
  fat_per_100g: number;
  carbs_per_100g: number;
  price_kzt_per_100g: number;
};

type SeedResult = { total: number; inserted: number; skipped: number };

type MealPlanItem = {
  meal_type: string;
  product_id: string;
  name: string;
  grams: number;
  kcal: number;
  cost_kzt: number;
};

type MealPlanOut = {
  id: string;
  user_id: string;
  plan_date: string;
  target_kcal: number;
  total_kcal: number;
  total_cost_kzt: number;
  items: MealPlanItem[];
};

type ShoppingItem = {
  product_id: string;
  name: string;
  total_grams: number;
  total_kcal: number;
  total_cost_kzt: number;
};

type WeekPlanOut = {
  user_id: string;
  start_date: string;
  end_date: string;
  total_week_kcal: number;
  total_week_cost_kzt: number;
  plans: MealPlanOut[];
  shopping_list: ShoppingItem[];
};

// AUTH
type TokenOut = { access_token: string; token_type?: string; user_id?: string };
type MeOut = { id?: string; email?: string; created_at?: string; user_id?: string };

function isSex(v: unknown): v is Sex {
  return v === "male" || v === "female";
}
function isGoal(v: unknown): v is Goal {
  return v === "lose_fat" || v === "maintain" || v === "gain";
}
function isActivity(v: unknown): v is Activity {
  return v === "low" || v === "medium" || v === "high";
}

export default function Page() {
  const API = useMemo(
    () => process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000",
    []
  );

  // ===== AUTH STATE =====
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");

  const [token, setToken] = useState<string>(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem("mealmind_token") ?? "";
  });

  // debug only
  const [userId, setUserId] = useState<string>(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem("mealmind_user_id") ?? "";
  });

  useEffect(() => {
    const savedToken = localStorage.getItem("mealmind_token");
    if (savedToken && savedToken !== token) setToken(savedToken);

    const savedUid = localStorage.getItem("mealmind_user_id");
    if (savedUid && savedUid !== userId) setUserId(savedUid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [profile, setProfile] = useState<ProfileIn>({
    sex: "male",
    age: 21,
    height_cm: 180,
    weight_kg: 80,
    goal: "lose_fat",
    activity_level: "medium",
    budget_kzt_per_day: 2500,
  });

  const [profileLoaded, setProfileLoaded] = useState<ProfileOut | null>(null);

  const [planDate, setPlanDate] = useState<string>(() =>
    new Date().toISOString().slice(0, 10)
  );
  const [plan, setPlan] = useState<MealPlanOut | null>(null);
  const [week, setWeek] = useState<WeekPlanOut | null>(null);
  const [weekDays, setWeekDays] = useState<number>(7);

  const [status, setStatus] = useState<string>("");

  // PRODUCTS
  const [products, setProducts] = useState<ProductOut[]>([]);
  const [productQuery, setProductQuery] = useState("");

  async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${API}${path}`, {
      ...init,
      headers: {
        ...(init?.headers ?? {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    const text = await res.text().catch(() => "");

    if (!res.ok) {
      throw new Error(`${res.status} ${res.statusText} ${text}`.trim());
    }

    if (!text) return undefined as T;

    try {
      return JSON.parse(text) as T;
    } catch {
      throw new Error(`Response is not JSON: ${text.slice(0, 300)}`);
    }
  }

  function requireToken(): boolean {
    if (!token) {
      setStatus("No token. Please Login/Register first.");
      return false;
    }
    return true;
  }

  async function register() {
    setStatus("Registering...");
    try {
      const data = await apiFetch<TokenOut>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });

      setToken(data.access_token);
      localStorage.setItem("mealmind_token", data.access_token);

      if (data.user_id) {
        setUserId(data.user_id);
        localStorage.setItem("mealmind_user_id", data.user_id);
      }

      setStatus("Registered ✅");
      await loadProfile();
    } catch (err) {
      setStatus(`Register failed: ${String(err)}`);
    }
  }

  async function login() {
    setStatus("Logging in...");
    try {
      const data = await apiFetch<TokenOut>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });

      if (!data?.access_token) {
        setStatus("Login failed: no access_token");
        return;
      }

      setToken(data.access_token);
      localStorage.setItem("mealmind_token", data.access_token);

      if (data.user_id) {
        setUserId(data.user_id);
        localStorage.setItem("mealmind_user_id", data.user_id);
      }

      setStatus("Logged in ✅");
      await loadProfile();
    } catch (err) {
      setStatus(`Login failed: ${String(err)}`);
    }
  }

  function clearToken() {
    setToken("");
    localStorage.removeItem("mealmind_token");

    setProfileLoaded(null);
    setPlan(null);
    setWeek(null);

    setStatus("Token cleared ✅");
  }

  async function me() {
    if (!requireToken()) return;

    setStatus("Loading /me ...");
    try {
      const data = await apiFetch<MeOut>("/api/v1/auth/me");
      const uid = data?.user_id ?? data?.id;

      if (uid) {
        setUserId(uid);
        localStorage.setItem("mealmind_user_id", uid);
      }

      setStatus(`Me ✅ ${data?.email ?? ""}`);
    } catch (err) {
      setStatus(`Me failed: ${String(err)}`);
    }
  }

  // ===== PROFILE (/profiles/me) =====
  async function loadProfile() {
    if (!requireToken()) return;

    setStatus("Loading profile...");
    try {
      const data = await apiFetch<ProfileOut>("/api/v1/profiles/me");

      setProfileLoaded(data);
      setProfile({
        sex: isSex(data.sex) ? data.sex : "male",
        age: Number(data.age) || 21,
        height_cm: Number(data.height_cm) || 180,
        weight_kg: Number(data.weight_kg) || 80,
        goal: isGoal(data.goal) ? data.goal : "maintain",
        activity_level: isActivity(data.activity_level)
          ? data.activity_level
          : "medium",
        budget_kzt_per_day: Number(data.budget_kzt_per_day) || 2500,
      });

      setStatus("Profile loaded ✅");
    } catch (err) {
      const msg = String(err);
      if (msg.includes("404")) {
        setProfileLoaded(null);
        setStatus("Profile not found. Create it 👇");
        return;
      }
      setProfileLoaded(null);
      setStatus(`Load profile failed: ${msg}`);
    }
  }

  async function saveProfile() {
    if (!requireToken()) return;

    setStatus(profileLoaded ? "Updating profile..." : "Creating profile...");
    try {
      if (!profileLoaded) {
        const created = await apiFetch<ProfileOut>("/api/v1/profiles/me", {
          method: "POST",
          body: JSON.stringify(profile),
        });
        setProfileLoaded(created);
        setStatus("Profile created ✅");
      } else {
        const updated = await apiFetch<ProfileOut>("/api/v1/profiles/me", {
          method: "PUT",
          body: JSON.stringify(profile),
        });
        setProfileLoaded(updated);
        setStatus("Profile updated ✅");
      }
    } catch (err) {
      setStatus(`Save failed: ${String(err)}`);
    }
  }

  useEffect(() => {
    if (token) loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  // ===== MEAL PLANS (/meal-plans/me...) =====
  async function loadPlanByDate() {
    if (!requireToken()) return;

    setStatus("Loading meal plan...");
    try {
      const d = encodeURIComponent(planDate);
      const data = await apiFetch<MealPlanOut>(`/api/v1/meal-plans/me?date=${d}`);
      setPlan(data);
      setStatus("Meal plan loaded ✅");
    } catch (err) {
      setPlan(null);
      setStatus(`Load plan failed: ${String(err)}`);
    }
  }

  async function generatePlan() {
  if (!requireToken()) return;

  setStatus("Generating plan...");
  try {
    setWeek(null);

    const data = await apiFetch<MealPlanOut>("/api/v1/meal-plans/me/generate", {
      method: "POST",
      body: JSON.stringify({
        plan_date: planDate, // YYYY-MM-DD
      }),
    });

    setPlan(data);
    setStatus("Meal plan generated ✅");
  } catch (err) {
    setStatus(`Generate failed: ${String(err)}`);
  }
}


  async function generateWeek() {
  if (!requireToken()) return;

  setStatus("Generating week plan...");
  try {
    setPlan(null);

    const days = Math.max(1, Math.min(14, Number(weekDays) || 7));

    const data = await apiFetch<WeekPlanOut>("/api/v1/meal-plans/me/generate-week", {
      method: "POST",
      body: JSON.stringify({
        start_date: planDate,      // YYYY-MM-DD
        days,                      // number
        reuse_existing: true,      // ✅ ВАЖНО (иначе 422)
      }),
    });

    setWeek(data);
    setStatus("Week plan generated ✅");
  } catch (err) {
    setWeek(null);
    setStatus(`Generate week failed: ${String(err)}`);
  }
}

  // ===== PRODUCTS =====
  async function loadProducts() {
    setStatus("Loading products...");
    try {
      const data = await apiFetch<ProductOut[]>("/api/v1/products");
      setProducts(data);
      setStatus(`Products loaded ✅ (${data.length})`);
    } catch (err) {
      setStatus(`Load products failed: ${String(err)}`);
    }
  }

  async function seedProducts() {
    setStatus("Seeding products...");
    try {
      const res = await apiFetch<SeedResult>("/api/v1/products/seed", {
        method: "POST",
      });
      setStatus(`Seed done ✅ inserted=${res.inserted}, skipped=${res.skipped}`);
      await loadProducts();
    } catch (err) {
      setStatus(`Seed failed: ${String(err)}`);
    }
  }

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(productQuery.toLowerCase())
  );

  const effectiveUserId =
    profileLoaded?.user_id || plan?.user_id || week?.user_id || userId || "";

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-6">
      <div className="w-full max-w-4xl bg-white rounded-2xl shadow-2xl p-6 space-y-6">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-2xl font-bold">MealMind</h1>
          <div className="text-sm text-gray-700">{status}</div>
        </div>

        {/* AUTH */}
        <div className="rounded-2xl p-5 space-y-3 bg-gray-50">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Auth</h2>
            <div className="flex gap-2">
              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={me}
                disabled={!token}
              >
                Me
              </button>
              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={clearToken}
              >
                Clear token
              </button>
            </div>
          </div>

          {!token ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input
                className="border rounded-xl p-3"
                placeholder="email"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
              />
              <input
                className="border rounded-xl p-3"
                placeholder="password"
                type="password"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
              />
              <div className="flex gap-2">
                <button
                  className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                  onClick={register}
                  disabled={!authEmail || !authPassword}
                >
                  Register
                </button>
                <button
                  className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                  onClick={login}
                  disabled={!authEmail || !authPassword}
                >
                  Login
                </button>
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-600 break-all">
              Token saved ✅ (Authorization header enabled)
              {effectiveUserId ? (
                <div className="mt-2">
                  user_id:{" "}
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {effectiveUserId}
                  </code>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* PROFILE */}
        <div className="rounded-2xl p-5 space-y-4 bg-[rgb(247,93,247)] text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Profile</h2>
            <div className="flex gap-2">
              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={loadProfile}
                disabled={!token}
              >
                Load
              </button>
              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={saveProfile}
                disabled={!token}
              >
                {profileLoaded ? "Update" : "Create"} profile
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <select
              className="border rounded-xl p-3 text-black"
              value={profile.sex}
              onChange={(e) =>
                setProfile((p) => ({ ...p, sex: e.target.value as Sex }))
              }
            >
              <option value="male">male</option>
              <option value="female">female</option>
            </select>

            <input
              className="border rounded-xl p-3 text-black"
              type="number"
              placeholder="age"
              value={profile.age}
              onChange={(e) =>
                setProfile((p) => ({ ...p, age: Number(e.target.value) }))
              }
            />

            <input
              className="border rounded-xl p-3 text-black"
              type="number"
              placeholder="height_cm"
              value={profile.height_cm}
              onChange={(e) =>
                setProfile((p) => ({ ...p, height_cm: Number(e.target.value) }))
              }
            />

            <input
              className="border rounded-xl p-3 text-black"
              type="number"
              placeholder="weight_kg"
              value={profile.weight_kg}
              onChange={(e) =>
                setProfile((p) => ({ ...p, weight_kg: Number(e.target.value) }))
              }
            />

            <select
              className="border rounded-xl p-3 text-black"
              value={profile.goal}
              onChange={(e) =>
                setProfile((p) => ({ ...p, goal: e.target.value as Goal }))
              }
            >
              <option value="lose_fat">lose_fat</option>
              <option value="maintain">maintain</option>
              <option value="gain">gain</option>
            </select>

            <select
              className="border rounded-xl p-3 text-black"
              value={profile.activity_level}
              onChange={(e) =>
                setProfile((p) => ({
                  ...p,
                  activity_level: e.target.value as Activity,
                }))
              }
            >
              <option value="low">low</option>
              <option value="medium">medium</option>
              <option value="high">high</option>
            </select>

            <input
              className="border rounded-xl p-3 md:col-span-3 text-black"
              type="number"
              placeholder="budget_kzt_per_day"
              value={profile.budget_kzt_per_day}
              onChange={(e) =>
                setProfile((p) => ({
                  ...p,
                  budget_kzt_per_day: Number(e.target.value),
                }))
              }
            />
          </div>
        </div>

        {/* PRODUCTS */}
        <div className="rounded-2xl p-5 space-y-4 bg-[rgb(247,93,247)] text-white">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Products</h2>
            <div className="flex gap-2">
              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={seedProducts}
              >
                Seed
              </button>
              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={loadProducts}
              >
                Refresh
              </button>
            </div>
          </div>

          <input
            className="border rounded-xl p-3 text-black w-full"
            placeholder="Search product..."
            value={productQuery}
            onChange={(e) => setProductQuery(e.target.value)}
          />

          <div className="overflow-x-auto rounded-xl bg-white text-black">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2 px-2">Name</th>
                  <th className="py-2 px-2">kcal/100g</th>
                  <th className="py-2 px-2">P</th>
                  <th className="py-2 px-2">F</th>
                  <th className="py-2 px-2">C</th>
                  <th className="py-2 px-2">KZT/100g</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((p) => (
                  <tr key={p.id} className="border-b">
                    <td className="py-2 px-2">{p.name}</td>
                    <td className="py-2 px-2">{p.kcal_per_100g}</td>
                    <td className="py-2 px-2">{p.protein_per_100g}</td>
                    <td className="py-2 px-2">{p.fat_per_100g}</td>
                    <td className="py-2 px-2">{p.carbs_per_100g}</td>
                    <td className="py-2 px-2">{p.price_kzt_per_100g}</td>
                  </tr>
                ))}

                {products.length === 0 && (
                  <tr>
                    <td className="py-3 px-2 text-gray-600" colSpan={6}>
                      No products loaded yet. Click “Seed” or “Refresh”.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* MEAL PLAN */}
        <div className="rounded-2xl p-5 space-y-4 bg-[rgb(247,93,247)] text-white">
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <h2 className="text-lg font-semibold">Meal plan</h2>

            <div className="flex items-center gap-2">
              <input
                className="border rounded-xl p-2 text-black"
                type="date"
                value={planDate}
                onChange={(e) => setPlanDate(e.target.value)}
              />

              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={loadPlanByDate}
                disabled={!token}
              >
                Get
              </button>

              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={generatePlan}
                disabled={!token}
              >
                Generate
              </button>

              <input
                className="border rounded-xl p-2 text-black w-[90px]"
                type="number"
                min={1}
                max={14}
                value={weekDays}
                onChange={(e) => setWeekDays(Number(e.target.value))}
                title="days"
              />

              <button
                className="px-4 py-2 rounded-xl text-white font-semibold bg-[rgb(247,93,247)]"
                onClick={generateWeek}
                disabled={!token}
              >
                Generate week + shopping list
              </button>
            </div>
          </div>

          {plan ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-3 text-sm">
                <div className="bg-white/20 rounded-xl px-3 py-2 text-white">
                  date: <b>{plan.plan_date}</b>
                </div>
                <div className="bg-white/20 rounded-xl px-3 py-2 text-white">
                  target: <b>{plan.target_kcal}</b>
                </div>
                <div className="bg-white/20 rounded-xl px-3 py-2 text-white">
                  total: <b>{plan.total_kcal}</b>
                </div>
                <div className="bg-white/20 rounded-xl px-3 py-2 text-white">
                  cost: <b>{plan.total_cost_kzt} ₸</b>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {plan.items.map((it) => (
                  <div
                    key={`${it.meal_type}-${it.product_id}`}
                    className="rounded-2xl border p-4 bg-white text-black"
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-semibold">{it.name}</div>
                      <span className="text-xs px-2 py-1 rounded-full text-white bg-[rgb(247,93,247)]">
                        {it.meal_type}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {it.grams}g • {it.kcal} kcal • {it.cost_kzt} ₸
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-gray-200 text-sm">No meal plan loaded yet.</div>
          )}

          {week ? (
            <div className="mt-4 space-y-2">
              <div className="text-sm bg-white/20 rounded-xl px-3 py-2">
                Week: <b>{week.start_date}</b> → <b>{week.end_date}</b> | kcal:{" "}
                <b>{week.total_week_kcal}</b> | cost:{" "}
                <b>{week.total_week_cost_kzt} ₸</b>
              </div>

              <div className="rounded-xl bg-white text-black p-3">
                <div className="font-semibold mb-2">Shopping list</div>
                {week.shopping_list?.length ? (
                  <ul className="text-sm list-disc pl-6">
                    {week.shopping_list.map((s) => (
                      <li key={s.product_id}>
                        {s.name} — {s.total_grams}g — {s.total_cost_kzt} ₸
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-sm text-gray-600">No shopping list</div>
                )}
              </div>
            </div>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          {["Auth", "Profile", "Products", "Meal Plan"].map((x) => (
            <div
              key={x}
              className="px-4 py-2 rounded-xl text-white font-semibold"
              style={{ backgroundColor: PINK }}
            >
              {x}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
