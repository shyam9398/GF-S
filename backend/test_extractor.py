from app.documents.extractor import extract_pdf_text


PDF_PATH = (
    "uploads/"
    "22a2278a-ddb5-4700-97f1-719b741ceaa2_"
    "sample_sih26108_tender_industrial_safety_helmets.pdf"
)


try:
    text = extract_pdf_text(PDF_PATH)

    print("\n========== PDF EXTRACTION SUCCESS ==========\n")
    print(text[:10000])

    print("\n========== END OF PREVIEW ==========\n")

    print(
        f"Total extracted characters: {len(text)}"
    )

except Exception as error:
    print("\n========== PDF EXTRACTION FAILED ==========\n")
    print(type(error).__name__)
    print(error)