# convert.py

import os
import requests
from flask import Blueprint, request, jsonify

convert_bp = Blueprint('convert', __name__)

@convert_bp.route('/convert', methods=['POST'])
def convert_handler():
    if request.method != 'POST':
        return jsonify({"error": f"Method {request.method} Not Allowed"}), 405

    try:
        data = request.get_json()
        linkedin_url = data.get('linkedinUrl')
        if not linkedin_url:
            return jsonify({"error": "Missing linkedinUrl in request body"}), 400

        # Prepare payload for the scraping trigger
        post_data = [{"url": linkedin_url}]
        trigger_url = (
            f"{os.environ['BD_API_URL']}?dataset_id={os.environ['DATASET_ID']}"
            "&include_errors=true"
        )

        # Make the POST request to the external API
        headers = {
            "Authorization": f"Bearer {os.environ['BD_TOKEN']}",
            "Content-Type": "application/json"
        }
        response = requests.post(trigger_url, json=post_data, headers=headers)
        response.raise_for_status()

        # Get snapshotId from the response
        resp_json = response.json()
        snapshot_id = resp_json.get('snapshot_id')
        if not snapshot_id:
            raise ValueError("No snapshot_id returned from the trigger request.")

        # Return snapshotId to the client
        return jsonify({"snapshotId": snapshot_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500