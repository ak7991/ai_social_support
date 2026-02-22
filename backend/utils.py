import ollama
import pymupdf as fitz
from time import time
import os

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen3-vl:8b"
# MODEL_NAME = "qwen3-vl:235b-cloud"
PATH_PREFIX = "../uploaded_files/"
client = ollama.Client(host=OLLAMA_HOST)

def convert_pdf_to_images(pdf_path, output_folder=f"{PATH_PREFIX}images"):
    doc = fitz.open(PATH_PREFIX + pdf_path)
    # Create output folder if it doesn't exist
    import os
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    pages = len(doc)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Load a specific page
        pix = page.get_pixmap()        # Render page to image

        # Specify output path and filename
        output_file = os.path.join(output_folder, f"page_{page_num + 1}.png")
        pix.save(output_file)          # Save the image as a PNG
        print(f"Saved {output_file}")

    doc.close()
    print("Conversion successful!")
    return pages

def _load_cache(filetype: str, path: str) -> str | None:
    """Return cached content if it exists.

    The cache filename follows the pattern ``cache_{filetype}_{basename}.txt``
    where ``basename`` is the original filename without extension.
    """
    basename = os.path.splitext(os.path.basename(path))[0]
    cache_file = f"./cache_{filetype}_{basename}.txt"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None

def _save_cache(filetype: str, path: str, content: str) -> None:
    """Save ``content`` to the cache file for the given ``filetype`` and ``path``."""
    basename = os.path.splitext(os.path.basename(path))[0]
    cache_file = f"./cache_{filetype}_{basename}.txt"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Failed to write cache file {cache_file}: {e}")


def resume_parser(resume_path: str):
    prompt = f"""
You are an expert resume parser.

Return the following information:
- full_name
- email
- phone
- skills
- education
- experience
    """
    # Check cache first
    cached = _load_cache("resume", resume_path)
    if cached is not None:
        print("Returning cached resume parsing result")
        return cached

    t1 = time()
    print('starting resume parsing')
    pages = convert_pdf_to_images(resume_path)
    print('pages: ', pages)
    image_paths = [f"../uploaded_files/images/page_{i+1}.png" for i in range(pages)]
    stream = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You extract structured data."},
            {"role": "user", "content": prompt, "images": image_paths}
        ],
        stream=True
    )
    response = ""
    for chunk in stream:
        response += chunk["message"]["content"]
        print(chunk['message']['content'], end='', flush=True)

    elapsed = time() - t1
    print(f'Successfully parsed resume in {elapsed} seconds')
    _save_cache("resume", resume_path, response)
    return response

def id_card_parser(id_card_path: str):
    prompt = f"""
You are an ID card OCR and parser.

Return the following information:
- full_name
- id_number
- date_of_birth
- address
    """
    # Check cache first
    cached = _load_cache("id_card", id_card_path)
    if cached is not None:
        print("Returning cached ID card parsing result")
        return cached
    id_card_path = PATH_PREFIX + id_card_path
    print('starting id_card parsing: ', id_card_path)
    breakpoint()
    # pages = convert_pdf_to_images(id_card_path)
    # image_paths = [f"images/page_{i+1}.png" for i in range(pages)]
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You extract structured data from ID documents."},
            {"role": "user", "content": prompt, 'images': [id_card_path]}
        ]
    )
    print('Successfully parsed id_card')
    result = response["message"]["content"]
    _save_cache("id_card", id_card_path, result)
    return result

def bank_statement_parser(statement_path: str):
    prompt = f"""
You are a financial document analysis system.

Extract the following information along with some description/brief:
- account_holder_name
- bank_name
- account_number (masked if visible)
- statement_start_date
- statement_end_date
- min_balance
- max_balance
- total_credit_inflow
- total_debit_outflow
- number_of_transactions
- currency (if visible)
    """
    # Check cache first
    cached = _load_cache("bank_statement", statement_path)
    if cached is not None:
        print("Returning cached bank statement parsing result")
        return cached

    print('parsing bank stmt')
    pages = convert_pdf_to_images(statement_path)
    pages = 2
    image_paths = [f"../uploaded_files/images/page_{i+1}.png" for i in range(pages)]
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You extract financial metadata from bank statements.",
                "images": image_paths
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

    )
    print('Successfully parsed bank stmt')
    result = response["message"]["content"]
    _save_cache("bank_statement", statement_path, result)
    return result

if __name__ == "__main__":
    # result = resume_parser("../uploaded_files/akshay_ds_resume_single_col.pdf")
    # print("result: ", result)
    # breakpoint()
    result = bank_statement_parser("../uploaded_files/IDFCFIRSTBankstatement_10111095788_100742082_260221_100750.pdf")
    print("result: ", result)
