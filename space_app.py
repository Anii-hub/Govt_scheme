import os
import gradio as gr
from app.rag.search import search_schemes
from app.rag.answer_generator import generate_answer, translate_query_for_search
from app.main import app as fastapi_app


def perform_search(query: str, language: str):
    if not query or not query.strip():
        return (
            "<p style='color: #e53e3e;'>⚠️ Please enter a search query.</p>",
            "",
            "",
            gr.update(visible=False),
        )

    try:
        lang = language.lower()
        search_query = translate_query_for_search(query.strip(), lang)
        search_output = search_schemes(query=search_query, final_k=5)

        results = search_output["results"]
        parsed = search_output["parsed"]

        answer = generate_answer(query.strip(), results, language=lang)

        # Build parsed profile tag badges
        profile_tags = []
        if parsed.get("state"):
            profile_tags.append(f"📍 State: <b>{parsed['state']}</b>")
        if parsed.get("category"):
            profile_tags.append(f"📂 Category: <b>{parsed['category']}</b>")
        if parsed.get("age"):
            profile_tags.append(f"👤 Age: <b>{parsed['age']}</b>")
        if parsed.get("gender"):
            profile_tags.append(f"⚧ Gender: <b>{parsed['gender']}</b>")
        if parsed.get("income"):
            profile_tags.append(f"💰 Income: <b>{parsed['income']}</b>")

        parsed_html = (
            "<div style='margin-bottom: 15px; padding: 10px; background: #f0f4f8; border-radius: 8px; font-size: 0.95rem;'>"
            + " | ".join(profile_tags)
            + "</div>"
            if profile_tags
            else ""
        )

        summary_md = f"### 📌 Summary\n{answer.get('summary', '')}\n\n*Note: {answer.get('important_note', '')}*"

        schemes = answer.get("schemes", [])
        if not schemes:
            return (
                parsed_html,
                summary_md,
                "### No matching schemes found.\nTry broadening your query with state, age, or category details.",
                gr.update(visible=True),
            )

        schemes_md = []
        for i, s in enumerate(schemes, 1):
            name = s.get("scheme_name", "Unknown Scheme")
            state = s.get("state", "Central / All India") or "Central / All India"
            cat = s.get("category", "General")
            rel = s.get("relevance", "")

            benefits = "\n".join([f"- {b}" for b in s.get("benefits", [])]) or "Not specified"
            eligibility = "\n".join([f"- {e}" for e in s.get("eligibility", [])]) or "Not specified"
            process = "\n".join([f"- {p}" for p in s.get("application_process", [])]) or "Not specified"
            docs = "\n".join([f"- {d}" for d in s.get("documents_required", [])]) or "Not specified"

            urls = []
            if s.get("official_url"):
                urls.append(f"[Official Portal]({s['official_url']})")
            if s.get("apply_url"):
                urls.append(f"[Apply Online]({s['apply_url']})")
            links_md = " | ".join(urls) if urls else "Check official government portal"

            card = f"""
---
### 🏛️ {i}. {name}
- **State**: {state} | **Category**: {cat}
- **Why Relevant**: {rel}

#### 🎁 Benefits
{benefits}

#### 📋 Eligibility
{eligibility}

#### 📝 Application Process
{process}

#### 📄 Documents Required
{docs}

🔗 **Official Links**: {links_md}
"""
            schemes_md.append(card)

        return parsed_html, summary_md, "\n".join(schemes_md), gr.update(visible=True)

    except Exception as e:
        return (
            "",
            f"❌ **Error occurred**: {str(e)}",
            "Please ensure GROQ_API_KEY is configured in Space Secrets.",
            gr.update(visible=True),
        )


with gr.Blocks(title="Govt Scheme Search AI") as demo:
    gr.Markdown(
        """
        # 🏛️ Indian Government Schemes AI Assistant (YojnaSearch)
        ### Discover Central & State government schemes in English and Hindi powered by RAG and Groq AI.
        """
    )

    with gr.Row():
        with gr.Column(scale=4):
            query_input = gr.Textbox(
                label="Enter your query / अपना प्रश्न दर्ज करें",
                placeholder="e.g. Financial assistance for small farmers in Uttar Pradesh / महिलाओं के लिए स्वरोजगार ऋण योजना",
                lines=2,
            )
        with gr.Column(scale=1):
            lang_radio = gr.Radio(
                choices=["english", "hindi"],
                value="english",
                label="Response Language / भाषा",
            )
            search_btn = gr.Button("🔍 Search Schemes", variant="primary")

    gr.Examples(
        examples=[
            ["Financial assistance for small farmers in Maharashtra", "english"],
            ["Scholarship schemes for girl students in higher education", "english"],
            ["उत्तर प्रदेश में महिलाओं के लिए स्वरोजगार योजनाएं", "hindi"],
            ["Loans and subsidies for starting a new business for SC/ST", "english"],
            ["वृद्धावस्था पेंशन योजना की पात्रता और आवेदन प्रक्रिया", "hindi"],
        ],
        inputs=[query_input, lang_radio],
    )

    with gr.Column(visible=False) as output_container:
        profile_output = gr.HTML()
        summary_output = gr.Markdown()
        schemes_output = gr.Markdown()

    search_btn.click(
        fn=perform_search,
        inputs=[query_input, lang_radio],
        outputs=[profile_output, summary_output, schemes_output, output_container],
    )
    query_input.submit(
        fn=perform_search,
        inputs=[query_input, lang_radio],
        outputs=[profile_output, summary_output, schemes_output, output_container],
    )

# Mount FastAPI app so all REST API endpoints (/api/search, /health, /docs) are also active
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    # Spaces reserves port 7860 for the Python application.  Gradio 6's SSR
    # proxy otherwise tries to bind the same port and the Space is stopped.
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        theme=gr.themes.Soft(),
        ssr_mode=False,
    )
