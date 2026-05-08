"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AcbaForm } from "@/components/acba/acba-form";
import { apiRequest } from "@/lib/api";
import type { AcbaDetail, AcbaFormPayload } from "@/types/acba";

export default function AcbaEditPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
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
