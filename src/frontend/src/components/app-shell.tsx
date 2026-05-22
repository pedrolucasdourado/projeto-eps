"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { CADASTROS } from "@/config/cadastro-registry";
import { useAuth, type UserRole } from "@/contexts/auth-context";

type NavItem = { href: string; label: string };

const cadastroSlugOrder = [
  "unidades",
  "delegacias",
  "cidades",
  "ufs",
  "delegados",
  "escrivaos",
  "agentes",
  "processos",
  "tipos-procedimento",
  "tipos-material",
] as const satisfies readonly (keyof typeof CADASTROS)[];

const cadastroLinks = [
  ...cadastroSlugOrder.map((slug) => ({
    slug,
    href: `/cadastros/${slug}`,
    label: CADASTROS[slug].title,
  })),
  { slug: "equipes", href: "/cadastros/equipes", label: "Equipes operacionais" },
];

/**
 * Itens da navegação principal por papel. ACBA fica disponível para todo
 * usuário operacional; administrador só vê "Usuários" e "Cadastros" — sem
 * acesso ao módulo ACBA, como definido na regra de negócio.
 */
function navItemsForRole(role: UserRole): NavItem[] {
  if (role === "administrador") {
    return [
      { href: "/dashboard", label: "Início" },
      { href: "/usuarios", label: "Usuários" },
    ];
  }
  return [
    { href: "/dashboard", label: "Início" },
    { href: "/acba", label: "ACBA" },
  ];
}

/**
 * Quais cadastros aparecem para cada papel.
 *
 * Administrador vê todos (e pode mutar).
 * Delegado vê todos também, mas os cadastros de pessoas (delegados,
 * escrivãos, agentes) entram em modo somente-leitura — a restrição
 * fica na ``GenericCatalogPage`` via ``adminOnlyMutations``, e o
 * backend também devolve 403 em POST/PUT/DELETE nessas rotas.
 * Escrivão e agente não chegam a ver a seção "Cadastros" (a sidebar
 * já esconde — ver ``showCadastros`` abaixo).
 */
function visibleCadastros(_role: UserRole) {
  return cadastroLinks;
}

function roleLabel(role: UserRole): string {
  return {
    administrador: "Administrador",
    delegado: "Delegado",
    escrivao: "Escrivão",
    agente: "Agente",
  }[role];
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const role: UserRole = user?.role ?? "administrador";
  const navPrimary = navItemsForRole(role);
  const showCadastros = role === "administrador" || role === "delegado";
  const cadastrosVisiveis = visibleCadastros(role);

  return (
    <div className="flex min-h-screen bg-shell-bg">
      <aside className="flex w-72 flex-col border-r border-shell-border bg-shell-sidebar text-shell-text shadow-2xl">
        <div className="flex items-center gap-3 border-b border-shell-border px-6 py-6">
          <Image
            src="/logo.png"
            alt="Assistente de Apreensão Inteligente"
            width={44}
            height={44}
            className="rounded-md"
            priority
          />
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-shell-accent">
              AAI
            </p>
            <p className="truncate text-sm font-semibold leading-tight text-shell-text">
              Apreensão Inteligente
            </p>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-4 overflow-y-auto p-4">
          <div className="flex flex-col gap-1">
            {navPrimary.map((item) => {
              const active =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-lg border px-3 py-2.5 text-sm font-medium transition-colors ${
                    active
                      ? "border-shell-accent/50 bg-shell-accent/20 text-shell-accent"
                      : "border-transparent text-shell-text hover:border-shell-border hover:bg-shell-sidebarHover"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
          {showCadastros ? (
            <div>
              <p className="mb-2 px-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-shell-muted">
                Cadastros auxiliares
              </p>
              <div className="flex flex-col gap-1">
                {cadastrosVisiveis.map(({ href, label }) => {
                  const active =
                    pathname === href || pathname.startsWith(`${href}/`);
                  return (
                    <Link
                      key={href}
                      href={href}
                      className={`rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                        active
                          ? "border-shell-accent/40 bg-shell-accent/15 text-shell-accent"
                          : "border-transparent text-shell-muted hover:border-shell-border hover:bg-shell-sidebarHover hover:text-shell-text"
                      }`}
                    >
                      {label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ) : null}
        </nav>
        <div className="border-t border-shell-border p-4 text-xs text-shell-muted">
          Sistema Operacional PCDF
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-shell-border bg-shell-surface px-8">
          <h1 className="text-sm font-semibold uppercase tracking-[0.12em] text-shell-muted">
            Ambiente de Operações
          </h1>
          <div className="flex items-center gap-4">
            <div className="hidden text-right sm:block">
              <p className="text-sm text-shell-text">
                {user?.full_name ?? user?.email}
              </p>
              <p className="text-[10px] uppercase tracking-[0.14em] text-shell-muted">
                {roleLabel(role)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => logout()}
              className="rounded-md border border-shell-border bg-shell-bg px-3 py-1.5 text-sm font-medium text-shell-text transition hover:border-shell-accent hover:text-shell-accent"
            >
              Sair
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-auto bg-shell-bg p-8">{children}</main>
      </div>
    </div>
  );
}
