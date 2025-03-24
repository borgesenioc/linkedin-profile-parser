# Linkedin Profile Parser

This web app transforms Linkedin scraped profiles into CSVs formatted to be uploaded to OnFrontiers. The inputs CSVs could be scraped in bulk of a few thousand profiles unsing Phantombuster. The output has columns named as the OnFrontiers Profile uploader expects them.

---

## Live Demo

Check out the live version here:  
TBA

---

## App Architecture

    1.	Flask: Provides an endpoint to “start CSV processing.” Pass the CSV or the list of profile IDs, etc.
    2.	Celery: The Flask endpoint enqueues a task that’s picked up by Celery workers.
    3.	Celery Worker: Runs a function that fetches profiles in parallel (using asyncio) and writes the results to a CSV.
    4.	Callback: the worker calls the server with a “job done” callback
    5.	Results: Once complete, the CSV becomes available for Download.

Folder Structure

linkedin-profile-parser/
├── app.py
├── convert.py
├── checkSnapshot.py
├── public/
│ ├── index.html
│ └── ...
└── requirements.txt

Support from: https://chatgpt.com/share/e/67e05f43-be2c-8001-acba-7224e2b29446
