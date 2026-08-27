/* AI PDF Scanner Platform Frontend Logic */

let currentExtractedText = "";

function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active-tab'));

    const section = document.getElementById(`section-${tabId}`);
    const tabBtn = document.getElementById(`tab-${tabId}`);

    if (section) section.classList.remove('hidden');
    if (tabBtn) tabBtn.classList.add('active-tab');

    if (tabId === 'expense') fetchExpenseReport();
    if (tabId === 'workflow') fetchWorkflows();
}

async function handleScanSubmit(e) {
    e.preventDefault();
    const fileInput = document.getElementById('scanFileInput');
    if (!fileInput.files.length) return alert("Please select a file.");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('language', document.getElementById('scanLangSelect').value);
    formData.append('is_handwritten', document.getElementById('scanModeSelect').value);

    const box = document.getElementById('scanResultBox');
    box.innerHTML = `<p class="text-blue-400 italic"><i class="fas fa-spinner fa-spin mr-2"></i> Processing document edge detection, AI enhancement, and OCR extraction...</p>`;

    try {
        const response = await fetch('/api/ocr/process', { method: 'POST', body: formData });
        const data = await response.json();

        currentExtractedText = data.ocr.extracted_text;
        document.getElementById('extractTextInput').value = currentExtractedText;
        document.getElementById('summarySourceText').value = currentExtractedText;

        document.getElementById('scanBadge').classList.remove('hidden');
        box.innerHTML = `
            <div class="p-2 bg-blue-950/60 rounded border border-blue-800 mb-2">
                <span class="font-bold text-blue-300">Category:</span> ${data.classification.category} (${data.classification.document_type}) <br>
                <span class="font-bold text-blue-300">Confidence:</span> ${(data.classification.confidence * 100).toFixed(1)}% |
                <span class="font-bold text-blue-300">OCR Accuracy:</span> ${data.ocr.accuracy}%
            </div>
            <div class="text-gray-300 whitespace-pre-line">${data.ocr.extracted_text}</div>
        `;
    } catch (err) {
        box.innerHTML = `<p class="text-red-400">Error processing OCR: ${err.message}</p>`;
    }
}

async function runDataExtraction(format) {
    const text = document.getElementById('extractTextInput').value || currentExtractedText;
    const docType = document.getElementById('extractDocType').value;
    const outputBox = document.getElementById('extractionOutput');

    const formData = new FormData();
    formData.append('text_content', text);
    formData.append('document_type', docType);
    formData.append('export_format', format);

    try {
        const response = await fetch('/api/extract', { method: 'POST', body: formData });
        if (format === 'csv') {
            const csvText = await response.text();
            outputBox.textContent = csvText;
        } else {
            const data = await response.json();
            outputBox.textContent = JSON.stringify(data, null, 2);
        }
    } catch (err) {
        outputBox.textContent = "Extraction failed: " + err.message;
    }
}

async function handleChatSubmit(e) {
    e.preventDefault();
    const queryInput = document.getElementById('chatQueryInput');
    const question = queryInput.value.trim();
    if (!question) return;

    const messagesBox = document.getElementById('chatMessagesBox');
    messagesBox.innerHTML += `
        <div class="bg-blue-900/40 p-3 rounded-lg border border-blue-700 max-w-md ml-auto text-right">
            <p class="text-xs font-bold text-blue-300 mb-1">You</p>
            <p class="text-gray-100">${question}</p>
        </div>
    `;

    queryInput.value = "";
    messagesBox.scrollTop = messagesBox.scrollHeight;

    try {
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text_content: currentExtractedText || "Invoice Total Amount: $1,770.00. Vendor: Acme Cloud Solutions. Due Date: 2026-04-15.",
                question: question
            })
        });
        const data = await response.json();

        messagesBox.innerHTML += `
            <div class="bg-gray-800 p-3 rounded-lg border border-gray-700 max-w-md">
                <p class="text-xs font-bold text-green-400 mb-1">AI Document Copilot</p>
                <p class="text-gray-200">${data.answer}</p>
                <span class="text-xxs text-gray-500 mt-1 block">Vector Search Score: ${(data.confidence * 100).toFixed(0)}%</span>
            </div>
        `;
        messagesBox.scrollTop = messagesBox.scrollHeight;
    } catch (err) {
        messagesBox.innerHTML += `<div class="text-red-400 text-xs">Error fetching answer.</div>`;
    }
}

async function runSummarizer() {
    const text = document.getElementById('summarySourceText').value || currentExtractedText;
    const outputBox = document.getElementById('summaryOutput');

    try {
        const response = await fetch('/api/ai/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text_content: text, summary_type: "Executive Summary" })
        });
        const data = await response.json();
        outputBox.innerHTML = `
            <p class="font-bold text-yellow-400">Executive Summary:</p>
            <p class="mb-2">${data.executive_summary}</p>
            <p class="font-bold text-yellow-400">Key Action Items:</p>
            <ul class="list-disc pl-4 space-y-1">${data.action_items.map(i => `<li>${i}</li>`).join('')}</ul>
        `;
    } catch (err) {
        outputBox.textContent = "Summarization failed.";
    }
}

