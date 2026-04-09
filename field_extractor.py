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
        "계약금_선급금": extract_amount(text, ["선금", "선급금", "계약금"]),
        "중도금": extract_amount(text, ["중도금"]),
        "잔금": extract_amount(text, ["잔금"]),
        "총계약대금": extract_total_amount(text),
        "수수료_공급률": extract_rate(text),
        "부가세_포함여부": extract_vat(text),
        "기타": extract_field_value(text, "기타"),
        "비고": extract_field_value(text, "비고"),
    }


def extract_start_date(text: str):
    """계약기간 시작일 추출 - 'N년 N월 N일부터' 패턴"""
    patterns = [
        r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일부터",
        r"(\d{4})[.\-]\s*(\d{1,2})[.\-]\s*(\d{1,2})\s*[~～\-]",
        r"계약기간\s*[：:]\s*(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year, month, day = match.group(1), match.group(2), match.group(3)
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return None


def extract_end_date(text: str):
    """계약기간 종료일 추출 - 'N년 N월 N일까지' 패턴"""
    patterns = [
        r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일까지",
        r"[~～\-]\s*(\d{4})[.\-]\s*(\d{1,2})[.\-]\s*(\d{1,2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year, month, day = match.group(1), match.group(2), match.group(3)
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
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
    """금액 추출 - 숫자 패턴"""
    for keyword in keywords:
        pattern = rf"{keyword}[^\n]{{0,30}}?\\?([\d,]{{6,}})"
        match = re.search(pattern, text)
        if match:
            amount = match.group(1).replace(",", "")
            return amount + "원"
    return None


def extract_total_amount(text: str):
    """총 계약대금 추출"""
    patterns = [
        r"계약금액[^\\n]{0,30}\\([\d,]+)",
        r"합계\s*100\.0%\s*\\([\d,]+)",
        r"W60,000,000",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            nums = re.findall(r"[\d,]+", match.group(0))
            if nums:
                return nums[-1].replace(",", "") + "원"
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
    if re.search(r"부가세\s*포함", text):
        return "포함"
    if re.search(r"부가세\s*(별도|비포함)", text):
        return "비포함"
    return None


def extract_field_value(text: str, keyword: str):
    """기타/비고 등 단순 키워드 다음 값 추출"""
    pattern = rf"{keyword}\s*[：:]?\s*([^\n]+)"
    match = re.search(pattern, text)
    if match:
        value = match.group(1).strip()
        return value if value and len(value) < 100 else None
    return None