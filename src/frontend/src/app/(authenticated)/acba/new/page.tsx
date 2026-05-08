"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AcbaForm } from "@/components/acba/acba-form";
import { apiRequest } from "@/lib/api";
import type { AcbaDetail, AcbaFormPayload } from "@/types/acba";

export default function AcbaNewPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(payload: AcbaFormPayload) {
    setSubmitting(true);
    try {
      const created = await apiRequest<AcbaDetail>("/api/acba/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      router.push(`/acba/${created.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-5">
      <h2 className="text-xl font-semibold text-shell-text">
        Novo auto circunstanciado de busca e arrecadação
      </h2>
      <AcbaForm submitting={submitting} onSubmit={handleSubmit} />
    </div>
  );
}
