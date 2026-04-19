import { fetchPen } from 'codepen-fetcher';
import fs from 'fs/promises';
import path from 'path';

/**
 * Extract the pen ID from a CodePen URL.
 * Supports formats like:
 *   - https://codepen.io/username/pen/abc123
 *   - https://codepen.io/username/details/abc123
 *   - https://codepen.io/username/full/abc123
 */
function extractPenId(url) {
  const regex = /codepen\.io\/[^/]+\/(?:pen|details|full|embed)\/([a-zA-Z0-9]+)/;
  const match = url.match(regex);
  if (!match) {
    throw new Error(`Could not extract pen ID from URL: ${url}`);
  }
  return match[1];
}

async function main() {
  const codePenUrl = process.argv[2];
  if (!codePenUrl) {
    console.error('Error: CodePen URL is required.');
    console.error('Usage: node fetch_codepen.js <CodePen URL>');
    process.exit(1);
  }

  try {
    const penId = extractPenId(codePenUrl);
    console.log(`Fetching pen: ${penId}`);

    const pen = await fetchPen(penId);
    const { html, css, js } = pen.config;

    // Create output directory
    const outputDir = 'codepen_export';
    await fs.mkdir(outputDir, { recursive: true });

    // Write files (even if empty)
    await fs.writeFile(path.join(outputDir, 'index.html'), html || '<!-- No HTML -->');
    await fs.writeFile(path.join(outputDir, 'style.css'), css || '/* No CSS */');
    await fs.writeFile(path.join(outputDir, 'script.js'), js || '// No JavaScript');

    console.log('✅ Successfully downloaded CodePen source:');
    console.log(`   📄 HTML → ${outputDir}/index.html`);
    console.log(`   🎨 CSS  → ${outputDir}/style.css`);
    console.log(`   ⚡ JS   → ${outputDir}/script.js`);
  } catch (error) {
    console.error('❌ Error fetching CodePen:', error.message);
    process.exit(1);
  }
}

main();
