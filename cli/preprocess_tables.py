import re
import pandas as pd
from io import StringIO
from langchain_core.documents import Document


# ===============================
# STEP 2 — EXTRACT TABLES + SECTIONS
# ===============================


def extract_tables_with_sections(md_text):
    lines = md_text.split("\n")
    current_section = "Unknown Section"
    tables = []
    table_buffer = []
    in_table = False

    for line in lines:
        # Detect markdown headers
        if line.startswith("#"):
            current_section = line.strip("# ").strip()

        # Detect table rows
        if line.startswith("|"):
            table_buffer.append(line)
            in_table = True
        else:
            if in_table:
                tables.append((current_section, "\n".join(table_buffer)))
                table_buffer = []
                in_table = False

    return tables


# ===============================
# STEP 3 — MARKDOWN TABLE → DATAFRAME
# ===============================


def markdown_table_to_df(table_md):
    df = pd.read_table(StringIO(table_md), sep="|", engine="python")

    # Drop completely empty columns (leading/trailing pipes)
    df = df.dropna(axis=1, how="all")

    # Strip column whitespace
    df.columns = df.columns.str.strip()

    # Drop empty column names
    df = df.loc[:, df.columns != ""]

    # Remove markdown separator row (---- | ----)
    df = df.iloc[1:].reset_index(drop=True)

    # Strip cell whitespace
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

    # Remove duplicate columns (critical fix)
    df = df.loc[:, ~df.columns.duplicated()]

    return df


# ===============================
# STEP 4 — NUMERIC NORMALIZATION
# ===============================


def normalize_numeric(x):
    if pd.isna(x):
        return None
    x = str(x).strip()

    if x == "-" or x == "":
        return None

    # Handle (1,234) → -1234
    if "(" in x and ")" in x:
        x = "-" + x.replace("(", "").replace(")", "")

    x = re.sub(r"[^\d.-]", "", x)

    try:
        return float(x)
    except:
        return None


# ===============================
# MAIN ENTRY POINT
# ===============================


def run_extraction(filepath: str) -> list[Document]:
    # STEP 1 — LOAD MARKDOWN
    with open(filepath, "r", encoding="utf-8") as f:
        md_content = f.read()

    # STEP 2 — EXTRACT TABLES + SECTIONS
    table_sections = extract_tables_with_sections(md_content)
    print(f"Found {len(table_sections)} tables")

    # STEP 3 — BUILD DOCUMENTS + METADATA
    documents = []

    for table_id, (section, table_md) in enumerate(table_sections):
        df = markdown_table_to_df(table_md)

        # Clean numeric columns
        for col in df.columns:
            df[col + "_numeric"] = df[col].apply(normalize_numeric)

        for row_id, row in df.iterrows():
            row_text = "\n".join(
                [
                    f"{col}: {row[col]}"
                    for col in df.columns
                    if not col.endswith("_numeric")
                ]
            )

            full_text = (
                f"Filing Type: 10-K\n"
                f"Section: {section}\n"
                f"Table ID: {table_id}\n"
                f"Row ID: {row_id}\n"
                f"{row_text}"
            )

            meta = {
                "source": filepath,
                "section": section,
                "table_id": table_id,
                "row_id": row_id,
            }

            # Add numeric fields to metadata
            for col in df.columns:
                if col.endswith("_numeric") and row[col] is not None:
                    meta[col] = row[col]

            documents.append(Document(page_content=full_text, metadata=meta))

    print(f"Generated {len(documents)} table row documents")
    return documents
