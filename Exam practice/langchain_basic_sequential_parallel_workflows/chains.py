"""
LangChain LCEL examples converted from Google Gemini to Groq.

Original examples:
- chain_basics.py
- chain_sequential.py
- chain_parallel.py
- chain_conditional.py

This file keeps the same teaching idea but uses:
- langchain-groq
- ChatGroq
- GROQ_API_KEY from .env
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_groq import ChatGroq

load_dotenv()


def get_model(temperature: float = 0.0) -> ChatGroq:
    """Create a Groq chat model using values from .env."""
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError(
            "GROQ_API_KEY is missing. Create a .env file and add your Groq API key."
        )

    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    return ChatGroq(model=model_name, temperature=temperature)


# ---------------------------------------------------------------------
# 1. Basic Chain
# ---------------------------------------------------------------------
def run_basic_chain(animal: str = "elephant", fact_count: int = 1) -> str:
    """Basic LCEL chain: prompt -> Groq model -> string output."""
    model = get_model()

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a facts expert who knows facts about {animal}."),
            ("human", "Tell me {fact_count} facts."),
        ]
    )

    chain = prompt_template | model | StrOutputParser()
    return chain.invoke({"animal": animal, "fact_count": fact_count})


# ---------------------------------------------------------------------
# 2. Sequential Chain
# ---------------------------------------------------------------------
def run_sequential_chain(
    animal: str = "cat",
    count: int = 2,
    language: str = "French",
) -> str:
    """
    Sequential LCEL chain:
    animal facts -> prepare text for translation -> translation prompt -> Groq model
    """
    model = get_model()

    animal_facts_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You like telling facts and you tell facts about {animal}."),
            ("human", "Tell me {count} facts."),
        ]
    )

    translation_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a translator and convert the provided text into {language}.",
            ),
            ("human", "Translate the following text to {language}: {text}"),
        ]
    )

    prepare_for_translation = RunnableLambda(
        lambda output: {"text": output, "language": language}
    )

    chain = (
        animal_facts_template
        | model
        | StrOutputParser()
        | prepare_for_translation
        | translation_template
        | model
        | StrOutputParser()
    )

    return chain.invoke({"animal": animal, "count": count})


# ---------------------------------------------------------------------
# 3. Parallel Chain
# ---------------------------------------------------------------------
def run_parallel_chain(movie_name: str = "Inception") -> str:
    """
    Parallel chain:
    1. Generate movie summary
    2. Send summary to two branches at the same time:
       - plot analysis
       - character analysis
    3. Combine both outputs
    """
    model = get_model()

    summary_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a movie critic."),
            ("human", "Provide a brief summary of the movie {movie_name}."),
        ]
    )

    plot_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a movie critic."),
            (
                "human",
                "Analyze the plot from this movie summary:\n\n{summary}\n\n"
                "Mention strengths and weaknesses.",
            ),
        ]
    )

    character_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a movie critic."),
            (
                "human",
                "Analyze the characters from this movie summary:\n\n{summary}\n\n"
                "Mention strengths and weaknesses.",
            ),
        ]
    )

    summary_chain = summary_template | model | StrOutputParser()

    parallel_chain = RunnableParallel(
        plot=plot_template | model | StrOutputParser(),
        characters=character_template | model | StrOutputParser(),
    )

    summary = summary_chain.invoke({"movie_name": movie_name})
    analyses = parallel_chain.invoke({"summary": summary})

    return (
        f"Movie Summary:\n{summary}\n\n"
        f"Plot Analysis:\n{analyses['plot']}\n\n"
        f"Character Analysis:\n{analyses['characters']}"
    )


# ---------------------------------------------------------------------
# 4. Conditional Chain
# ---------------------------------------------------------------------
def run_conditional_chain(feedback: str) -> str:
    """
    Conditional chain:
    1. Classify feedback sentiment
    2. Route the feedback to the correct response chain
    """
    model = get_model()

    classification_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            (
                "human",
                "Classify the sentiment of this feedback as exactly one word: "
                "positive, negative, neutral, or escalate.\n\nFeedback: {feedback}",
            ),
        ]
    )

    positive_feedback_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            (
                "human",
                "Generate a thank-you note for this positive feedback:\n{feedback}",
            ),
        ]
    )

    negative_feedback_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            (
                "human",
                "Generate a professional response addressing this negative feedback:\n{feedback}",
            ),
        ]
    )

    neutral_feedback_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            (
                "human",
                "Generate a request for more details for this neutral feedback:\n{feedback}",
            ),
        ]
    )

    escalate_feedback_template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant."),
            (
                "human",
                "Generate a message to escalate this feedback to a human agent:\n{feedback}",
            ),
        ]
    )

    classification_chain = classification_template | model | StrOutputParser()

    response_branches = RunnableLambda(
        lambda data: _route_feedback_response(
            data=data,
            positive_chain=positive_feedback_template | model | StrOutputParser(),
            negative_chain=negative_feedback_template | model | StrOutputParser(),
            neutral_chain=neutral_feedback_template | model | StrOutputParser(),
            escalate_chain=escalate_feedback_template | model | StrOutputParser(),
        )
    )

    chain = RunnablePassthrough.assign(classification=classification_chain) | response_branches
    return chain.invoke({"feedback": feedback})


def _route_feedback_response(
    data: dict,
    positive_chain,
    negative_chain,
    neutral_chain,
    escalate_chain,
) -> str:
    """Route feedback based on classification result."""
    classification = str(data["classification"]).strip().lower()
    feedback = data["feedback"]

    if "positive" in classification:
        response = positive_chain.invoke({"feedback": feedback})
        label = "positive"
    elif "negative" in classification:
        response = negative_chain.invoke({"feedback": feedback})
        label = "negative"
    elif "neutral" in classification:
        response = neutral_chain.invoke({"feedback": feedback})
        label = "neutral"
    else:
        response = escalate_chain.invoke({"feedback": feedback})
        label = "escalate"

    return f"Classification: {label}\n\nResponse:\n{response}"
