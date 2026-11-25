import Link from "next/link";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Clock,
  Sparkles,
  Target,
  X,
} from "lucide-react";
import FaqAccordion, { FaqItem } from "@/components/FaqAccordion";

const PAIN_CARDS = [
  {
    title: "Horas de buscas",
    description:
      "Pesquisar diariamente em diversos sites de emprego e encontrar sempre as mesmas vagas.",
  },
  {
    title: "Currículos sem retorno",
    description:
      "Enviar dezenas de currículos sem saber por que não está sendo chamado para entrevistas.",
  },
  {
    title: "Currículos genéricos",
    description:
      "Utilizar o mesmo currículo para oportunidades que exigem competências diferentes.",
  },
  {
    title: "Formulários intermináveis",
    description:
      "Responder inúmeras perguntas e preencher repetidamente as mesmas informações.",
  },
  {
    title: "Oportunidades perdidas",
    description:
      "Descobrir tarde demais uma vaga que seria ideal para sua carreira.",
  },
  {
    title: "Falta de estratégia",
    description:
      "Candidatar-se a vagas sem saber o quanto seu perfil realmente corresponde aos requisitos.",
  },
];

const FEATURES = [
  {
    title: "Busca automatizada de vagas",
    description:
      "Deixe a inteligência artificial buscar oportunidades compatíveis com seus objetivos profissionais e reduza o tempo gasto em pesquisas manuais.",
    badge: null,
  },
  {
    title: "Principais plataformas de emprego",
    description:
      "Acesse atalhos inteligentes para buscas direcionadas no LinkedIn, Indeed e demais plataformas disponíveis. Encontre oportunidades sem precisar repetir as mesmas pesquisas todos os dias.",
    badge: null,
  },
  {
    title: "Currículos personalizados para cada vaga",
    description:
      "Transforme seu currículo em uma versão estrategicamente direcionada à descrição de cada oportunidade, valorizando suas experiências reais e palavras-chave relevantes para os sistemas ATS.",
    badge: null,
  },
  {
    title: "Respostas inteligentes para candidaturas",
    description:
      "Receba respostas naturais, profissionais e personalizadas para as inúmeras perguntas dos processos seletivos, alinhadas à vaga, à senioridade e à sua experiência.",
    badge: null,
  },
  {
    title: "Análise inteligente de aderência",
    description:
      "Descubra o quanto seu perfil corresponde aos requisitos da vaga, identifique seus diferenciais e direcione seus esforços para oportunidades mais compatíveis.",
    badge: null,
  },
  {
    title: "Radar de empresas dos seus sonhos",
    description:
      "Escolha as empresas onde deseja trabalhar e acompanhe novas oportunidades nos canais de carreira monitorados pela plataforma.",
    badge: null,
  },
  {
    title: "Cartas de apresentação personalizadas",
    description:
      "Demonstre seu interesse pela empresa com uma comunicação profissional, estratégica e direcionada aos desafios da posição.",
    badge: "Em breve",
  },
  {
    title: "Gestão completa das candidaturas",
    description:
      "Organize suas oportunidades, acompanhe seus processos seletivos e tenha uma visão centralizada da sua jornada profissional.",
    badge: null,
  },
  {
    title: "Sua experiência real, valorizada",
    description:
      "Uma inteligência artificial que valoriza suas competências e resultados sem inventar experiências, qualificações ou informações profissionais.",
    badge: null,
  },
];

const TRADITIONAL_CV = [
  "Mesmo conteúdo para todas as vagas",
  "Experiências pouco direcionadas",
  "Palavras-chave genéricas",
  "Sem adaptação à senioridade",
  "Personalização manual",
];

const CAREER_HUNTER_CV = [
  "Personalizado para cada oportunidade",
  "Experiências relevantes em destaque",
  "Palavras-chave contextualizadas",
  "Adequação ao cargo pretendido",
  "Otimização para ATS e recrutadores",
];

