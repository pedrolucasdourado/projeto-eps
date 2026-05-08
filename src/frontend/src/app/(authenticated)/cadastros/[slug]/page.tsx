"use client";

import { notFound, useParams } from "next/navigation";

import { GenericCatalogPage } from "@/components/cadastro/GenericCatalogPage";
import { CADASTROS } from "@/config/cadastro-registry";

export default function CadastroSlugPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const cfg = CADASTROS[slug];
  if (!cfg) notFound();
  return <GenericCatalogPage config={cfg} />;
}
