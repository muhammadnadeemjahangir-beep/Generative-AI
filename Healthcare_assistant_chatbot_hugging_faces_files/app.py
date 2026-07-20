"""
AI Personal Healthcare Assistant Chatbot
-----------------------------------------
A compact, professional pop-up style AI health assistant built with
Gradio + LangChain + Groq.

This assistant offers general health information and guidance
(symptom explanations in plain language, medicine info lookups,
nutrition tips, first-aid basics, and mental-health support pointers).
It is NOT a substitute for professional medical advice, diagnosis, or
treatment, and always encourages the user to consult a qualified
healthcare provider for anything serious or urgent.

--------------------------------------------------------------------------
RUNNING THIS ON HUGGING FACE SPACES
--------------------------------------------------------------------------
1. This file, requirements.txt, and README.md should sit at the root of
   the Space repo.

2. In the Space's Settings -> "Repository secrets", add a secret named
   GROQ_API_KEY with your Groq API key. Spaces injects secrets as
   environment variables automatically, so no code changes are needed
   between environments.

3. Push/commit the files (or use the Spaces web upload UI) -- the Space
   will build the requirements.txt environment and run this file
   automatically. No `share=True` or Colab-only setup is required here.
--------------------------------------------------------------------------
"""

import os
import gradio as gr
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ----------------------------------------------------------------------------
# 1. Model setup
# ----------------------------------------------------------------------------

# On Spaces, GROQ_API_KEY comes from a Repository secret (Settings ->
# Repository secrets), which Spaces exposes as a normal env var at
# runtime. ChatGroq() also reads GROQ_API_KEY from the environment on
# its own, but we check it explicitly first so a missing key produces a
# clear message in the Space's build/runtime logs instead of a confusing
# stack trace from deep inside the client library.
if not os.environ.get("GROQ_API_KEY"):
    raise RuntimeError(
        "GROQ_API_KEY is not set. Add it in this Space's Settings -> "
        "Repository secrets, then restart the Space."
    )

chat_model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3,
)

HEALTH_SYSTEM_PROMPT = """You are "Vita", a friendly and knowledgeable AI Health
Assistant. You provide clear, general health information to help people
understand symptoms, medicines, nutrition, and everyday wellbeing.

For every message, respond as a calm, supportive, non-alarmist assistant and,
where relevant, weave in the following:

1. SYMPTOM INFORMATION
   - If the user describes symptoms, explain in plain language what general
     categories of causes are commonly associated with them.
   - Never provide a definitive diagnosis. Always frame possibilities as
     "this could be related to..." rather than "you have...".
   - Flag red-flag / emergency symptoms clearly (e.g. chest pain, difficulty
     breathing, signs of stroke, severe bleeding, suicidal thoughts) and tell
     the user to seek emergency care or call local emergency services
     immediately if these are present.

2. MEDICINE INFORMATION
   - Explain what a medicine is generally used for, in plain language.
   - Do NOT give specific dosing instructions, prescribing advice, or
     recommend combining/adjusting medications. Direct the user to a
     pharmacist or doctor for dosage and suitability questions.

3. NUTRITION & LIFESTYLE
   - Offer general, evidence-based nutrition and lifestyle tips (hydration,
     balanced meals, sleep, exercise) relevant to the user's question.

4. FIRST-AID BASICS
   - For minor, non-emergency situations (small cuts, mild burns, etc.),
     give basic, widely-accepted first-aid steps.
   - For anything potentially serious, prioritize telling the user to seek
     in-person medical or emergency care over giving self-care steps.

5. MENTAL HEALTH SUPPORT
   - Respond with warmth and validation to mental health concerns.
   - Encourage professional support (therapist, doctor, counselor) and,
     if the user expresses thoughts of self-harm or suicide, gently but
     clearly encourage them to reach out to a crisis line or emergency
     services right away, in addition to anything else you say.

Formatting rules:
   - Use short, clearly labeled sections only when they add value (don't
     force every category into every reply — be natural and concise).
   - Keep responses focused, calm, and free of unnecessary filler.
   - Use markdown (bold, bullet points) for readability.
   - Always sound professional, warm, and reassuring — like a knowledgeable
     friend, not a cold clinical script.

ALWAYS include, at the end of any message containing health guidance (skip
this for simple small talk), a short one-line reminder such as: "This is
general information, not a medical diagnosis — please check with a doctor
for anything urgent or persistent."

IMPORTANT — casual messages:
   - If the user's message is simple small talk (e.g. "Hi", "Hello",
     "Thanks", "Good morning", "Bye"), just reply warmly and naturally.
   - Do NOT add health disclaimers, symptom checklists, or unrelated
     medical commentary to a plain greeting.
   - Only bring in symptom/medicine/nutrition/mental-health guidance when
     the message actually raises a health topic, or the user asks for it.
"""

