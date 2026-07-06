/**
 * Markdown-to-HTML renderer for the document preview panel.
 * Uses a lightweight regex-based approach (no external dependencies).
 */

/**
 * Convert markdown text to sanitized HTML.
 * Handles: headings, bold, italic, lists, tables, code blocks, links, paragraphs.
 */
export function markdownToHtml(md: string): string {
  if (!md) return "";

  let html = md;

  // Escape HTML entities first
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code blocks (fenced)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_match, lang, code) => {
    return `<pre class="code-block"><code class="language-${lang}">${code.trim()}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  // Headings
  html = html.replace(/^######\s+(.+)$/gm, '<h6 class="md-h6">$1</h6>');
  html = html.replace(/^#####\s+(.+)$/gm, '<h5 class="md-h5">$1</h5>');
  html = html.replace(/^####\s+(.+)$/gm, '<h4 class="md-h4">$1</h4>');
  html = html.replace(/^###\s+(.+)$/gm, '<h3 class="md-h3">$1</h3>');
  html = html.replace(/^##\s+(.+)$/gm, '<h2 class="md-h2">$1</h2>');
  html = html.replace(/^#\s+(.+)$/gm, '<h1 class="md-h1">$1</h1>');

  // Bold + Italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Horizontal rules
  html = html.replace(/^---+$/gm, '<hr class="md-hr" />');
  html = html.replace(/^\*\*\*+$/gm, '<hr class="md-hr" />');

  // Unordered lists
  html = html.replace(/^[\s]*[-*]\s+(.+)$/gm, '<li class="md-li">$1</li>');
  html = html.replace(
    /(<li class="md-li">.*<\/li>\n?)+/g,
    '<ul class="md-ul">$&</ul>'
  );

  // Tables (simplified)
  html = html.replace(
    /^\|(.+)\|\s*\n\|[-|\s]+\|\s*\n((?:\|.+\|\s*\n?)*)/gm,
    (_match, headerRow: string, bodyRows: string) => {
      const headers = headerRow
        .split("|")
        .map((h: string) => h.trim())
        .filter(Boolean);
      const rows = bodyRows
        .trim()
        .split("\n")
        .map((row: string) =>
          row
            .split("|")
            .map((c: string) => c.trim())
            .filter(Boolean)
        );

      let table = '<table class="md-table"><thead><tr>';
      headers.forEach((h: string) => {
        table += `<th>${h}</th>`;
      });
      table += "</tr></thead><tbody>";
      rows.forEach((row: string[]) => {
        table += "<tr>";
        row.forEach((cell: string) => {
          table += `<td>${cell}</td>`;
        });
        table += "</tr>";
      });
      table += "</tbody></table>";
      return table;
    }
  );

  // Links
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>'
  );

  // Paragraphs (wrap remaining lines)
  html = html
    .split("\n\n")
    .map((block) => {
      const trimmed = block.trim();
      if (!trimmed) return "";
      // Skip if already wrapped in HTML tags
      if (/^<(?:h[1-6]|ul|ol|li|pre|table|hr|div|blockquote)/i.test(trimmed)) {
        return trimmed;
      }
      return `<p class="md-p">${trimmed.replace(/\n/g, "<br />")}</p>`;
    })
    .join("\n");

  return html;
}

/**
 * Format a currency amount with locale-appropriate separators.
 */
export function formatCurrency(
  amount: number,
  symbol: string = "₹"
): string {
  if (!amount) return `${symbol}0`;
  // Indian number system for INR
  if (symbol === "₹") {
    const str = Math.floor(amount).toString();
    let formatted = "";
    const len = str.length;
    if (len <= 3) {
      formatted = str;
    } else {
      formatted = str.slice(-3);
      let remaining = str.slice(0, -3);
      while (remaining.length > 2) {
        formatted = remaining.slice(-2) + "," + formatted;
        remaining = remaining.slice(0, -2);
      }
      if (remaining) {
        formatted = remaining + "," + formatted;
      }
    }
    return `${symbol}${formatted}`;
  }
  return `${symbol}${amount.toLocaleString()}`;
}
