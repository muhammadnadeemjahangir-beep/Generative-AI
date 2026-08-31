from chains import run_conditional_chain

review = "The product is terrible. It broke after just one use and the quality is very poor."
result = run_conditional_chain(feedback=review)
print(result)