# ----------------------------------------------------------------------------
# 2. Chat function
# ----------------------------------------------------------------------------

def chat(message, history):
    messages = [SystemMessage(content=HEALTH_SYSTEM_PROMPT)]

    # Gradio message format:
    # [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    for msg in history:
        role = msg.get("role")
        content = msg.get("content")

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=message))

    response = chat_model.invoke(messages)

    return response.content


# ----------------------------------------------------------------------------
# 3. Professional, compact "pop-up widget" styling
# ----------------------------------------------------------------------------

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@600;700&display=swap');

/* ==========================================================================
   DESIGN TOKENS — "Vitals" system
   A calm clinical palette (sage mist + deep pine) with one warm accent
   ("pulse" amber) reserved for the single signature moment: the heartbeat
   line and the send control. Everything else stays quiet on purpose.
   -------------------------------------------------------------------------
   Type: Quicksand (rounded, warm — headings/voice) + Inter (body, legible)
   + JetBrains Mono (small-caps utility labels, like a monitor readout).
   ========================================================================== */
.gradio-container {
    --vt-mist:   #E9F1EC;   /* page background — pale sage mist   */
    --vt-paper:  #FFFFFF;   /* bubble / card surface               */
    --vt-pine:   #163C33;   /* deep pine — primary, user bubble    */
    --vt-sea:    #4C8C7D;   /* mid teal — secondary accents        */
    --vt-border: #CFE3DB;   /* soft sage border on bot bubbles     */
    --vt-pulse:  #E8935C;   /* warm amber — the one accent, used sparingly */
    --vt-ink:    #16241F;   /* body text                           */
    --vt-mute:   #6B8079;   /* muted labels / captions             */

    max-width: 400px !important;
    width: 100% !important;
    box-sizing: border-box !important;
    margin: 16px auto !important;
    border-radius: 20px !important;
    box-shadow: 0 16px 46px rgba(16, 44, 38, 0.16) !important;
    border: 1px solid var(--vt-border) !important;
    overflow: hidden !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
    background: var(--vt-mist) !important;
}
* { box-sizing: border-box !important; }

/* Header bar */
#health-header {
    background: var(--vt-pine);
    color: #ffffff !important;
    padding: 12px 16px 10px 16px !important;
    border-radius: 0 !important;
}
#health-eyebrow {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    font-family: 'JetBrains Mono', ui-monospace, monospace !important;
    font-size: 9px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #9fd8c4 !important;
    margin: 0 0 4px 0 !important;
}
#health-eyebrow .dot {
    width: 6px !important;
    height: 6px !important;
    border-radius: 50% !important;
    background: var(--vt-pulse) !important;
    box-shadow: 0 0 0 0 rgba(232, 147, 92, 0.6) !important;
    animation: vt-ping 1.8s ease-out infinite !important;
    flex: 0 0 auto !important;
}
@keyframes vt-ping {
    0%   { box-shadow: 0 0 0 0 rgba(232, 147, 92, 0.55); }
    70%  { box-shadow: 0 0 0 6px rgba(232, 147, 92, 0); }
    100% { box-shadow: 0 0 0 0 rgba(232, 147, 92, 0); }
}
#health-header h1 {
    font-family: 'Quicksand', 'Inter', sans-serif !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    margin: 0 !important;
    color: #ffffff !important;
    letter-spacing: 0.01em !important;
}
#health-header p {
    font-size: 10.5px !important;
    margin: 4px 0 0 0 !important;
    color: #cfe9de !important;
    opacity: 0.95;
}

@media (prefers-reduced-motion: reduce) {
    #health-eyebrow .dot { animation: none !important; }
}