const ASSISTANT_BENEFITS = [
  "Respostas naturais e profissionais",
  "Linguagem adequada ao cargo",
  "Alinhamento à descrição da vaga",
  "Baseado em experiências reais",
  "Menos tempo preenchendo formulários",
  "Revisão e aprovação pelo candidato",
];

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Importe seu currículo",
    description:
      "Construa seu perfil profissional a partir da sua trajetória, formação, competências e experiências.",
  },
  {
    step: "2",
    title: "Defina seus objetivos",
    description:
      "Escolha os cargos pretendidos, empresas desejadas e preferências profissionais.",
  },
  {
    step: "3",
    title: "Encontre oportunidades",
    description:
      "Utilize buscas automatizadas, monitoramento de empresas e atalhos inteligentes de pesquisa.",
  },
  {
    step: "4",
    title: "Prepare sua candidatura",
    description:
      "Personalize seu currículo, analise sua aderência e gere respostas estratégicas para os formulários.",
  },
  {
    step: "5",
    title: "Revise e acompanhe",
    description:
      "Mantenha o controle das suas candidaturas e acompanhe a evolução dos processos seletivos.",
  },
];

const PLANS = [
  {
    code: "free",
    name: "Free",
    price: "R$ 0",
    period: "/mês",
    description: "Conheça a plataforma e dê os primeiros passos.",
    features: [
      "1 cargo-alvo ativo",
      "2 empresas preferidas",
      "5 análises por mês",
      "Dashboard básico",
      "Registro manual de candidaturas",
    ],
    cta: "Começar grátis",
    highlighted: false,
  },
  {
    code: "pro",
    name: "Pro",
    price: "R$ 49,90",
    period: "/mês",
    description: "Para quem está buscando ativamente uma nova oportunidade.",
    features: [
      "5 cargos-alvo ativos",
      "20 empresas preferidas",
      "150 análises por mês",
      "30 currículos personalizados",
      "30 candidaturas preparadas",
      "Dashboard completo",
    ],
    cta: "Quero o Pro",
    highlighted: true,
  },
  {
    code: "premium",
    name: "Premium",
    price: "R$ 89,90",
    period: "/mês",
    description: "Para quem deseja potencializar sua estratégia de recolocação.",
    features: [
      "15 cargos-alvo ativos",
      "100 empresas preferidas",
      "500 análises por mês",
      "100 currículos personalizados",
      "100 candidaturas preparadas",
      "Relatórios estratégicos",
      "Monitoramento mais frequente",
    ],
    cta: "Quero o Premium",
    highlighted: false,
  },
];

