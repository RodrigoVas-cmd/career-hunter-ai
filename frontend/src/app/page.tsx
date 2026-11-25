import Link from "next/link";
import {
  ArrowRight,
  Building2,
  CheckCircle2,
  FileCheck2,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

const PLANS = [
  {
    name: "Free",
    price: "R$ 0",
    period: "/mês",
    description: "Para organizar seu perfil verificado e testar a plataforma.",
    features: [
      "1 cargo-alvo ativo",
      "2 empresas preferidas",
      "10 análises por mês",
      "Dashboard básico",
      "Registro manual de candidaturas",
    ],
    highlighted: false,
  },
  {
    name: "Pro",
    price: "R$ 49,90",
    period: "/mês",
    description: "Para profissionais em busca ativa com personalização ATS.",
    features: [
      "5 cargos-alvo ativos",
      "20 empresas preferidas",
      "150 análises por mês",
      "30 currículos personalizados para ATS",
      "30 candidaturas preparadas + dashboard completo",
    ],
    highlighted: true,
  },
  {
    name: "Premium",
    price: "R$ 89,90",
    period: "/mês",
    description: "Para liderança, gerência e diretoria com radar estratégico.",
    features: [
      "15 cargos-alvo ativos",
      "100 empresas preferidas",
      "500 análises por mês",
      "100 currículos e 100 candidaturas preparadas",
      "Relatórios estratégicos + maior frequência de monitoramento",
    ],
    highlighted: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-lg text-slate-900">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
              <Sparkles className="h-4 w-4" />
            </span>
            Career Hunter AI
          </div>
          <nav className="flex items-center gap-3">
            <Link
              href="/auth?mode=login"
              className="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900"
            >
              Entrar
            </Link>
            <Link
              href="/auth?mode=register"
              className="px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition"
            >
              Criar conta gratuita
            </Link>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold border border-indigo-100">
            <ShieldCheck className="h-3.5 w-3.5" />
            100% Supervisionado · Fatos Verificados · LGPD
          </span>
          <h1 className="mt-6 text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 max-w-3xl mx-auto">
            Sua central inteligente de recolocação profissional
          </h1>
          <p className="mt-5 text-lg text-slate-600 max-w-2xl mx-auto">
            Para profissionais de analista a diretoria. Importe seu currículo,
            valide seu histórico real, defina cargos-alvo e empresas desejadas
            e conte com agentes de IA que nunca inventam experiências e só
            agem com sua aprovação.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/auth?mode=register"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition shadow-sm"
            >
              Começar gratuitamente
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#planos"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-white border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 transition"
            >
              Ver planos
            </a>
          </div>
        </section>

        {/* Pillars */}
        <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <FileCheck2 className="h-7 w-7 text-indigo-600" />
            <h2 className="mt-4 text-lg font-bold">Perfil Profissional Verificado</h2>
            <p className="mt-2 text-sm text-slate-600">
              Extraímos dados do seu PDF ou DOCX com rastreabilidade de origem e
              sinalização de ambiguidades. Nada entra sem sua validação.
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <Target className="h-7 w-7 text-indigo-600" />
            <h2 className="mt-4 text-lg font-bold">Cargos-Alvo & Aderência Real</h2>
            <p className="mt-2 text-sm text-slate-600">
              Configure cargos, senioridade, sinônimos e critérios obrigatórios.
              Sugestões da IA só entram nas buscas após sua aprovação.
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <Building2 className="h-7 w-7 text-indigo-600" />
            <h2 className="mt-4 text-lg font-bold">Radar de Empresas Preferidas</h2>
            <p className="mt-2 text-sm text-slate-600">
              Cadastre manualmente ou importe por CSV as empresas onde você quer
              trabalhar e acompanhe suas fontes oficiais de carreiras.
            </p>
          </div>
        </section>

        {/* Plans */}
        <section id="planos" className="bg-white border-t border-slate-200 py-16 sm:py-20">
          <div className="max-w-6xl mx-auto px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-3xl font-bold text-slate-900">Planos por assinatura</h2>
              <p className="mt-2 text-slate-600">
                Valores iniciais de referência para validação do MVP. Comece no
                plano gratuito e evolua conforme sua necessidade.
              </p>
            </div>
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              {PLANS.map((plan) => (
                <div
                  key={plan.name}
                  className={`rounded-2xl p-6 flex flex-col border ${
                    plan.highlighted
                      ? "border-indigo-600 ring-2 ring-indigo-600/10 bg-indigo-50/30"
                      : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-slate-900">{plan.name}</h3>
                    {plan.highlighted && (
                      <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-600 text-white">
                        Recomendado
                      </span>
                    )}
                  </div>
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold">{plan.price}</span>
                    <span className="text-sm text-slate-500">{plan.period}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{plan.description}</p>
                  <ul className="mt-6 space-y-2.5 flex-1">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-2 text-sm text-slate-700">
                        <CheckCircle2 className="h-4 w-4 text-indigo-600 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                  <Link
                    href="/auth?mode=register"
                    className={`mt-6 w-full py-2.5 rounded-xl text-center text-sm font-semibold transition ${
                      plan.highlighted
                        ? "bg-indigo-600 text-white hover:bg-indigo-700"
                        : "bg-slate-900 text-white hover:bg-slate-800"
                    }`}
                  >
                    Começar com {plan.name}
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        Career Hunter AI · Recolocação profissional supervisionada, ética e baseada em evidências.
      </footer>
    </div>
  );
}
