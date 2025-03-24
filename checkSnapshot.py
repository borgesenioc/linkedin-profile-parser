# checkSnapshot.py

import os
import requests
from flask import Blueprint, request, jsonify, Response

# Define the Blueprint
check_snapshot_bp = Blueprint('check_snapshot_bp', __name__)

def escape_csv_field(field):
    """
    Wrap field in quotes and escape existing quotes.
    Equivalent to the JS escapeCsvField function.
    """
    if field is None:
        return '""'
    text = str(field).replace('"', '""')
    return f'"{text}"'

def flatten_description(description):
    """
    Remove newlines, trim spaces.
    Equivalent to the JS flattenDescription function.
    """
    if not description:
        return ''
    return ' '.join(description.split()).strip()

def generate_four_digit_code(index):
    """
    Generate a zero-based 4-digit code from an index.
    Example: index=0 -> '0000', index=1 -> '0001', etc.
    (In the JS code, it started from 1000 and sliced, but we can adapt as needed.)
    """
    return str(1000 + index)[-4:]

def map_profile_to_csv_rows(json_data):
    """
    Replicates the logic in checkSnapshot.js -> mapProfileToCsvRows().
    Builds a single CSV row from the returned JSON data (which presumably
    contains LinkedIn profile info).
    """

    # 1) Define all columns in the same order as checkSnapshot.js
    columns = [
        'id',
        'id_type',
        'public_id',
        'profile_url',
        'full_name',
        'first_name',
        'last_name',
        'avatar',
        'headline',
        'location_name',
        'summary'
    ]

    # Add 10 groups of experience columns
    for i in range(1, 11):
        columns += [
            f'organization_{i}',
            f'organization_id_{i}',
            f'organization_url_{i}',
            f'organization_title_{i}',
            f'organization_start_{i}',
            f'organization_end_{i}',
            f'organization_description_{i}'
        ]

    # Add 3 groups of education columns
    for i in range(1, 4):
        columns += [
            f'education_{i}',
            f'education_degree_{i}',
            f'education_fos_{i}',
            f'education_start_{i}',
            f'education_end_{i}'
        ]

    # Add 3 groups of languages
    for i in range(1, 4):
        columns += [
            f'language_{i}',
            f'language_proficiency_{i}'
        ]

    # Finally add aggregated languages & skills
    columns += ['languages', 'skills']

    # 2) Initialize a row dict
    csv_row = {col: '' for col in columns}

    # 3) Fill the basic profile info
    csv_row['id'] = json_data.get('linkedin_num_id', '')
    csv_row['id_type'] = ''
    csv_row['public_id'] = json_data.get('linkedin_id', '')
    csv_row['profile_url'] = json_data.get('url') or json_data.get('input_url', '')
    csv_row['full_name'] = json_data.get('name', '')
    name_parts = csv_row['full_name'].split()
    csv_row['first_name'] = name_parts[0] if len(name_parts) > 0 else ''
    csv_row['last_name'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
    csv_row['avatar'] = json_data.get('avatar', '')
    csv_row['headline'] = json_data.get('position', '')
    csv_row['location_name'] = json_data.get('city', '')
    about_text = json_data.get('about')
    csv_row['summary'] = flatten_description(about_text) if about_text else ''

    # 4) Flatten experience
    experience = json_data.get('experience', [])
    experience_records = []
    if isinstance(experience, list):
        for exp in experience:
            # If exp.positions is a list, create multiple records
            positions = exp.get('positions')
            if positions and isinstance(positions, list) and len(positions) > 0:
                for pos in positions:
                    experience_records.append({
                        'organization': exp.get('company', ''),
                        'organization_url': exp.get('url', ''),
                        'organization_title': pos.get('title', ''),
                        'organization_start': pos.get('start_date', ''),
                        'organization_end': pos.get('end_date', ''),
                        'organization_description': (
                            pos.get('description')
                            or pos.get('description_html')
                            or exp.get('description', '')
                        ),
                    })
            else:
                # Single record from top-level exp object
                experience_records.append({
                    'organization': exp.get('company', ''),
                    'organization_url': exp.get('url', ''),
                    'organization_title': exp.get('title', ''),
                    'organization_start': exp.get('start_date', ''),
                    'organization_end': exp.get('end_date', ''),
                    'organization_description': (
                        exp.get('description')
                        or exp.get('description_html', '')
                    ),
                })

    # Fill up to 10 experience slots
    for i in range(10):
        if i < len(experience_records):
            record = experience_records[i]
            idx = i + 1
            csv_row[f'organization_{idx}'] = record.get('organization', '')
            csv_row[f'organization_id_{idx}'] = generate_four_digit_code(i)
            csv_row[f'organization_url_{idx}'] = record.get('organization_url', '')
            csv_row[f'organization_title_{idx}'] = record.get('organization_title', '')
            csv_row[f'organization_start_{idx}'] = record.get('organization_start', '')
            csv_row[f'organization_end_{idx}'] = record.get('organization_end', '')
            csv_row[f'organization_description_{idx}'] = flatten_description(
                record.get('organization_description', '')
            )
        else:
            idx = i + 1
            csv_row[f'organization_{idx}'] = ''
            csv_row[f'organization_id_{idx}'] = ''
            csv_row[f'organization_url_{idx}'] = ''
            csv_row[f'organization_title_{idx}'] = ''
            csv_row[f'organization_start_{idx}'] = ''
            csv_row[f'organization_end_{idx}'] = ''
            csv_row[f'organization_description_{idx}'] = ''

    # 5) Education (up to 3)
    education = json_data.get('education', [])
    if isinstance(education, list):
        for i, edu in enumerate(education):
            if i >= 3:
                break
            idx = i + 1
            csv_row[f'education_{idx}'] = edu.get('title', '')
            csv_row[f'education_degree_{idx}'] = edu.get('degree', '')
            csv_row[f'education_fos_{idx}'] = edu.get('field', '')
            csv_row[f'education_start_{idx}'] = edu.get('start_year', '')
            csv_row[f'education_end_{idx}'] = edu.get('end_year', '')
    # Fill any remaining
    for i in range(len(education), 3):
        idx = i + 1
        csv_row[f'education_{idx}'] = ''
        csv_row[f'education_degree_{idx}'] = ''
        csv_row[f'education_fos_{idx}'] = ''
        csv_row[f'education_start_{idx}'] = ''
        csv_row[f'education_end_{idx}'] = ''

    # 6) Languages (up to 3)
    languages = json_data.get('languages', [])
    if isinstance(languages, list):
        for i, lang in enumerate(languages):
            if i >= 3:
                break
            idx = i + 1
            csv_row[f'language_{idx}'] = lang.get('title', '')
            csv_row[f'language_proficiency_{idx}'] = lang.get('subtitle', '')
    # Fill any remaining
    for i in range(len(languages), 3):
        idx = i + 1
        csv_row[f'language_{idx}'] = ''
        csv_row[f'language_proficiency_{idx}'] = ''

    # Aggregated languages
    csv_row['languages'] = ', '.join(lang.get('title', '') for lang in languages)
    # Skills
    skills = json_data.get('skills', [])
    if isinstance(skills, list):
        csv_row['skills'] = ', '.join(skill.get('name', '') for skill in skills)
    else:
        csv_row['skills'] = ''

    # 7) Build the CSV string
    header_row = ','.join(columns)
    data_row_fields = []
    for col in columns:
        data_row_fields.append(escape_csv_field(csv_row[col]))

    data_row = ','.join(data_row_fields)
    csv_string = f"{header_row}\n{data_row}"
    return csv_string

@check_snapshot_bp.route('/checkSnapshot', methods=['GET'])
def check_snapshot_handler():
    """
    GET /api/checkSnapshot?snapshotId=XYZ
    1) Fetch snapshot info from BD_SNAPSHOT_URL/<snapshotId>
    2) If it's running, return JSON {status: 'running'}
    3) Otherwise, convert the data to CSV & return it.
    """
    if request.method != 'GET':
        return jsonify({"error": f"Method {request.method} Not Allowed"}), 405

    snapshot_id = request.args.get('snapshotId')
    if not snapshot_id:
        return jsonify({"error": "Missing snapshotId"}), 400

    # Build the snapshot URL from environment or fallback
    base_url = os.environ.get('BD_SNAPSHOT_URL', 'https://api.brightdata.com/datasets/v3/snapshot')
    snapshot_url = f"{base_url}/{snapshot_id}"

    try:
        # Call the external endpoint
        headers = {
            'Authorization': f"Bearer {os.environ.get('BD_TOKEN', '')}"
        }
        resp = requests.get(snapshot_url, headers=headers)
        resp.raise_for_status()  # Raise HTTPError if non-2xx

        data = resp.json()
        # If it's still running
        if data.get('status') == 'running':
            return jsonify({"status": "running"}), 200

        # Otherwise, assume we have the final data
        csv_content = map_profile_to_csv_rows(data)

        # Return CSV
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="profile_{snapshot_id}.csv"'
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500