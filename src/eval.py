import json
import re
from prettytable import PrettyTable

# Load JSONL file
file_path = "/Volumes/Video/video/vitcot_stage2.jsonl"

data = []
with open(file_path, 'r', encoding='utf-8') as file:
    for line in file:
        if line.strip():  # Skip empty lines
            data.append(json.loads(line))

# Function to normalize answers
def normalize_answer(answer):
    # Remove parentheses and spaces
    return answer.strip().replace("(", "").replace(")", "")

# Function to extract answer from model_output
def extract_answer(model_output):
    # Remove all line breaks
    model_output = model_output.replace('\n', '')
    
    # Directly match "Answer: X" format
    match = re.search(r"Answer:\s*([A-Z])", model_output)
    if match:
        return match.group(1)
    return None

# Calculate accuracy for each task
def calculate_accuracy_by_task(data):
    task_stats = {}
    for item in data:
        task = item.get("task", "Unknown Task")
        if task not in task_stats:
            task_stats[task] = {"correct": 0, "total": 0}
        
        correct_answer = normalize_answer(item.get("correct_answer", ""))
        model_output = item.get("model_output", "")
        
        extracted_answer = extract_answer(model_output)
        if extracted_answer and correct_answer == extracted_answer:
            task_stats[task]["correct"] += 1
        
        task_stats[task]["total"] += 1
    return task_stats

# Calculate accuracy
task_stats = calculate_accuracy_by_task(data)

# Create PrettyTable table
table = PrettyTable()
table.field_names = ["Task", "Correct", "Total", "Acc."]

total_correct = 0
total_total = 0

for task, stats in task_stats.items():
    accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
    table.add_row([task, stats["correct"], stats["total"], f"{accuracy*100:.1f}"])
    total_correct += stats["correct"]
    total_total += stats["total"]

# Calculate overall weighted average accuracy
average_accuracy_weighted = total_correct / total_total if total_total > 0 else 0

# Calculate unweighted average accuracy
sum_accuracy = 0
num_tasks = len(task_stats)
for stats in task_stats.values():
    task_accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
    sum_accuracy += task_accuracy
average_accuracy_unweighted = sum_accuracy / num_tasks if num_tasks > 0 else 0

# Add weighted and unweighted averages to the table
# table.add_row(["Weighted Mean", total_correct, total_total, f"{average_accuracy_weighted*100:.1f}"])
table.add_row(["Average", "-", "-", f"{average_accuracy_unweighted*100:.1f}"])

print(table)
