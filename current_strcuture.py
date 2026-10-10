import json

import pandas as pd
import requests

# =====================================================
# CONFIGURATION
# =====================================================
TOKEN = "token key"
MAIN_ENDPOINT = "link"

# Replace with your details endpoint.
# Example: https://api.xxx.com/request/details/{id}
DETAIL_ENDPOINT = "link"
METHOD = "POST"
PAYLOAD = {
    "pageNumber": 1,
    "pageSize": 50,
    "filter": {
        "requestId": "",
        "serviceId": "",
        "from": "",
        "to": "",
        "groupCode": "",
        "employeeName": "",
        "statusId": 0,
        "statusIds": [],
        "nameEn": "",
        "nameAr": "",
        "name": "",
        "requestTypeCode": "",
        "taxpayer": "",
        "TIN": "",
        "TaxRegNumber": "",
        "userEmails": [],
    },
    "orderByValue": [{"colId": "createdDate", "sort": "desc"}],
}
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


# =====================================================
# UTILITIES
# =====================================================
def safe_str(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def extract_form_fields(detail_json):
    """Extract visible major fields from viewForm.controls."""
    result = {}
    controls = (
        detail_json.get("result", {})
        .get("data", {})
        .get("viewForm", {})
        .get("controls", [])
    )

    for control in controls:
        label = control.get("label") or control.get("name") or control.get("id")
        if not label:
            continue

        value = control.get("value")
        if isinstance(value, list):
            vals = []
            for item in value:
                if isinstance(item, dict):
                    if "text" in item:
                        vals.append(safe_str(item["text"]))
                    elif "attachmentName" in item:
                        vals.append(safe_str(item["attachmentName"]))
                    else:
                        vals.append(json.dumps(item, ensure_ascii=False))
                else:
                    vals.append(safe_str(item))
            value = " | ".join(vals)
        elif isinstance(value, dict):
            if "text" in value:
                value = value["text"]
            else:
                value = json.dumps(value, ensure_ascii=False)

        result[f"FORM_{label}"] = value

    return result


def build_task_details(detail_json):
    """Summarize workflow history into one column."""
    actions = detail_json.get("result", {}).get("data", {}).get("previousActions", [])
    rows = []

    for action in actions:
        user = action.get("taskOnUserName", "")
        title = action.get("taskOnUserJobTitle", "")
        dept = action.get("taskOnUserDepartmentName", "")
        action_name = (
            action.get("takenAction", {}).get("labelEn")
            or action.get("takenAction", {}).get("name")
            or action.get("takenAction", {}).get("label")
            or ""
        )
        comment = action.get("comment", "")
        created = action.get("createdDate", "")
        completed = action.get("completionDate", "")
        rows.append(
            f"{user} | "
            f"{title} | "
            f"{dept} | "
            f"{action_name} | "
            f"{created} | "
            f"{completed} | "
            f"{comment}"
        )

    return "\n".join(rows)


def get_details(task_id):
    """Call the details endpoint using ID, not requestId."""
    try:
        # OPTION 1: GET detail/{id}
        response = requests.get(
            f"{DETAIL_ENDPOINT}/{task_id}",
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except Exception as ex:
        print(f"Failed getting details for ID {task_id}: {ex}")
        return {}


# =====================================================
# MAIN REQUEST
# =====================================================
try:
    if METHOD.upper() == "POST":
        response = requests.post(
            MAIN_ENDPOINT,
            headers=headers,
            json=PAYLOAD,
            timeout=120,
        )
    elif METHOD.upper() == "GET":
        response = requests.get(
            MAIN_ENDPOINT,
            headers=headers,
            timeout=120,
        )
    else:
        raise Exception(f"Unsupported method {METHOD}")

    response.raise_for_status()
    data = response.json()

    with open("response_raw.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # =================================================
    # TRY TO FIND RECORDS ARRAY AUTOMATICALLY
    # =================================================
    records = None
    candidate_paths = [
        data.get("result", {}).get("data"),
        data.get("data"),
        data.get("items"),
        data.get("result"),
    ]

    for candidate in candidate_paths:
        if isinstance(candidate, list):
            records = candidate
            break

    if records is None:
        if isinstance(data, list):
            records = data
        else:
            raise Exception("Could not find records array in response.")

    # =================================================
    # ENRICH EACH ROW
    # =================================================
    final_rows = []
    total = len(records)

    for idx, row in enumerate(records, 1):
        print(f"Processing {idx}/{total}")
        new_row = dict(row)
        task_id = row.get("id") or row.get("taskId") or row.get("bpmTaskId")

        if not task_id:
            new_row["task_details"] = ""
            final_rows.append(new_row)
            continue

        detail_json = get_details(task_id)

        # Workflow summary
        new_row["task_details"] = build_task_details(detail_json)

        # Status
        detail_data = detail_json.get("result", {}).get("data", {})
        new_row["detail_status"] = detail_data.get("status", {}).get("nameEn")
        new_row["detail_service_name"] = detail_data.get(
            "serviceNameEn"
        ) or detail_data.get("serviceName")
        new_row["detail_created_date"] = detail_data.get("createdDate")
        new_row["detail_completed_date"] = detail_data.get("requestCompletedDate")

        # Extract major form fields
        form_fields = extract_form_fields(detail_json)
        new_row.update(form_fields)
        final_rows.append(new_row)

    # =================================================
    # SAVE TO EXCEL
    # =================================================
    df = pd.json_normalize(final_rows)
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: json.dumps(x, ensure_ascii=False)
            if isinstance(x, (dict, list))
            else x
        )

    output_file = "requests_with_details_v4.xlsx"
    df = df[
        [
            "requestId",
            "detail_status",
            "detail_created_date",
            "FORM_نوع الطلب",
            "FORM_الوكالة",
            "FORM_القطاع",
            "FORM_الإدارة",
            "FORM_التاريخ",
            "FORM_منطقة العمل",
            "FORM_وصف منطقة العمل",
            "FORM_سبب الطلب",
            "FORM_تفاصيل  الطلب",
        ]
    ]
    df.to_excel(output_file, index=False)

    print()
    print("=" * 60)
    print(f"Saved: {output_file}")
    print(f"Rows : {len(df)}")
    print("=" * 60)
except Exception as e:
    print(f"ERROR: {e}")

# Get all pages: all pending tasks.
# Then fetch details by task ID.
# We delegate by task ID.

# Delegation payload
{
    "taskId": "5810314",
    "requestId": "MQR-4062038",
    "assignTo": "",
    "assignToNameEn": "",
    "assignToNameAr": "",
}

# Delegation API