const FAQ_ITEMS: FaqItem[] = [
  {
    question: "O Career Hunter AI encontra vagas automaticamente?",
    answer:
      "A plataforma auxilia na busca automatizada de oportunidades, no monitoramento de empresas e no acesso a pesquisas direcionadas nos principais canais de emprego disponíveis.",
  },
  {
    question: "Meu currículo será diferente para cada vaga?",
    answer:
      "Sim. A inteligência artificial utiliza sua trajetória profissional e os requisitos da oportunidade para elaborar uma versão personalizada do currículo.",
  },
  {
    question: "O Career Hunter inventa experiências para aumentar minha aderência?",
    answer:
      "Não. A personalização utiliza informações reais do seu perfil profissional, valorizando suas competências e experiências existentes.",
  },
  {
    question: "Preciso responder sozinho aos formulários de candidatura?",
    answer:
      "O assistente de inteligência artificial ajuda a elaborar respostas personalizadas, alinhadas à vaga e ao seu perfil profissional.",
  },
  {
    question: "A plataforma envia candidaturas sem minha autorização?",
    answer:
      "Não. Você mantém o controle sobre a revisão e a aprovação das candidaturas.",
  },
  {
    question: "O Career Hunter garante que vou conseguir um emprego?",
    answer:
      "Não. A plataforma ajuda a melhorar a eficiência das buscas e a qualidade das candidaturas. A decisão de contratação pertence às empresas.",
  },
  {
    question: "Posso utilizar gratuitamente?",
    answer:
      "Sim. O plano Free permite conhecer a plataforma e utilizar os recursos disponíveis dentro dos limites do plano.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#f5f7fa] text-[#10172a]">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2.5 font-bold text-lg text-[#10172a]">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[#5035f5] text-white shrink-0">
              <Sparkles className="h-4 w-4" />
            </span>
            <span>Career Hunter AI</span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <a href="#funcionalidades" className="hover:text-[#10172a]">
              Funcionalidades
            </a>
            <a href="#como-funciona" className="hover:text-[#10172a]">
              Como funciona
            </a>
            <a href="#planos" className="hover:text-[#10172a]">
              Planos
            </a>
            <a href="#faq" className="hover:text-[#10172a]">
              FAQ
            </a>
          </nav>

          <div className="flex items-center gap-2 sm:gap-3">
            <Link
              href="/auth?mode=login"
              className="px-3 sm:px-4 py-2 text-sm font-medium text-slate-700 hover:text-[#10172a]"
            >
              Entrar
            </Link>
            <Link
              href="/auth?mode=register"
              className="px-3.5 sm:px-4 py-2 text-sm font-semibold rounded-lg bg-[#5035f5] text-white hover:bg-indigo-700 transition"
            >
              Criar conta gratuita
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* SEÇÃO 01 — HERO */}
        <section className="bg-white border-b border-slate-200">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-[#5035f5]">
              INTELIGÊNCIA ARTIFICIAL A FAVOR DA SUA CARREIRA
            </p>
            <h1 className="mt-4 text-3xl sm:text-5xl font-extrabold tracking-tight text-[#10172a] max-w-4xl mx-auto leading-tight">
              Procurar emprego não deveria ser um trabalho em tempo integral.
            </h1>
            <p className="mt-5 text-lg sm:text-xl font-semibold text-[#5035f5] max-w-2xl mx-auto">
              Menos tempo procurando. Mais estratégia para conquistar sua próxima oportunidade.
            </p>
            <p className="mt-4 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
              Automatize suas buscas, encontre vagas compatíveis com seu perfil, personalize seu
              currículo para cada oportunidade e receba ajuda para responder aos formulários de
              candidatura. Tudo em uma única plataforma, com inteligência artificial e sob seu
              controle.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href="/auth?mode=register"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-[#5035f5] text-white font-semibold hover:bg-indigo-700 transition shadow-sm"
              >
                Começar minha recolocação gratuitamente
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#planos"
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-white border border-slate-300 text-[#10172a] font-semibold hover:bg-slate-50 transition"
              >
                Ver planos
              </a>
            </div>
            <p className="mt-3 text-xs text-slate-500">Comece gratuitamente · Sem compromisso</p>

            {/* 3 Hero Highlights */}
            <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 border border-slate-200 rounded-2xl bg-white divide-y sm:divide-y-0 sm:divide-x divide-slate-200 text-left">
              <div className="p-5 flex items-center gap-3">
                <Clock className="h-5 w-5 text-[#5035f5] shrink-0" />
                <span className="text-sm font-bold text-[#10172a]">Economize tempo</span>
              </div>
              <div className="p-5 flex items-center gap-3">
                <Target className="h-5 w-5 text-[#5035f5] shrink-0" />
                <span className="text-sm font-bold text-[#10172a]">
                  Candidate-se com estratégia
                </span>
              </div>
              <div className="p-5 flex items-center gap-3">
                <Check className="h-5 w-5 text-[#5035f5] shrink-0" />
                <span className="text-sm font-bold text-[#10172a]">Você mantém o controle</span>
              </div>
            </div>
          </div>
        </section>

        {/* SEÇÃO 02 — IDENTIFICAÇÃO COM A DOR */}
        <section className="py-16 sm:py-20 bg-[#f5f7fa]">
          <div className="max-w-5xl mx-auto px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-4xl font-extrabold text-[#10172a]">
                Quantas horas você já perdeu procurando emprego nesta semana?
              </h2>
              <p className="mt-3 text-sm sm:text-base text-slate-600">
                Se você está buscando uma nova oportunidade profissional, provavelmente já passou por
                alguma dessas situações.
              </p>
            </div>

            <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {PAIN_CARDS.map((card) => (
                <div
                  key={card.title}
                  className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm"
                >
                  <Sparkles className="h-4 w-4 text-[#5035f5]" />
                  <h3 className="mt-3 text-base font-bold text-[#10172a]">{card.title}</h3>
                  <p className="mt-2 text-sm text-slate-600 leading-relaxed">{card.description}</p>
                </div>
              ))}
            </div>

            <div className="mt-10 text-center max-w-2xl mx-auto space-y-2">
              <p className="text-base sm:text-lg font-bold text-[#10172a]">
                Sua energia deveria estar concentrada em conquistar a vaga, não em procurar por ela
                o dia inteiro.
              </p>
              <p className="text-sm text-slate-600">
                O Career Hunter AI foi criado para tornar sua busca profissional mais inteligente,
                organizada e estratégica.
              </p>
            </div>
          </div>
        </section>

        {/* SEÇÃO 03 — FUNCIONALIDADES E BENEFÍCIOS */}
        <section id="funcionalidades" className="py-16 sm:py-20 bg-white border-y border-slate-200">
          <div className="max-w-6xl mx-auto px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-4xl font-extrabold text-[#10172a]">
                Tudo o que você precisa para conquistar sua próxima oportunidade.
              </h2>
              <p className="mt-3 text-sm sm:text-base text-slate-600">
                Da busca pela vaga à preparação da candidatura. Uma única plataforma para toda a sua
                jornada de recolocação.
              </p>
            </div>

            <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {FEATURES.map((feat) => (
                <div
                  key={feat.title}
                  className="bg-[#f5f7fa]/60 p-6 rounded-2xl border border-slate-200 flex flex-col"
                >
                  <div className="flex items-center justify-between gap-2">
                    <Sparkles className="h-4 w-4 text-[#5035f5]" />
                    {feat.badge && (
                      <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-[#5035f5] border border-indigo-200">
                        {feat.badge}
                      </span>
                    )}
                  </div>
                  <h3 className="mt-3 text-base font-bold text-[#10172a]">{feat.title}</h3>
                  <p className="mt-2 text-sm text-slate-600 leading-relaxed">{feat.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SEÇÃO 04 — PERSONALIZAÇÃO CURRICULAR */}
        <section className="py-16 sm:py-20 bg-[#f5f7fa]">
          <div className="max-w-5xl mx-auto px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-4xl font-extrabold text-[#10172a]">
                A vaga mudou. Por que seu currículo continua o mesmo?
              </h2>
              <p className="mt-3 text-sm sm:text-base text-slate-600">
                Cada empresa procura competências diferentes. Enviar o mesmo currículo para todas as
                oportunidades pode fazer com que experiências relevantes passem despercebidas.
              </p>
            </div>

            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-0 rounded-2xl overflow-hidden border border-slate-200 bg-white shadow-sm">
              <div className="p-6 sm:p-8 border-b md:border-b-0 md:border-r border-slate-200">
                <h3 className="text-lg font-bold text-[#10172a]">Currículo tradicional</h3>
                <ul className="mt-5 space-y-3">
                  {TRADITIONAL_CV.map((item) => (
                    <li key={item} className="flex items-center gap-2.5 text-sm text-slate-600">
                      <X className="h-4 w-4 text-slate-400 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-6 sm:p-8 bg-indigo-50/30">
                <h3 className="text-lg font-bold text-[#5035f5]">Currículo Career Hunter</h3>
                <ul className="mt-5 space-y-3">
                  {CAREER_HUNTER_CV.map((item) => (
                    <li
                      key={item}
                      className="flex items-center gap-2.5 text-sm font-medium text-[#10172a]"
                    >
                      <Check className="h-4 w-4 text-[#5035f5] shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mt-8 text-center space-y-5">
              <p className="text-base font-bold text-[#10172a]">
                O mesmo profissional. A mesma trajetória. Uma estratégia diferente para cada
                oportunidade.
              </p>
              <a
                href="#planos"
                className="inline-flex items-center justify-center px-7 py-3.5 rounded-xl bg-[#5035f5] text-white text-sm font-semibold hover:bg-indigo-700 transition shadow-sm"
              >
                Personalizar meu currículo
              </a>
            </div>
          </div>
        </section>

        {/* SEÇÃO 05 — ASSISTENTE INTELIGENTE DE CANDIDATURAS */}
        <section className="py-16 sm:py-20 bg-white border-y border-slate-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-4xl font-extrabold text-[#10172a]">
                Chega de perder tempo respondendo às mesmas perguntas em cada candidatura.
              </h2>
              <p className="mt-3 text-sm sm:text-base text-slate-600">
                O Career Hunter AI interpreta as perguntas dos recrutadores e elabora respostas
                personalizadas, considerando sua trajetória profissional, a descrição da vaga e o
                cargo pretendido.
              </p>
            </div>

            {/* Card demonstrativo Gerente Comercial */}
            <div className="mt-10 rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm space-y-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  PERGUNTA DO RECRUTADOR
                </p>
                <p className="mt-1 text-lg font-bold text-[#10172a]">
                  Por que você tem interesse em trabalhar conosco?
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100">
                <p className="inline-flex items-center gap-1.5 text-xs font-bold text-[#5035f5]">
                  <Sparkles className="h-3.5 w-3.5" />
                  Resposta personalizada pelo Career Hunter AI
                </p>
                <p className="mt-2 text-sm sm:text-base text-slate-700 leading-relaxed">
                  Tenho interesse nesta oportunidade pela possibilidade de contribuir para o
                  crescimento sustentável do negócio, conectando estratégia comercial, inteligência
                  de mercado e desenvolvimento de equipes. Acredito que uma gestão comercial
                  eficiente vai além do cumprimento de metas: exige capacidade de identificar
                  oportunidades, desenvolver relacionamentos duradouros com clientes e transformar
                  crescimento de receita em rentabilidade. É nessa perspectiva que pretendo
                  contribuir para os resultados e a competitividade da empresa.
                </p>
                <p className="mt-4 text-xs text-slate-500">
                  Exemplo ilustrativo de resposta para uma vaga de Gerente Comercial.
                </p>
              </div>
            </div>

            {/* 6 Benefícios */}
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 rounded-2xl border border-slate-200 bg-[#f5f7fa]/50 divide-y sm:divide-y-0 sm:grid-rows-3">
              {ASSISTANT_BENEFITS.map((benefit) => (
                <div
                  key={benefit}
                  className="p-4 flex items-center gap-2.5 border-b border-slate-200/80 last:border-b-0 sm:odd:border-r"
                >
                  <Check className="h-4 w-4 text-[#5035f5] shrink-0" />
                  <span className="text-sm font-medium text-[#10172a]">{benefit}</span>
                </div>
              ))}
            </div>

            <p className="mt-8 text-center text-base font-bold text-[#10172a]">
              Sua experiência. Sua voz. Uma comunicação mais estratégica.
            </p>
          </div>
        </section>

        {/* SEÇÃO 06 — COMO FUNCIONA */}
        <section id="como-funciona" className="py-16 sm:py-20 bg-[#f5f7fa]">
          <div className="max-w-4xl mx-auto px-4 sm:px-6">
            <h2 className="text-2xl sm:text-4xl font-extrabold text-[#10172a] text-center">
              Sua recolocação profissional em cinco passos.
            </h2>

            <div className="mt-10 space-y-3">
              {HOW_IT_WORKS.map((item) => (
                <div
                  key={item.step}
                  className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200 shadow-sm flex items-start gap-4"
                >
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-[#5035f5] font-extrabold text-sm shrink-0">
                    {item.step}
                  </span>
                  <div>
                    <h3 className="text-base font-bold text-[#10172a]">{item.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">{item.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SEÇÃO 07 — PLANOS E ASSINATURAS */}
        <section id="planos" className="py-16 sm:py-20 bg-white border-y border-slate-200">
          <div className="max-w-6xl mx-auto px-4 sm:px-6">
            <div className="text-center max-w-2xl mx-auto">
              <h2 className="text-2xl sm:text-4xl font-extrabold text-[#10172a]">
                Invista na sua próxima oportunidade profissional.
              </h2>
              <p className="mt-3 text-sm sm:text-base text-slate-600">
                Escolha o plano ideal para sua jornada de recolocação e conte com inteligência
                artificial para tornar suas candidaturas mais estratégicas.
              </p>
            </div>

            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              {PLANS.map((plan) => (
                <div
                  key={plan.name}
                  className={`rounded-2xl p-6 sm:p-7 flex flex-col border ${
                    plan.highlighted
                      ? "border-[#5035f5] ring-2 ring-[#5035f5]/15 bg-indigo-50/25 shadow-sm"
                      : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-[#10172a]">{plan.name}</h3>
                    {plan.highlighted && (
                      <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#5035f5] text-white">
                        Recomendado
                      </span>
                    )}
                  </div>
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold text-[#5035f5]">{plan.price}</span>
                    <span className="text-sm text-slate-500">{plan.period}</span>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{plan.description}</p>
                  <ul className="mt-6 space-y-2.5 flex-1">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-2 text-sm text-slate-700">
                        <CheckCircle2 className="h-4 w-4 text-[#5035f5] shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                  <Link
                    href={`/auth?mode=register&plan=${plan.code}`}
                    className={`mt-6 w-full py-2.5 rounded-xl text-center text-sm font-semibold transition ${
                      plan.highlighted
                        ? "bg-[#5035f5] text-white hover:bg-indigo-700"
                        : "bg-[#10172a] text-white hover:bg-slate-800"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SEÇÃO 08 — PERGUNTAS FREQUENTES */}
        <section id="faq" className="py-16 sm:py-20 bg-[#f5f7fa]">
          <div className="max-w-3xl mx-auto px-4 sm:px-6">
            <h2 className="text-2xl sm:text-4xl font-extrabold text-[#10172a] text-center mb-10">
              Perguntas frequentes
            </h2>
            <FaqAccordion items={FAQ_ITEMS} />
          </div>
        </section>

        {/* SEÇÃO 09 — CHAMADA FINAL PARA AÇÃO */}
        <section className="py-16 sm:py-20 bg-white border-t border-slate-200">
          <div className="max-w-4xl mx-auto px-4 sm:px-6">
            <div className="rounded-3xl bg-[#10172a] text-white px-6 py-12 sm:px-12 sm:py-16 text-center shadow-lg">
              <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#5035f5]/20 text-[#8b7cff] mx-auto">
                <Sparkles className="h-5 w-5" />
              </div>
              <h2 className="mt-5 text-2xl sm:text-4xl font-extrabold max-w-2xl mx-auto leading-tight">
                Sua próxima oportunidade começa com uma estratégia melhor.
              </h2>
              <p className="mt-4 text-sm sm:text-base text-slate-300 max-w-xl mx-auto leading-relaxed">
                Você já construiu sua experiência profissional. Agora conte com a tecnologia para
                encontrar oportunidades e apresentar todo o seu potencial aos recrutadores.
              </p>
              <div className="mt-8">
                <Link
                  href="/auth?mode=register"
                  className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-[#5035f5] text-white font-semibold hover:bg-indigo-600 transition shadow-sm"
                >
                  Começar minha recolocação gratuitamente
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
              <p className="mt-5 text-xs text-slate-400">
                Sua carreira. Sua estratégia. Seu próximo passo.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* SEÇÃO 10 — RODAPÉ */}
      <footer className="border-t border-slate-200 bg-white py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-[#5035f5] text-white">
              <Sparkles className="h-3.5 w-3.5" />
            </span>
            <span className="font-semibold text-[#10172a]">
              Career Hunter AI — Sua carreira. Nossa inteligência.
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <a href="#funcionalidades" className="hover:text-[#10172a]">
              Funcionalidades
            </a>
            <a href="#planos" className="hover:text-[#10172a]">
              Planos
            </a>
            <a href="#faq" className="hover:text-[#10172a]">
              Perguntas frequentes
            </a>
            <Link href="/auth?mode=login" className="hover:text-[#10172a]">
              Entrar
            </Link>
            <Link href="/auth?mode=register" className="hover:text-[#10172a]">
              Criar conta
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
