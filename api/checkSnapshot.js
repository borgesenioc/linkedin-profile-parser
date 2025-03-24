// public/api/checkSnapshot.js
import dotenv from 'dotenv';
dotenv.config();
import axios from 'axios';

// Helper functions for CSV conversion
function escapeCsvField(field) {
  if (field == null) return '';
  return `"${String(field).replace(/"/g, '""')}"`;
}

function flattenDescription(description) {
  return description ? description.replace(/\r?\n|\r/g, ' ').trim() : '';
}

function generateFourDigitCode(index) {
  return String(1000 + index).slice(-4);
}

function mapProfileToCsvRows(jsonData) {
  const columns = [
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
    'summary',
    ...Array.from({ length: 10 }, (_, i) => [
      `organization_${i + 1}`,
      `organization_id_${i + 1}`,
      `organization_url_${i + 1}`,
      `organization_title_${i + 1}`,
      `organization_start_${i + 1}`,
      `organization_end_${i + 1}`,
      `organization_description_${i + 1}`,
    ]).flat(),
    ...Array.from({ length: 3 }, (_, i) => [
      `education_${i + 1}`,
      `education_degree_${i + 1}`,
      `education_fos_${i + 1}`,
      `education_start_${i + 1}`,
      `education_end_${i + 1}`,
    ]).flat(),
    ...Array.from({ length: 3 }, (_, i) => [
      `language_${i + 1}`,
      `language_proficiency_${i + 1}`,
    ]).flat(),
    'languages',
    'skills',
  ];

  const csvRow = {};

  // Basic profile info
  csvRow.id = jsonData.linkedin_num_id || '';
  csvRow.id_type = '';
  csvRow.public_id = jsonData.linkedin_id || '';
  csvRow.profile_url = jsonData.url || jsonData.input_url || '';
  csvRow.full_name = jsonData.name || '';
  csvRow.first_name = jsonData.name ? jsonData.name.split(' ')[0] : '';
  csvRow.last_name = jsonData.name
    ? jsonData.name.split(' ').slice(1).join(' ')
    : '';
  csvRow.avatar = jsonData.avatar || '';
  csvRow.headline = jsonData.position || '';
  csvRow.location_name = jsonData.city || '';
  csvRow.summary = jsonData.about ? flattenDescription(jsonData.about) : '';

  // Flatten experience
  let experienceRecords = [];
  if (jsonData.experience && Array.isArray(jsonData.experience)) {
    jsonData.experience.forEach((exp) => {
      if (
        exp.positions &&
        Array.isArray(exp.positions) &&
        exp.positions.length > 0
      ) {
        exp.positions.forEach((pos) => {
          experienceRecords.push({
            organization: exp.company || '',
            organization_url:
              exp.url ||
              (jsonData.current_company ? jsonData.current_company.link : '') ||
              '',
            organization_title: pos.title || '',
            organization_start: pos.start_date || '',
            organization_end: pos.end_date || '',
            organization_description:
              pos.description || pos.description_html || exp.description || '',
          });
        });
      } else {
        experienceRecords.push({
          organization: exp.company || '',
          organization_url:
            exp.url ||
            (jsonData.current_company ? jsonData.current_company.link : '') ||
            '',
          organization_title: exp.title || '',
          organization_start: exp.start_date || '',
          organization_end: exp.end_date || '',
          organization_description:
            exp.description || exp.description_html || '',
        });
      }
    });
  }

  // Fill up to 10 experience slots
  for (let i = 0; i < 10; i++) {
    if (i < experienceRecords.length) {
      const exp = experienceRecords[i];
      csvRow[`organization_${i + 1}`] = exp.organization;
      csvRow[`organization_id_${i + 1}`] = generateFourDigitCode(i);
      csvRow[`organization_url_${i + 1}`] = exp.organization_url;
      csvRow[`organization_title_${i + 1}`] = exp.organization_title;
      csvRow[`organization_start_${i + 1}`] = exp.organization_start;
      csvRow[`organization_end_${i + 1}`] = exp.organization_end;
      csvRow[`organization_description_${i + 1}`] = flattenDescription(
        exp.organization_description
      );
    } else {
      csvRow[`organization_${i + 1}`] = '';
      csvRow[`organization_id_${i + 1}`] = '';
      csvRow[`organization_url_${i + 1}`] = '';
      csvRow[`organization_title_${i + 1}`] = '';
      csvRow[`organization_start_${i + 1}`] = '';
      csvRow[`organization_end_${i + 1}`] = '';
      csvRow[`organization_description_${i + 1}`] = '';
    }
  }

  // Education (up to 3)
  if (jsonData.education && Array.isArray(jsonData.education)) {
    jsonData.education.forEach((edu, index) => {
      if (index >= 3) return;
      const idx = index + 1;
      csvRow[`education_${idx}`] = edu.title || '';
      csvRow[`education_degree_${idx}`] = edu.degree || '';
      csvRow[`education_fos_${idx}`] = edu.field || '';
      csvRow[`education_start_${idx}`] = edu.start_year || '';
      csvRow[`education_end_${idx}`] = edu.end_year || '';
    });
  }
  for (let i = jsonData.education ? jsonData.education.length : 0; i < 3; i++) {
    const idx = i + 1;
    csvRow[`education_${idx}`] = '';
    csvRow[`education_degree_${idx}`] = '';
    csvRow[`education_fos_${idx}`] = '';
    csvRow[`education_start_${idx}`] = '';
    csvRow[`education_end_${idx}`] = '';
  }

  // Languages (up to 3)
  if (jsonData.languages && Array.isArray(jsonData.languages)) {
    jsonData.languages.forEach((lang, index) => {
      if (index >= 3) return;
      const idx = index + 1;
      csvRow[`language_${idx}`] = lang.title || '';
      csvRow[`language_proficiency_${idx}`] = lang.subtitle || '';
    });
  }
  for (let i = jsonData.languages ? jsonData.languages.length : 0; i < 3; i++) {
    const idx = i + 1;
    csvRow[`language_${idx}`] = '';
    csvRow[`language_proficiency_${idx}`] = '';
  }
  csvRow.languages = (jsonData.languages || [])
    .map((lang) => lang.title)
    .join(', ');
  csvRow.skills =
    jsonData.skills && Array.isArray(jsonData.skills)
      ? jsonData.skills.map((skill) => skill.name).join(', ')
      : '';

  // Build final CSV output
  const headerRow = columns.join(',');
  const dataRow = columns
    .map((col) => escapeCsvField(csvRow[col] || ''))
    .join(',');
  return `${headerRow}\n${dataRow}`;
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).send(`Method ${req.method} Not Allowed`);
  }

  try {
    const { snapshotId } = req.query;
    if (!snapshotId) {
      return res
        .status(400)
        .json({ error: 'Missing snapshotId in query params' });
    }

    // Check snapshot status
    const snapshotURL = `${process.env.BD_SNAPSHOT_URL || 'https://api.brightdata.com/datasets/v3/snapshot'}/${snapshotId}`;
    const getResponse = await axios.get(snapshotURL, {
      headers: {
        Authorization: `Bearer ${process.env.BD_TOKEN}`,
      },
    });

    // If it's still running, return JSON indicating "running"
    if (getResponse.data.status === 'running') {
      return res.status(200).json({ status: 'running' });
    }

    // Otherwise, we assume it's ready; convert data to CSV
    const profileData = getResponse.data;
    const csvContent = mapProfileToCsvRows(profileData);

    // Send CSV file back to client
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename="profile_${Date.now()}.csv"`
    );
    return res.status(200).send(csvContent);
  } catch (error) {
    console.error('Error in /api/checkSnapshot:', error.message);
    return res.status(500).json({ error: error.message });
  }
}
