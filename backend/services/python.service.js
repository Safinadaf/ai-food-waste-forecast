const { spawn } = require('child_process');
const path = require('path');

// Try 'python3' first on Linux/Mac, fall back to 'python' on Windows
const PY = process.env.PYTHON_BIN || (process.platform === 'win32' ? 'python' : 'python3');
const SCRIPTS_DIR = path.join(__dirname, '..', 'python');
const TIMEOUT_MS = 30000; // 30 second timeout

/**
 * Run a Python script and return parsed JSON from stdout.
 * @param {string} script  e.g. "forecast.py"
 * @param {object} payload sent on stdin as JSON
 */
function runPython(script, payload = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(PY, [path.join(SCRIPTS_DIR, script)], {
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });

    let out = '', err = '';
    let timedOut = false;

    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill();
      reject(new Error(`Python script ${script} timed out after ${TIMEOUT_MS}ms`));
    }, TIMEOUT_MS);

    proc.stdout.on('data', d => (out += d.toString()));
    proc.stderr.on('data', d => (err += d.toString()));

    proc.on('close', code => {
      clearTimeout(timer);
      if (timedOut) return;
      if (code !== 0) return reject(new Error(`python ${script} exited ${code}: ${err.trim()}`));
      try {
        resolve(JSON.parse(out.trim() || '{}'));
      } catch (e) {
        reject(new Error(`Bad JSON from ${script}: ${e.message}\n${out.slice(0, 500)}`));
      }
    });

    proc.on('error', e => {
      clearTimeout(timer);
      reject(new Error(`Failed to start python (${PY}): ${e.message}. Is Python installed?`));
    });

    proc.stdin.write(JSON.stringify(payload));
    proc.stdin.end();
  });
}

module.exports = { runPython };
