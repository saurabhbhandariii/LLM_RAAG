from llm_guard import scan_prompt, scan_output
from llm_guard.input_scanners import PromptInjection, Toxicity, Secrets, Anonymize
from llm_guard.output_scanners import Toxicity as OutputToxicity, Deanonymize

input_scanners = [
    PromptInjection(),
    Toxicity(),
    Secrets(),
    Anonymize(),
]

output_scanners = [
    OutputToxicity(),
]

sanitized_prompt, results_valid, results_score = scan_prompt(input_scanners, "user will ask ques in streamlit ?")
print(sanitized_prompt, results_valid)
