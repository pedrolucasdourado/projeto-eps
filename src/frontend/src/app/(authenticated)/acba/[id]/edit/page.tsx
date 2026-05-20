"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AcbaForm } from "@/components/acba/acba-form";
import { useAuth } from "@/contexts/auth-context";
import { apiRequest } from "@/lib/api";
import type { AcbaDetail, AcbaFormPayload } from "@/types/acba";

export default function AcbaEditPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [detail, setDetail] = useState<AcbaDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiRequest<AcbaDetail>(`/api/acba/${params.id}`);
        setDetail(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar.");
      }
    }
    void load();
  }, [params.id]);

  async function handleSubmit(payload: AcbaFormPayload) {
    setSubmitting(true);
    try {
      const updated = await apiRequest<AcbaDetail>(`/api/acba/${params.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      router.push(`/acba/${updated.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  if (error) return <p className="text-red-300">{error}</p>;
  if (!detail) return <p className="text-shell-muted">Carregando...</p>;

  const role = user?.role ?? "agente";
  const bloqueado =
    role === "agente" ||
    (role === "escrivao" && Boolean(detail.pdf_gerado_at));

  if (bloqueado) {
    return (
      <div className="space-y-3">
        <h2 className="text-xl font-semibold text-shell-text">Editar ACBA</h2>
        <p className="rounded border border-amber-700/50 bg-amber-950/30 p-3 text-sm text-amber-200">
          {role === "agente"
            ? "Agentes não podem editar ACBAs."
            : "Este ACBA já teve o PDF gerado e está bloqueado para edição pelo escrivão. Acione o delegado responsável."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <h2 className="text-xl font-semibold text-shell-text">Editar ACBA</h2>
      <AcbaForm
        submitting={submitting}
        initialDetail={detail}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
