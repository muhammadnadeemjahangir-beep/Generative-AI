import gradio as gr

from chains import (
    run_basic_chain,
    run_conditional_chain,
    run_parallel_chain,
    run_sequential_chain,
)


with gr.Blocks(title="LangChain + Groq + Gradio Chains") as demo:
    gr.Markdown(
        """
        # LangChain + Groq + Gradio Chain Workflows

        This app demonstrates four LangChain chain types using Groq:
        Basic Chain, Sequential Chain, Parallel Chain, and Conditional Chain.
        """
    )

    with gr.Tab("1. Basic Chain"):
        gr.Markdown("### Animal Facts Generator")
        basic_animal = gr.Textbox(label="Animal", value="Dog")
        basic_count = gr.Slider(label="Number of facts", minimum=1, maximum=10, value=2, step=1)
        basic_button = gr.Button("Generate Facts")
        basic_output = gr.Textbox(label="Output", lines=10)
        basic_button.click(
            fn=run_basic_chain,
            inputs=[basic_animal, basic_count],
            outputs=basic_output,
        )

    with gr.Tab("2. Sequential Chain"):
        gr.Markdown("### Facts then Translation")
        seq_animal = gr.Textbox(label="Animal", value="Lion")
        seq_count = gr.Slider(label="Number of facts", minimum=1, maximum=10, value=2, step=1)
        seq_language = gr.Textbox(label="Translate to language", value="French")
        seq_button = gr.Button("Run Sequential Chain")
        seq_output = gr.Textbox(label="Output", lines=12)
        seq_button.click(
            fn=run_sequential_chain,
            inputs=[seq_animal, seq_count, seq_language],
            outputs=seq_output,
        )

    with gr.Tab("3. Parallel Chain"):
        gr.Markdown("### Movie Summary + Plot Analysis + Character Analysis")
        movie_name = gr.Textbox(label="Movie name", value="Spiderman")
        parallel_button = gr.Button("Run Parallel Chain")
        parallel_output = gr.Textbox(label="Output", lines=18)
        parallel_button.click(
            fn=run_parallel_chain,
            inputs=movie_name,
            outputs=parallel_output,
        )

    with gr.Tab("4. Conditional Chain"):
        gr.Markdown("### Feedback Classifier and Response Generator")
        feedback = gr.Textbox(
            label="Customer feedback",
            value="The product is terrible. It broke after just one use and the quality is very poor.",
            lines=5,
        )
        conditional_button = gr.Button("Classify and Respond")
        conditional_output = gr.Textbox(label="Output", lines=12)
        conditional_button.click(
            fn=run_conditional_chain,
            inputs=feedback,
            outputs=conditional_output,
        )


if __name__ == "__main__":
    demo.launch()