/* Example question chips — styled as small mono "vitals" tags */
#health-examples {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 6px !important;
    padding: 8px 12px 8px 12px !important;
    background: var(--vt-mist) !important;
    border-bottom: 1px solid var(--vt-border) !important;
}
#health-examples button {
    flex: 0 1 auto !important;
    width: auto !important;
    min-width: unset !important;
    height: auto !important;
    font-family: 'JetBrains Mono', ui-monospace, monospace !important;
    font-size: 9.5px !important;
    letter-spacing: 0.01em !important;
    line-height: 1.35 !important;
    padding: 6px 12px !important;
    border-radius: 999px !important;
    background: var(--vt-paper) !important;
    color: var(--vt-pine) !important;
    border: 1px solid var(--vt-border) !important;
    white-space: normal !important;
    text-align: left !important;
    box-shadow: 0 1px 2px rgba(16, 44, 38, 0.05) !important;
    transition: background 0.15s ease, border-color 0.15s ease !important;
}
#health-examples button:hover {
    background: var(--vt-sea) !important;
    color: #ffffff !important;
    border-color: var(--vt-sea) !important;
}

/* Chat window */
#health-chat {
    height: 260px !important;
    overflow-y: auto !important;
    background: #F4F0E9 !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 8px 8px !important;
    font-size: 12px !important;
}

/* Hide any placeholder avatar icons -- avatar_images=(None, None) should
   suppress these, but some Gradio versions still render a generic
   fallback icon/box. Hiding it also removes the extra vertical space
   that was pushing the reply text into a cramped, scrollable box. */
#health-chat [class*="avatar"] {
    display: none !important;
}

/* Safety net: some Gradio versions insert a normally-invisible cursor
   or selection-marker element inside each message (used for streaming
   "typing" indicators or copy/selection anchoring). If our styling
   above ever makes one visible again, this hides it outright. */
#health-chat [class*="cursor"],
#health-chat [class*="caret"] {
    display: none !important;
}

/* --------------------------------------------------------------------
   IMESSAGE-STYLE BUBBLES
   Simple, solid, high-contrast bubbles — no tails, no outline tricks.
   The row is forced to full width so the bubble's percentage max-width
   is computed against the *whole chat column*, not a row that has
   shrunk to fit its own content — that mismatch was what made bubbles
   wrap after only a few characters instead of using the space available.
   -------------------------------------------------------------------- */
#health-chat .message-row,
#health-chat [class*="message-wrap"] {
    max-width: 100% !important;
    width: 100% !important;
    display: flex !important;
    padding: 0 !important;
    margin: 0 !important;
    gap: 0 !important;
    min-height: 0 !important;
}
#health-chat .message,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) {
    box-sizing: border-box !important;
    border-radius: 14px !important;
    max-width: 92% !important;
    width: max-content !important;
    min-width: 0 !important;
    flex: 0 0 auto !important;
    padding: 6px 10px !important;
    line-height: 1.3 !important;
    font-size: 11px !important;
    white-space: normal !important;
    overflow-wrap: break-word !important;
    word-break: normal !important;
    margin: 2px 8px 4px 8px !important;
    border: none !important;
    box-shadow: none !important;
}

/* Belt-and-braces: stop any element *inside* a bubble (Gradio's own
   markdown/"prose" wrapper, code blocks, etc.) from imposing a width
   narrower than the bubble itself. Without this, the inner wrapper's
   own default width can force the bubble to shrink to fit it, which is
   the other half of why text was wrapping early. */
#health-chat .message *,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) * {
    max-width: 100% !important;
}
#health-chat .message > div,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) > div {
    padding: 0 !important;
    margin: 0 !important;
}

/* Only target real text-carrying elements -- NOT a blanket "*" selector.
   Also zero out default paragraph/list margins, which is what was
   creating extra empty space inside each bubble. */
#health-chat .message p,
#health-chat .message li,
#health-chat .message a,
#health-chat .message code,
#health-chat .message pre,
#health-chat .message em,
#health-chat .message strong,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) p,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) li,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) a,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) code,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) pre,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) em,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) strong {
    font-size: 11px !important;
    margin: 0 !important;
    padding: 0 !important;
}
#health-chat .message p + p,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) p + p {
    margin-top: 4px !important;
}
#health-chat .message ul,
#health-chat .message ol,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) ul,
#health-chat [class*="bubble"]:not([class*="bubble-wrap"]) ol {
    margin: 2px 0 0 0 !important;
    padding-left: 14px !important;
}

