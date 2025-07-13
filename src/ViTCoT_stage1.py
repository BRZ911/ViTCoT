import json
import os
import time
import argparse
import logging
from tqdm import tqdm
from google import genai


# API key pool (maintaining original key sequence)
API_KEYS = []

class GeminiVideoAnalyzer:
    global api_key_index
    def __init__(self):
        self.api_index = 0
        self._init_client()
        self.uploaded_files = {}

    def _init_client(self):
        """Maintain original API key initialization logic"""
        # genai.configure(api_key=API_KEYS[self.api_index])
        self.client = genai.Client(api_key=API_KEYS[self.api_index])

    def _rotate_key(self):
        """Maintain original key rotation mechanism"""
        self.api_index = (self.api_index + 1) % len(API_KEYS)
        self._init_client()
        logging.warning(f"API key rotated to index {self.api_index}")

    def generate_response(self, video_path, prompt, max_retries=10):
        """Maintain original inference logic for Gemini implementation"""
        for _ in range(max_retries):
            try:
                video_file = upload_video(video_path, self.client)
                response = generate_content(video_file, prompt, self.client)
                return response
            except Exception as e:
                logging.error(f"Error: {str(e)}")
                self._rotate_key()
                time.sleep(2)
        return "ERROR: API request failed"

# Your upload_video function
def upload_video(video_path, client):
    video_path = video_path
    # print(f"Uploading video: {video_path}")

    video_file = client.files.upload(file=video_path)

    # Check whether the file is ready to be used.
    while video_file.state.name == "PROCESSING":
        # print('.', end='')
        time.sleep(1)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(video_file.state.name)

    # print(f"Completed upload: {video_file.uri}")
    return video_file

# Your generate_content function
def generate_content(video_file, prompt, client):
    # print("Generating content based on the video...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # Specify model version
        contents=[video_file, prompt]
    )
    print(f"Generated content: {response.text}")
    return response.text

# Modified clean_options method
def clean_options(option):
    cleaned_option = option.split("):", 1)[-1].strip()
    return cleaned_option

def build_prompt(item, with_evidence):
    """Generate prompt according to new logic"""
    task_desc = f"Please finish the {item['task']} task." if 'task' in item else "Please finish the video comprehension task."
    options = item["options"]
    options_prompt = ""
    option_list = ["\n(A) ", "(B) ", "(C) ", "(D) "]
    
    for i, opt in enumerate(options):
        options_prompt += option_list[i] + clean_options(opt) + "\n"
    
    correct_answer = item["correct_answer"]
    evidence = item["evidence"]
    question = item["question"]
    question = item["question"]
    task = item['task']
    
    if with_evidence:
        final_query = f"{task_desc} Question: {question} Your inference evidence is {evidence}. You have the following options: {options_prompt}. Select the answer and only give the option letters."
    else:
        final_query = f"Please finish the {task} task. Question: {question} You have the following options: {options_prompt}. \nDescribe the image information relevant to the question. Do notanswer the choice question directly."
    
    return final_query

def main():
    """Maintain original main program structure"""
    parser = argparse.ArgumentParser(description='ViTCoT Video Reasoning')
    parser.add_argument('-sn',  '--save_path', default='vitcot_stage1.jsonl', help='Result save path')
    parser.add_argument('-we',  '--with_evidence', action='store_true', help='Evidence mode')
    parser.add_argument('-jp',  '--json_path', default='vitcot_data.jsonl',  help='Input file')
    parser.add_argument('--begin_index', type=int, default=0, help='Start processing from this index')
    parser.add_argument('--end_index', type=int, default=None, help='End processing at this index')
    args = parser.parse_args()

    analyzer = GeminiVideoAnalyzer()

    dataset = []
    with open(args.json_path, 'r', encoding='utf-8') as file:
        for line in file:
            dataset.append(json.loads(line)) 

    # Control data processing range
    start_idx = args.begin_index
    end_idx = args.end_index if args.end_index else len(dataset)
    
    # Set total as the size of data to be processed
    total = end_idx - start_idx
    
    # Maintain progress bar display
    for i, item in enumerate(tqdm(dataset[start_idx:end_idx], desc='Video Analysis Progress')):
        try:
            video_path =  item["video_path"]
            final_query = build_prompt(item, args.with_evidence)

            # Execute inference
            response = analyzer.generate_response(video_path, final_query)
            print(response)

            output_item = {
                "id": start_idx + i,  # Ensure output id starts from start_idx
                "video_path": item["video_path"],
                "key_video_path": item["key_video_path"],
                "question": item["question"],
                "options": item["options"],
                "correct_answer": item["correct_answer"],
                "evidence": item.get("evidence",  ""),
                "task": item.get("task",  ""),
                "final_query": final_query,
                "model_output_1": response
            }

            # Immediately append save to jsonl file
            with open(args.save_path, 'a', encoding='utf-8') as f:
                json.dump(output_item, f, ensure_ascii=False)
                f.write("\n")

        except Exception as e:
            logging.error(f"Failed to process item: {str(e)}")
            continue

if __name__ == "__main__":
    main()