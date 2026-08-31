from chains import (
    run_basic_chain,
    run_conditional_chain,
    run_parallel_chain,
    run_sequential_chain,
)



def main() -> None:
    print("\n==============================")
    print("LangChain + Groq Chain Examples")
    print("==============================\n")

    print("1. Basic Chain\n")
    print(run_basic_chain(animal="elephant", fact_count=1))

    print("\n------------------------------")
    print("2. Sequential Chain\n")
    print(run_sequential_chain(animal="cat", count=2, language="French"))

    print("\n------------------------------")
    print("3. Parallel Chain\n")
    print(run_parallel_chain(movie_name="Inception"))

    print("\n------------------------------")
    print("4. Conditional Chain\n")
    feedback = "The product is terrible. It broke after just one use and the quality is very poor."
    print(run_conditional_chain(feedback=feedback))


if __name__ == "__main__":
    main()
