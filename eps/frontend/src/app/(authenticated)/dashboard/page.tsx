export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-6xl">
      <h2 className="text-2xl font-semibold tracking-tight text-shell-text">
        Centro de Controle Operacional
      </h2>
      <p className="mt-2 text-shell-muted">
        Gestão centralizada de autos e diligências em ambiente seguro.
      </p>
      <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5">
          <p className="text-xs uppercase tracking-[0.12em] text-shell-muted">
            Status
          </p>
          <p className="mt-2 text-lg font-semibold text-shell-text">Em operação</p>
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5">
          <p className="text-xs uppercase tracking-[0.12em] text-shell-muted">
            Módulo ativo
          </p>
          <p className="mt-2 text-lg font-semibold text-shell-text">
            Auto Circunstanciado
          </p>
        </div>
        <div className="rounded-xl border border-shell-border bg-shell-surface p-5">
          <p className="text-xs uppercase tracking-[0.12em] text-shell-muted">
            Segurança
          </p>
          <p className="mt-2 text-lg font-semibold text-shell-text">
            Autenticação validada
          </p>
        </div>
      </div>
    </div>
  );
}
