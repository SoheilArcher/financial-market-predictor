function renderAssistantAnswer(data) {
  const ranked = data.ranked_opportunities || [];
  const rows = ranked.map((item, index) => `
    <tr>
      <td>${index + 1}</td>
      <td>${item.symbol}</td>
      <td><span class="badge ${String(item.signal).toLowerCase()}">${item.signal}</span></td>
      <td>${item.score}</td>
      <td>${item.expected_quality}</td>
      <td>${item.risk}</td>
      <td>${item.change_percent}%</td>
      <td>${item.reasons.join("<br>")}</td>
    </tr>
  `).join("");

  $("assistantResult").className = "assistantResultBox";
  $("assistantResult").innerHTML = `
    <div class="assistantAnswer">${data.answer_fa}</div>
    <div class="tableWrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>نماد</th>
            <th>سیگنال</th>
            <th>امتیاز</th>
            <th>کیفیت امید</th>
            <th>ریسک</th>
            <th>تغییر</th>
            <th>دلیل</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <p class="assistantDisclaimer">${data.disclaimer}</p>
  `;
}

$("assistantForm")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    $("assistantResult").className = "empty";
    $("assistantResult").textContent = "دستیار معامله‌گر در حال مقایسه فرصت‌هاست...";
    const payload = {
      question: $("assistantQuestion").value.trim(),
      timeframe: $("assistantTimeframe").value || null,
      limit: 120,
    };
    const data = await api("/assistant/ask", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderAssistantAnswer(data);
    await refreshMe();
  } catch (error) {
    $("assistantResult").className = "empty";
    $("assistantResult").textContent = error.message;
  }
});