async function runTranslation() {
    const text = document.getElementById('summarySourceText').value || currentExtractedText;
    const lang = document.getElementById('targetLangSelect').value;
    const outputBox = document.getElementById('translationOutput');

    try {
        const response = await fetch('/api/ai/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text_content: text, target_language: lang })
        });
        const data = await response.json();
        outputBox.innerHTML = `
            <p class="font-bold text-indigo-400 mb-2">Target Language: ${data.target_language}</p>
            <div class="p-3 bg-gray-950 rounded border border-gray-800">${data.translated_text}</div>
        `;
    } catch (err) {
        outputBox.textContent = "Translation failed.";
    }
}

async function runPdfMerge() {
    const fileInput = document.getElementById('mergeFileInput');
    if (!fileInput.files.length) return alert("Select at least 1 PDF file.");

    const formData = new FormData();
    for (let f of fileInput.files) formData.append('files', f);

    const response = await fetch('/api/pdf/merge', { method: 'POST', body: formData });
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "merged.pdf";
        a.click();
    }
}

async function runPdfSplit() {
    const fileInput = document.getElementById('splitFileInput');
    if (!fileInput.files.length) return alert("Select a PDF file.");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const response = await fetch('/api/pdf/split', { method: 'POST', body: formData });
    const data = await response.json();
    alert(data.message);
}

async function runPdfProtect() {
    const fileInput = document.getElementById('protectFileInput');
    const pwd = document.getElementById('pdfPasswordInput').value;
    if (!fileInput.files.length || !pwd) return alert("Select PDF and enter password.");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('password', pwd);

    const response = await fetch('/api/pdf/protect', { method: 'POST', body: formData });
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "protected.pdf";
        a.click();
    }
}

async function runPdfWatermark() {
    const fileInput = document.getElementById('watermarkFileInput');
    const text = document.getElementById('watermarkTextInput').value;
    if (!fileInput.files.length) return alert("Select PDF file.");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('watermark_text', text);

    const response = await fetch('/api/pdf/watermark', { method: 'POST', body: formData });
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "watermarked.pdf";
        a.click();
    }
}

async function runPdfDigitalSignature() {
    const fileInput = document.getElementById('signFileInput');
    const name = document.getElementById('signerNameInput').value;
    if (!fileInput.files.length) return alert("Select PDF file.");

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('signer_name', name);

    const response = await fetch('/api/pdf/digital-signature', { method: 'POST', body: formData });
    const data = await response.json();
    alert(`Digital Signature Applied!\nSigner: ${data.signer}\nEncryption: ${data.encryption}\nStatus: ${data.status}`);
}

async function fetchExpenseReport() {
    try {
        const res = await fetch('/api/expense/report');
        const data = await res.json();

        document.getElementById('totalSpendVal').textContent = `$${data.total_spend.toFixed(2)}`;
        document.getElementById('totalGstVal').textContent = `$${data.total_gst_reclaimable.toFixed(2)}`;
        document.getElementById('totalCountVal').textContent = data.total_expenses_count;

        const tbody = document.getElementById('expenseTableBody');
        tbody.innerHTML = data.recent_expenses.map(exp => `
            <tr class="border-b border-gray-800 hover:bg-gray-800/50">
                <td class="p-2 font-mono">${exp.id}</td>
                <td class="p-2 font-medium">${exp.vendor}</td>
                <td class="p-2"><span class="px-2 py-0.5 rounded text-xxs bg-indigo-900/60 text-indigo-300 border border-indigo-700">${exp.category}</span></td>
                <td class="p-2">${exp.date}</td>
                <td class="p-2 font-semibold text-white">$${exp.amount.toFixed(2)}</td>
                <td class="p-2 text-green-400">$${exp.gst_amount.toFixed(2)}</td>
            </tr>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

async function fetchWorkflows() {
    try {
        const res = await fetch('/api/workflow/list');
        const list = await res.json();
        const container = document.getElementById('workflowList');
        container.innerHTML = list.map(wf => `
            <div class="p-3 bg-gray-950 rounded border border-gray-800 space-y-1">
                <div class="flex justify-between items-center">
                    <span class="font-bold text-teal-300">${wf.id}: ${wf.document_name}</span>
                    <span class="px-2 py-0.5 rounded text-xxs bg-yellow-900/60 text-yellow-300 border border-yellow-700">${wf.status}</span>
                </div>
                <div class="text-gray-400 text-xxs">Assigned: ${wf.assigned_role} | Step: ${wf.current_step}</div>
            </div>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

async function runCloudSync() {
    const provider = document.getElementById('cloudProviderSelect').value;
    const statusBox = document.getElementById('cloudSyncStatus');
    statusBox.textContent = `Syncing files to ${provider}...`;

    const res = await fetch('/api/cloud/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: provider, filename: "scanned_doc_2026.pdf" })
    });
    const data = await res.json();
    statusBox.textContent = `Status: ${data.status} -> ${data.remote_uri}`;
}

function toggleVoiceModal() {
    const cmd = prompt("Voice Assistant Voice Command Simulation:\ne.g. 'Scan invoice', 'Summarize document', or 'Translate to Tamil'");
    if (cmd) {
        fetch('/api/ai/voice-command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: cmd, text_content: currentExtractedText })
        }).then(res => res.json()).then(data => {
            alert(`Voice Intent Recognized: ${data.recognized_intent.toUpperCase()}\n\nExecution Result:\n${JSON.stringify(data.execution_result, null, 2)}`);
        });
    }
}