/* User bubble: solid iMessage green, white text, right-aligned */
#health-chat [class*="user"]:not([class*="avatar"]) {
    background: #34C759 !important;
    color: #ffffff !important;
    border-bottom-right-radius: 5px !important;
    margin-left: auto !important;
}
#health-chat [class*="user"]:not([class*="avatar"]) p,
#health-chat [class*="user"]:not([class*="avatar"]) li,
#health-chat [class*="user"]:not([class*="avatar"]) a,
#health-chat [class*="user"]:not([class*="avatar"]) code,
#health-chat [class*="user"]:not([class*="avatar"]) strong,
#health-chat [class*="user"]:not([class*="avatar"]) em {
    color: #ffffff !important;
}

/* Bot bubble: solid iMessage gray, dark readable text, left-aligned */
#health-chat [class*="bot"]:not([class*="avatar"]),
#health-chat [class*="assistant"]:not([class*="avatar"]) {
    background: #E9E9EB !important;
    color: #1C1C1E !important;
    border-bottom-left-radius: 5px !important;
    margin-right: auto !important;
}
#health-chat [class*="bot"]:not([class*="avatar"]) p,
#health-chat [class*="bot"]:not([class*="avatar"]) li,
#health-chat [class*="bot"]:not([class*="avatar"]) a,
#health-chat [class*="bot"]:not([class*="avatar"]) code,
#health-chat [class*="assistant"]:not([class*="avatar"]) p,
#health-chat [class*="assistant"]:not([class*="avatar"]) li,
#health-chat [class*="assistant"]:not([class*="avatar"]) a,
#health-chat [class*="assistant"]:not([class*="avatar"]) code {
    color: #1C1C1E !important;
}
#health-chat [class*="bot"]:not([class*="avatar"]) strong,
#health-chat [class*="assistant"]:not([class*="avatar"]) strong {
    color: #163C33 !important;
}

/* --------------------------------------------------------------------
   INPUT PILL
   Textbox + send button rendered as one rounded pill with the arrow
   tucked inside the right edge, instead of two separate elements.
   `:has()` finds the wrapper that Gradio generates around the
   textbox + submit button and re-styles it as a single pill; the
   textbox itself becomes transparent/borderless so only the outer
   pill shows a border. If your installed Gradio version wraps these
   in a different element, inspect it in devtools and swap the
   `:has(#health-textbox)` selector below to match.
   -------------------------------------------------------------------- */
.gradio-container form:has(#health-textbox),
.gradio-container div.input-row:has(#health-textbox) {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    background: #F0F0F0 !important;
    border: 1px solid #E2E2E2 !important;
    border-radius: 999px !important;
    padding: 4px 6px 4px 14px !important;
    margin: 8px 12px 12px 12px !important;
}
#health-textbox {
    flex: 1 1 auto !important;
    min-width: 0 !important;
}
#health-textbox textarea,
#health-textbox input {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 6px 0 !important;
    font-size: 12px !important;
    color: var(--vt-ink) !important;
}
#health-textbox textarea:focus,
#health-textbox input:focus {
    border: none !important;
    box-shadow: none !important;
}

/* Small round "send" arrow button, styled like iMessage's up-arrow,
   sitting flush inside the right edge of the pill. */
.gradio-container button.primary,
.gradio-container button[variant="primary"] {
    border-radius: 50% !important;
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
    flex: 0 0 auto !important;
    padding: 0 !important;
    margin: 0 !important;
    background: #34C759 !important;
    color: #ffffff !important;
    font-size: 13px !important;
    line-height: 1 !important;
    box-shadow: none !important;
    transition: transform 0.15s ease !important;
}
.gradio-container button.primary:hover,
.gradio-container button[variant="primary"]:hover {
    transform: scale(1.06) !important;
}

/* Footer credit */
#health-footer {
    text-align: center !important;
    font-family: 'JetBrains Mono', ui-monospace, monospace !important;
    font-size: 9px !important;
    letter-spacing: 0.02em !important;
    color: var(--vt-mute) !important;
    padding: 9px 10px 13px 10px !important;
    border-top: 1px solid var(--vt-border) !important;
    background: var(--vt-mist) !important;
}
#health-footer b {
    color: var(--vt-pine) !important;
}

