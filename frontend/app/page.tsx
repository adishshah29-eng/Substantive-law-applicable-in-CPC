import Link from "next/link";
import { CheckCircle2, ScrollText, ShieldCheck } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <div className="bg-background text-foreground">
      {/* Hero */}
      <section className="border-b border-border">
        <div className="mx-auto max-w-5xl px-6 py-20 sm:py-28">
          <div className="mb-6 inline-flex items-center gap-2 rounded-sm border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary">
            <ShieldCheck className="h-3.5 w-3.5" />
            Civil litigation verification engine
          </div>

          <h1 className="max-w-3xl font-serif text-4xl font-medium leading-[1.1] tracking-tight text-foreground sm:text-5xl md:text-6xl">
            AI drafts. VERITAS verifies.
            <br />
            <span className="text-primary">The lawyer decides.</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
            The only Indian-law verification engine that reads AI-generated legal
            drafts and tells you what&rsquo;s real, what&rsquo;s overstated, and
            what&rsquo;s fabricated.
          </p>

          <div className="mt-10">
            <Link
              href="/verify"
              className={cn(
                buttonVariants({ size: "lg" }),
                "h-12 bg-accent px-8 text-base font-semibold text-accent-foreground hover:bg-accent/90"
              )}
            >
              Verify a document
            </Link>
          </div>
        </div>
      </section>

      {/* Proof */}
      <section className="border-b border-border bg-card">
        <div className="mx-auto max-w-5xl px-6 py-14">
          <div className="grid grid-cols-1 gap-10 sm:grid-cols-3">
            <Stat
              value="Up to 33%"
              label="Hallucination rate"
              detail="Leading legal AI research tools, per Stanford RegLab"
            />
            <Stat
              value="1,000+"
              label="Fabricated citations catalogued"
              detail="Court cases worldwide, and growing weekly"
            />
            <Stat
              value="First"
              label="CPC procedural coverage"
              detail="Injunctions, pleadings, written statements, res judicata"
            />
          </div>
        </div>
      </section>

      {/* Solution overview */}
      <section className="mx-auto max-w-5xl px-6 py-20">
        <h2 className="font-serif text-2xl font-medium text-foreground sm:text-3xl">
          One verdict per claim, traced to its source
        </h2>
        <p className="mt-3 max-w-2xl text-muted-foreground">
          Upload a memo, plaint, or written statement. VERITAS classifies every
          proposition, checks it against Indian statute and case law, and tells
          you exactly what to fix before it goes anywhere near a partner.
        </p>

        <div className="mt-12 grid grid-cols-1 gap-x-10 gap-y-10 sm:grid-cols-3">
          <Feature
            icon={ScrollText}
            title="Every claim classified"
            body="Substantive propositions, CPC procedure, citations, and statutory references are separated automatically, so nothing gets verified against the wrong standard."
          />
          <Feature
            icon={ShieldCheck}
            title="Sources, not opinions"
            body="Verdicts reason only from the statute and judgment text retrieved for that claim. If the sources are silent, VERITAS says so instead of guessing."
          />
          <Feature
            icon={CheckCircle2}
            title="Nothing hidden"
            body="Every flag links to the exact statutory provision or judgment excerpt it's based on, quoted verbatim, so you can check the work in seconds."
          />
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border bg-primary">
        <div className="mx-auto max-w-5xl px-6 py-14 text-center">
          <h2 className="font-serif text-2xl font-medium text-primary-foreground sm:text-3xl">
            Upload once. Get a verdict on every claim.
          </h2>
          <div className="mt-8">
            <Link
              href="/verify"
              className={cn(
                buttonVariants({ size: "lg" }),
                "h-12 bg-accent px-8 text-base font-semibold text-accent-foreground hover:bg-accent/90"
              )}
            >
              Verify a document
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function Stat({ value, label, detail }: { value: string; label: string; detail: string }) {
  return (
    <div>
      <div className="font-serif text-3xl font-medium text-primary">{value}</div>
      <div className="mt-1 text-sm font-semibold text-foreground">{label}</div>
      <div className="mt-1 text-sm text-muted-foreground">{detail}</div>
    </div>
  );
}

function Feature({
  icon: Icon,
  title,
  body,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  body: string;
}) {
  return (
    <div>
      <Icon className="h-6 w-6 text-accent" />
      <h3 className="mt-4 font-semibold text-foreground">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{body}</p>
    </div>
  );
}
