import torch
import os
from transformers import AutoProcessor, AutoModelForVision2Seq
from qwen_vl_utils import process_vision_info, fetch_image

# Percorso del modello locale
model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'NuExtract-2.0-2B')

# Carica il modello locale invece di scaricarlo da Hugging Face
processor = AutoProcessor.from_pretrained(model_path, 
                                          trust_remote_code=True, 
                                          padding_side='left',
                                          use_fast=True)
model = AutoModelForVision2Seq.from_pretrained(model_path, 
                                               trust_remote_code=True, 
                                               torch_dtype=torch.bfloat16,
                                               device_map="auto")



def construct_messages(document, template, examples=None, image_placeholder="<|vision_start|><|image_pad|><|vision_end|>"):
    """
    Construct the individual NuExtract message texts, prior to chat template formatting.
    """
    images = []
    # add few-shot examples if needed
    if examples is not None and len(examples) > 0:
        icl = "# Examples:\n"
        for row in examples:
            example_input = row['input']
            
            if not isinstance(row['input'], str):
                example_input = image_placeholder
                images.append(row['input'])
                
            icl += f"## Input:\n{example_input}\n## Output:\n{row['output']}\n"
    else:
        icl = ""
        
    # if input document is an image, set text to an image placeholder
    text = document
    if not isinstance(document, str):
        text = image_placeholder
        images.append(document)
    text = f"""# Template:\n{template}\n{icl}# Context:\n{text}"""
    
    messages = [
        {
            "role": "system",
            "content": "You are NuExtract, an information extraction tool created by NuMind." 
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": text}] + images,
        }
    ]
    return messages


def process_all_vision_info(messages, examples=None):
    """
    Process vision information from both messages and in-context examples, supporting batch processing.
    
    Args:
        messages: List of message dictionaries (single input) OR list of message lists (batch input)
        examples: Optional list of example dictionaries (single input) OR list of example lists (batch)
    
    Returns:
        A flat list of all images in the correct order:
        - For single input: example images followed by message images
        - For batch input: interleaved as (item1 examples, item1 input, item2 examples, item2 input, etc.)
        - Returns None if no images were found
    """
    
    
    # Helper function to extract images from examples
    def extract_example_images(example_item):
        if not example_item:
            return []
            
        # Handle both list of examples and single example
        examples_to_process = example_item if isinstance(example_item, list) else [example_item]
        images = []
        
        for example in examples_to_process:
            if isinstance(example.get('input'), dict) and example['input'].get('type') == 'image':
                images.append(fetch_image(example['input']))
                
        return images
    
    # Normalize inputs to always be batched format
    is_batch = messages and isinstance(messages[0], list)
    messages_batch = messages if is_batch else [messages]
    is_batch_examples = examples and isinstance(examples, list) and (isinstance(examples[0], list) or examples[0] is None)
    examples_batch = examples if is_batch_examples else ([examples] if examples is not None else None)
    
    # Ensure examples batch matches messages batch if provided
    if examples and len(examples_batch) != len(messages_batch):
        if not is_batch and len(examples_batch) == 1:
            # Single example set for a single input is fine
            pass
        else:
            raise ValueError("Examples batch length must match messages batch length")
    
    # Process all inputs, maintaining correct order
    all_images = []
    for i, message_group in enumerate(messages_batch):
        # Get example images for this input
        if examples and i < len(examples_batch):
            input_example_images = extract_example_images(examples_batch[i])
            all_images.extend(input_example_images)
        
        # Get message images for this input
        input_message_images = process_vision_info(message_group)[0] or []
        all_images.extend(input_message_images)
    
    return all_images if all_images else None


# =====================
# UTILITY GENERALI
# =====================
def extract_entities(text, template):
        # prepare the user message content
    messages = [{"role": "user", "content": text}]
    text = processor.tokenizer.apply_chat_template(
        messages,
        template=template, # template is specified here
        tokenize=False,
        add_generation_prompt=True,
    )

    print(text)

    image_inputs = process_all_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        padding=True,
        return_tensors="pt",
    ).to("cpu")

    # we choose greedy sampling here, which works well for most information extraction tasks
    generation_config = {"do_sample": False, "num_beams": 1, "max_new_tokens": 2048}

    # Inference: Generation of the output
    generated_ids = model.generate(
        **inputs,
        **generation_config
    )
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )

    print(output_text)
    
    # Gestisci il caso in cui output_text è una lista
    if isinstance(output_text, list) and len(output_text) > 0:
        return output_text[0]  # Restituisci il primo elemento della lista
    elif isinstance(output_text, list):
        return ""  # Restituisci stringa vuota se la lista è vuota
    else:
        return output_text


