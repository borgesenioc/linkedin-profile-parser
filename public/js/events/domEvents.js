// public/js/events/domEvents.js
document.addEventListener('DOMContentLoaded', () => {
  const convertButton = document.getElementById('convertButton1');
  const urlInput = document.getElementById('urlInput');
  const successMessage = document.getElementById('successMessage1');

  convertButton.addEventListener('click', async () => {
    const linkedinUrl = urlInput.value.trim();
    if (!linkedinUrl) {
      alert('Please enter a LinkedIn profile URL.');
      return;
    }

    successMessage.textContent = 'Triggering scraping...';
    successMessage.style.display = 'block';

    try {
      // 1) Trigger the job and get the snapshotId
      const convertRes = await fetch('/api/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ linkedinUrl }),
      });
      if (!convertRes.ok) throw new Error('Failed to trigger scraping');
      const { snapshotId } = await convertRes.json();

      successMessage.textContent = `LinkedIn profile found. We'll start preparing your CSV.`;

      // 2) Poll for readiness
      let retries = 0;
      const maxRetries = 10;
      const delay = 20000; // 20 seconds

      async function poll() {
        try {
          const checkRes = await fetch(
            `/api/checkSnapshot?snapshotId=${snapshotId}`
          );
          if (!checkRes.ok) throw new Error('Check snapshot failed');

          const contentType = checkRes.headers.get('content-type');
          if (contentType.includes('application/json')) {
            // Likely still "running"
            const data = await checkRes.json();
            if (data.status === 'running') {
              if (retries === 0) {
                retries++;
                successMessage.innerHTML = `Building the CSV might take a minute.<br><br>In the meantime, please note: this app only scrapes profile <strong>data isn't behind login</strong>.`;
                setTimeout(poll, delay);
              } else if (retries === 1) {
                retries++;
                successMessage.innerHTML = `Parsing data to the CSV.<br><br>Users choose which data goes public, which often includes the full profile.`;
                setTimeout(poll, delay);
              } else if (retries === 2 || retries === 3) {
                retries++;
                successMessage.innerHTML = `We are almost there...`;
                setTimeout(poll, delay);
              } else if (retries > 3 && retries < maxRetries) {
                retries++;
                successMessage.innerHTML = `Finishing the CSV. This one took a bit longer than usual.`;
                setTimeout(poll, delay);
              } else {
                successMessage.textContent =
                  'Still not ready and our API reached the limit attempts. Sorry, we failed this time!';
              }
            } else {
              successMessage.textContent = 'Unexpected JSON response.';
            }
          } else if (contentType.includes('text/csv')) {
            // CSV is ready – download it
            const blob = await checkRes.blob();
            const downloadLink = document.createElement('a');
            downloadLink.href = URL.createObjectURL(blob);
            downloadLink.download = `profile_${new Date().toISOString()}.csv`;
            downloadLink.click();

            successMessage.textContent =
              'Success! You can download the CSV now.';
          } else {
            successMessage.textContent = 'Unknown response type.';
          }
        } catch (err) {
          successMessage.textContent = 'Error polling snapshot.';
          console.error(err);
        }
      }

      poll();
    } catch (error) {
      console.error('Error triggering scraping:', error);
      successMessage.textContent =
        'Error triggering scraping. Please try again.';
    }
  });
});
