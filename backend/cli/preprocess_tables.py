import json
import re
from langchain_core import documents
import pandas as pd
from io import StringIO
from langchain_core.documents import Document


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


def markdown_table_to_df(table_md):
    df = pd.read_table(StringIO(table_md), sep="|", engine="python")

    # Drop completely empty columns (leading/trailing pipes)
    df = df.dropna(axis=1, how="all")

    # Strip column whitespace
    df.columns = df.columns.str.strip()

    # Remove markdown separator row (---- | ----)
    df = df.iloc[1:].reset_index(drop=True)

    # Strip cell whitespace
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

    # Remove duplicate columns (critical fix)
    df = df.loc[:, ~df.columns.duplicated()]

    return df


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


def format_table_compact(
    df: pd.DataFrame,
    section: str,
    filing_type: str = "10-K",
    unit: str | None = None,
    table_id: int | None = None,
) -> str:
    """
    Convert a DataFrame into a token-efficient structured text block
    suitable for embedding.

    Output format:

    Filing Type: 10-K
    Section: ...
    Unit: USD millions

    Columns: Line Item, 2021, 2022, 2023.

    Revenue: 980, 1050, 1200.
    COGS: 600, 650, 700.
    """

    if df.empty:
        return ""

    # Ensure clean column names
    df.columns = df.columns.astype(str).str.strip()

    # Identify label column
    label_col = df.columns[0]
    value_cols = list(df.columns[1:])

    lines = []

    # Header context (minimal redundancy)
    lines.append(f"Filing Type: {filing_type}")
    lines.append(f"Section: {section}")

    if table_id is not None:
        lines.append(f"Table ID: {table_id}")

    if unit:
        lines.append(f"Unit: {unit}")

    lines.append("")  # spacing

    # Column definition once
    column_line = "Columns: " + ", ".join([label_col] + value_cols) + "."
    lines.append(column_line)
    lines.append("")

    # Row data
    for _, row in df.iterrows():
        label = str(row[label_col]).strip()

        values = []
        for col in value_cols:
            val = row[col]
            if pd.notna(val) and val != "":
                values.append(str(val).strip())
            else:
                values.append("")

        row_line = f"{label}: {', '.join(values)}."
        lines.append(row_line)

    return "\n".join(lines)


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

        # Store raw table in Postgres, get back the DB ID

        # Clean numeric columns
        for col in df.columns:
            df[col + "_numeric"] = df[col].apply(normalize_numeric)

        text = format_table_compact(
            df=df,
            section=section,
            unit="USD millions",
            table_id=table_id,
        )

        documents.append(Document(page_content=text))

    print(documents[0])  # Print first 500 chars of first table document

    print(f"Generated {len(documents)} table documents")
    return documents
