"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useAuthStore } from "@/store/auth-store";

import {
  Home,
  Bot,
  Calendar,
  BarChart3,
  Settings,
  HelpCircle,
  ChevronDown,
  LogOut,
  MessageSquare,
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const {
    logout,
    user,
    fetchCurrentUser,
  } = useAuthStore();

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const displayName =
    user?.full_name ||
    user?.username ||
    "User";

  const displayEmail =
    user?.email || "Logged In";

  return (
    <aside
      className="
        w-[260px]
        h-screen
        bg-white
        border-r
        border-[#F1F1F5]
        flex
        flex-col
        justify-between
      "
    >
      {/* Top Section */}
      <div>
        {/* Logo */}
        <div className="px-10 pt-8 pb-12">
          <div className="relative inline-block">
            <h1 className="text-5xl font-black tracking-tight text-black">
              AGIX
            </h1>

            <div
              className="
                absolute
                -top-2
                right-2
                text-violet-500
                text-xl
              "
            >
              ✦
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="px-4 space-y-3">
          <SidebarItem
            icon={<Home size={20} />}
            label="Dashboard"
            href="/dashboard"
            active={pathname === "/dashboard"}
          />

          <SidebarItem
            icon={<Bot size={20} />}
            label="AI Companions"
            href="/companions"
            active={pathname === "/companions"}
          />

          <SidebarItem
            icon={<MessageSquare size={20} />}
            label="Conversations"
            href="/conversations"
            active={
              pathname === "/conversations" ||
              pathname.startsWith("/chat")
            }
          />

          <SidebarItem
            icon={<Calendar size={20} />}
            label="Calendar"
            href="/calendar"
            active={pathname === "/calendar"}
          />

          <SidebarItem
            icon={<BarChart3 size={20} />}
            label="Analytics"
            href="/analytics"
            active={pathname === "/analytics"}
          />

          <SidebarItem
            icon={<Settings size={20} />}
            label="Settings"
            href="/settings"
            active={pathname === "/settings"}
          />

          <SidebarItem
            icon={<HelpCircle size={20} />}
            label="Help & Support"
            href="/help"
            active={pathname === "/help"}
          />
        </nav>
      </div>

      {/* Bottom Section */}
      <div className="border-t border-[#F1F1F5] p-4">
        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="
            w-full
            mb-4
            flex
            items-center
            justify-center
            gap-2
            px-4
            py-3
            rounded-xl
            bg-red-50
            text-red-600
            hover:bg-red-100
            transition
          "
        >
          <LogOut size={18} />
          Logout
        </button>

        {/* User Section */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img
              src={user?.profile_image_url || "/avatar.png"}
              alt="user"
              className="
                w-12
                h-12
                rounded-full
                object-cover
              "
            />

            <div className="min-w-0">
              <h3
                className="
                  text-sm
                  font-semibold
                  text-slate-800
                  truncate
                "
              >
                {displayName}
              </h3>

              <p
                className="
                  text-xs
                  text-slate-500
                  truncate
                  max-w-[140px]
                "
              >
                {displayEmail}
              </p>
            </div>
          </div>

          <ChevronDown
            size={18}
            className="text-slate-400"
          />
        </div>
      </div>
    </aside>
  );
}

interface ItemProps {
  icon: React.ReactNode;
  label: string;
  href: string;
  active?: boolean;
}

function SidebarItem({
  icon,
  label,
  href,
  active,
}: ItemProps) {
  return (
    <Link
      href={href}
      className={`
        w-full
        flex
        items-center
        gap-4
        px-4
        py-4
        rounded-2xl
        transition-all
        ${
          active
            ? "bg-violet-50 text-violet-600 font-semibold"
            : "text-slate-500 hover:bg-slate-50"
        }
      `}
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
}