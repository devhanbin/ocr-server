import re


def extract_fields(text: str) -> dict:
    """
    OCR 텍스트에서 계약서 필드 추출
    """
    return {
        "계약기간_시작일": extract_start_date(text),
        "계약기간_종료일": extract_end_date(text),
        "신규연장": extract_new_or_extend(text),
        "계약구분": extract_contract_type(text),
        "계약금_선급금": extract_amount(text, ["계약금", "선급금"]),
        "중도금": extract_amount(text, ["중도금"]),
        "잔금": extract_amount(text, ["잔금"]),
        "총계약대금": extract_amount(text, ["총 계약대금", "총계약대금"]),
        "수수료_공급률": extract_rate(text),
        "부가세_포함여부": extract_vat(text),
        "기타": extract_field_value(text, "기타"),
        "비고": extract_field_value(text, "비고"),
    }


def extract_start_date(text: str):
    """계약기간 시작일 추출"""
    patterns = [
        r"계약기간\s*[：:]\s*(\d{4}[.\-년]\s*\d{1,2}[.\-월]\s*\d{1,2})",
        r"(\d{4}[.\-년]\s*\d{1,2}[.\-월]\s*\d{1,2})\s*[~～\-]",
        r"기간\s*[：:]?\s*(\d{4}\.\d{1,2}\.\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return normalize_date(match.group(1))
    return None


def extract_end_date(text: str):
    """계약기간 종료일 추출"""
    patterns = [
        r"[~～\-]\s*(\d{4}[.\-년]\s*\d{1,2}[.\-월]\s*\d{1,2})",
        r"까지\s*[：:]?\s*(\d{4}\.\d{1,2}\.\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return normalize_date(match.group(1))
    return None


def extract_new_or_extend(text: str):
    """신규/연장 추출"""
    if re.search(r"연장", text):
        return "연장"
    if re.search(r"신규", text):
        return "신규"
    return None


def extract_contract_type(text: str):
    """계약구분 추출"""
    patterns = [
        r"계약구분\s*[：:]?\s*([가-힣\w]+)",
        r"계약\s*종류\s*[：:]?\s*([가-힣\w]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def extract_amount(text: str, keywords: list):
    """금액 추출 (키워드 기반)"""
    for keyword in keywords:
        pattern = rf"{keyword}[^0-9]*?([\d,]+)\s*원"
        match = re.search(pattern, text)
        if match:
            return match.group(1).replace(",", "") + "원"
    return None


def extract_rate(text: str):
    """수수료/공급률 추출"""
    patterns = [
        r"수수료[^0-9]*?([\d.]+)\s*%",
        r"공급률[^0-9]*?([\d.]+)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1) + "%"
    return None


def extract_vat(text: str):
    """부가세 포함여부 추출"""
    if re.search(r"부가세?\s*포함", text):
        return "포함"
    if re.search(r"부가세?\s*비포함|부가세?\s*별도", text):
        return "비포함"
    return None


def extract_field_value(text: str, keyword: str):
    """기타/비고 등 단순 키워드 다음 값 추출"""
    pattern = rf"{keyword}\s*[：:]?\s*([^\n]+)"
    match = re.search(pattern, text)
    if match:
        value = match.group(1).strip()
        return value if value else None
    return None


def normalize_date(date_str: str) -> str:
    """날짜 형식 정규화 → YYYY-MM-DD"""
    date_str = date_str.strip()
    date_str = re.sub(r"[년월]", "-", date_str)
    date_str = re.sub(r"일", "", date_str)
    date_str = re.sub(r"\s", "", date_str)
    date_str = date_str.rstrip("-")

    parts = re.split(r"[-.]", date_str)
    if len(parts) == 3:
        year, month, day = parts
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return date_str
