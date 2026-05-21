import React, { FormEvent, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type SearchResult = {
  id: string;
  result_type: string;
  section_number?: string;
  label: string;
  permalink?: string;
  semantic_score?: number;
  match_type?: string;
};

type SearchPayload = {
  query: string;
  count: number;
  results: SearchResult[];
  semantic_search?: {
    enabled: boolean;
    embedding_provider: string | null;
    pgvector_runtime?: string;
    ranked_document_count: number;
  };
  empty_state?: { message: string; fix: string } | null;
};

type AnswerPayload = {
  status: string;
  answer?: string;
  matched_section_number?: string;
  llm_provider?: string;
  llm_model?: string;
  ai_review_required?: boolean;
  ai_authority?: string;
  llm_error?: { message: string; fix: string };
  citations?: Array<{ citation_text: string; canonical_url?: string }>;
  message?: string;
  fix?: string;
};

const initialExamples = ["13.40.020", "roosters", "large livestock"];

function App() {
  const [query, setQuery] = useState("13.40.020");
  const [sectionNumber, setSectionNumber] = useState("");
  const [searchState, setSearchState] = useState<"idle" | "loading" | "success" | "empty" | "error">("idle");
  const [answerState, setAnswerState] = useState<"idle" | "loading" | "success" | "error" | "partial">("idle");
  const [searchPayload, setSearchPayload] = useState<SearchPayload | null>(null);
  const [answerPayload, setAnswerPayload] = useState<AnswerPayload | null>(null);
  const [error, setError] = useState("");

  const selectedSection = useMemo(() => {
    if (sectionNumber.trim()) return sectionNumber.trim();
    return searchPayload?.results.find((result) => result.section_number)?.section_number ?? "";
  }, [sectionNumber, searchPayload]);

  async function runSearch(nextQuery = query) {
    const normalized = nextQuery.trim();
    setQuery(nextQuery);
    setError("");
    setSearchPayload(null);
    if (!normalized) {
      setSearchState("error");
      setError("Enter a section number or plain-language term before searching.");
      return;
    }
    setSearchState("loading");
    try {
      const response = await fetch(`/api/v1/civiccode/search?q=${encodeURIComponent(normalized)}`);
      const payload = (await response.json()) as SearchPayload;
      if (!response.ok) throw new Error(payload.empty_state?.message ?? "Search failed.");
      setSearchPayload(payload);
      setSearchState(payload.count === 0 ? "empty" : "success");
    } catch (caught) {
      setSearchState("error");
      setError(caught instanceof Error ? caught.message : "Search failed.");
    }
  }

  async function runAnswer(event?: FormEvent) {
    event?.preventDefault();
    const normalized = query.trim();
    setAnswerPayload(null);
    if (!normalized) {
      setAnswerState("error");
      setError("Ask a question before requesting a cited answer.");
      return;
    }
    setAnswerState("loading");
    try {
      const response = await fetch("/api/v1/civiccode/questions/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: normalized,
          section_number: selectedSection || undefined
        })
      });
      const payload = (await response.json()) as AnswerPayload;
      setAnswerPayload(payload);
      if (!response.ok || payload.status !== "ok") {
        setAnswerState("error");
        return;
      }
      setAnswerState(payload.llm_error ? "partial" : "success");
    } catch (caught) {
      setAnswerState("error");
      setError(caught instanceof Error ? caught.message : "Answer failed.");
    }
  }

  return (
    <>
    <a className="skip-link" href="#content">Skip to content</a>
    <main id="content" className="shell">
      <section className="mast">
        <div>
          <p className="eyebrow">CivicCode</p>
          <h1>Read municipal code with cited, staff-reviewable answers.</h1>
        </div>
        <div className="status-strip" aria-label="Runtime evidence">
          <span>Live API</span>
          <span>Configured retrieval shown in results</span>
          <span>Staff review required for AI answers</span>
        </div>
      </section>

      <section className="workspace" aria-label="CivicCode lookup workspace">
        <form className="query-panel" onSubmit={runAnswer}>
          <label htmlFor="query">Question or section</label>
          <div className="query-row">
            <input
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by topic, phrase, or section number"
            />
            <button type="button" onClick={() => runSearch()}>
              Search
            </button>
            <button type="submit">Answer</button>
          </div>
          <label htmlFor="section">Pinned section</label>
          <input
            id="section"
            value={sectionNumber}
            onChange={(event) => setSectionNumber(event.target.value)}
            placeholder="Optional exact section number"
          />
          <div className="examples" aria-label="Example searches">
            {initialExamples.map((example) => (
              <button key={example} type="button" onClick={() => runSearch(example)}>
                {example}
              </button>
            ))}
          </div>
        </form>

        <section className="results-panel" aria-live="polite">
          <PanelState title="Search" state={searchState} error={error} />
          {searchPayload?.empty_state ? (
            <div className="notice">
              <strong>{searchPayload.empty_state.message}</strong>
              <span>{searchPayload.empty_state.fix}</span>
            </div>
          ) : null}
          <div className="result-list">
            {searchPayload?.results.map((result) => (
              <button
                className="result-card"
                type="button"
                key={`${result.result_type}-${result.id}`}
                onClick={() => setSectionNumber(result.section_number ?? "")}
              >
                <span>{result.label}</span>
                <small>
                  {result.match_type === "semantic" ? "semantic" : result.result_type}
                  {typeof result.semantic_score === "number" ? ` · ${result.semantic_score}` : ""}
                </small>
              </button>
            ))}
          </div>
          {searchPayload?.semantic_search ? (
            searchPayload.semantic_search.enabled ? (
              <p className="footnote">
                {searchPayload.semantic_search.embedding_provider} ranked{" "}
                {searchPayload.semantic_search.ranked_document_count} adopted code records via{" "}
                {searchPayload.semantic_search.pgvector_runtime ?? "configured vector search"}.
              </p>
            ) : (
              <p className="footnote">
                Semantic retrieval is not configured for this runtime; results use exact text and approved related-material matches.
              </p>
            )
          ) : null}
        </section>

        <section className="answer-panel" aria-live="polite">
          <PanelState title="Answer" state={answerState} error={answerPayload?.message ?? error} />
          {answerPayload?.answer ? <p className="answer">{answerPayload.answer}</p> : null}
          {answerPayload?.llm_error ? (
            <div className="notice warning">
              <strong>{answerPayload.llm_error.message}</strong>
              <span>{answerPayload.llm_error.fix}</span>
            </div>
          ) : null}
          {answerPayload?.citations?.map((citation) => (
            <div className="citation" key={citation.citation_text}>
              <span>{citation.citation_text}</span>
            </div>
          ))}
          {answerPayload ? (
            <dl className="meta-grid">
              <div>
                <dt>Provider</dt>
                <dd>{answerPayload.llm_provider ?? "n/a"}</dd>
              </div>
              <div>
                <dt>Review</dt>
                <dd>{answerPayload.ai_review_required ? "staff required" : "deterministic extract"}</dd>
              </div>
              <div>
                <dt>Section</dt>
                <dd>{answerPayload.matched_section_number ?? "unresolved"}</dd>
              </div>
            </dl>
          ) : null}
        </section>
      </section>
    </main>
    </>
  );
}

function PanelState({ title, state, error }: { title: string; state: string; error?: string }) {
  return (
    <header className="panel-header">
      <h2>{title}</h2>
      <span data-state={state}>{state}</span>
      {state === "loading" ? <div className="meter" aria-label={`${title} loading`} /> : null}
      {state === "error" && error ? <p>{error}</p> : null}
    </header>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