footer { display: none !important; } /* hide default Gradio footer */
"""

THEME = gr.themes.Soft(
    primary_hue="emerald",
    secondary_hue="slate",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
)

# ----------------------------------------------------------------------------
# 4. Build the compact widget-style app
# ----------------------------------------------------------------------------

EXAMPLE_PROMPTS = [
    "🤒  I have a headache and mild fever, what could it be?",
    "💊  What is paracetamol generally used for?",
    "🥗  Give me some tips for a balanced daily diet.",
    "🩹  How do I treat a small kitchen burn at home?",
]

with gr.Blocks(title="AI Health Assistant") as demo:

    with gr.Column(elem_id="health-header"):
        gr.HTML(
            "<div id='health-eyebrow'><span class='dot'></span>VITALS · ONLINE</div>"
        )
        gr.Markdown(
            "# 🩺 AI Health Assistant\n"
            "🤒 Symptoms &nbsp;•&nbsp; 💊 Medicines &nbsp;•&nbsp; "
            "🥗 Nutrition &nbsp;•&nbsp; 🧠 Mental Health"
        )

    # Small pill-shaped example question chips, shown at the top.
    with gr.Row(elem_id="health-examples"):
        example_buttons = [
            gr.Button(prompt, size="sm", variant="secondary")
            for prompt in EXAMPLE_PROMPTS
        ]

    health_textbox = gr.Textbox(
        elem_id="health-textbox",
        placeholder="💬 ask your question ...",
        show_label=False,
        container=False,
    )

    # Note: intentionally NOT passing bubble_full_width= here -- that
    # argument was removed in Gradio 6 and will raise a TypeError
    # ("unexpected keyword argument 'bubble_full_width'") on this version.
    # The remaining kwargs are applied defensively: if any one of them
    # isn't supported by your installed Gradio build, it's dropped and
    # construction is retried rather than crashing the app.
    chatbot_kwargs = dict(
        elem_id="health-chat",
        type="messages",
        height=260,
        show_label=False,
        avatar_images=(None, None),
        show_copy_button=True,
        show_share_button=True,
    )
    while True:
        try:
            health_chatbot = gr.Chatbot(**chatbot_kwargs)
            break
        except TypeError as e:
            bad_kwarg = str(e).split("argument '")[-1].rstrip("'")
            if bad_kwarg in chatbot_kwargs:
                print(f"Note: dropping unsupported Chatbot argument '{bad_kwarg}' for this Gradio version.")
                chatbot_kwargs.pop(bad_kwarg)
            else:
                raise

    gr.ChatInterface(
        fn=chat,
        chatbot=health_chatbot,
        textbox=health_textbox,
        submit_btn="↑",
    )

    # Clicking a chip fills the textbox with that example question
    # (the leading icon is stripped so it isn't sent as part of the message).
    for btn, prompt in zip(example_buttons, EXAMPLE_PROMPTS):
        clean_prompt = prompt.split(" ", 1)[1].strip() if " " in prompt else prompt
        btn.click(fn=(lambda p=clean_prompt: p), outputs=health_textbox)

    gr.HTML(
        "<div id='health-footer'>&copy; 2026 <b>AI HEALTH ASSISTANT</b> — "
        "GENERAL INFO ONLY · NOT A DIAGNOSIS</div>"
    )

# ----------------------------------------------------------------------------
# 5. Launch
#    Spaces builds and runs this file itself and exposes it publicly, so no
#    share= tunnel or debug loop is needed here (those were Colab-only).
#    pwa=True still enables an "Install App" option in supporting browsers.
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    launch_kwargs = dict(
        pwa=True,
        css=CUSTOM_CSS,
        theme=THEME,
    )
    try:
        # Gradio 6.x: css, theme, and pwa are all valid launch() kwargs.
        demo.launch(**launch_kwargs)
    except TypeError as e:
        # Older Gradio: some of these aren't accepted by launch().
        # Drop whichever kwargs aren't supported and retry.
        print(f"Note: adjusting launch() arguments for this Gradio version ({e}).")
        for bad_kwarg in ("css", "theme", "pwa"):
            launch_kwargs.pop(bad_kwarg, None)
            try:
                demo.launch(**launch_kwargs)
                break
            except TypeError:
                continue
