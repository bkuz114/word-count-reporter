<?php
/**
 * Word Count Reporter - Web Upload Interface
 *
 * Receives uploaded .txt input files, validates them, and invokes the
 * Python word_count_reporter.py script to generate an HTML report.
 *
 * Security: Implements file validation, command escaping, output encoding,
 * and unique temporary filenames to prevent injection and race conditions.
 *
 * IMPORTANT: Input files must use ABSOLUTE PATHS for chapter files (or
 * for root key within [keys] directive) because the uploaded input file
 * is moved to the server's script directory.
 */

// Configuration
define('MAX_FILE_SIZE', 500 * 1024); // 500KB
define('TEMP_DIR', __DIR__ . '/tmp');  // Isolated directory
define('PYTHON_SCRIPT', dirname(__DIR__) . '/word_count_reporter.py');
define('ALLOWED_EXTENSIONS', ['txt']);

// Ensure temp directory exists
if (!is_dir(TEMP_DIR)) {
    mkdir(TEMP_DIR, 0755, true);
}

$failures = [];
$report_path = '';
$tmp_file = null;

// Only process POST requests
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    validate_upload();

    if (empty($failures)) {
        run_report();
    }

    // Clean up temp file if it exists
    if ($tmp_file && file_exists($tmp_file)) {
        unlink($tmp_file);
    }
}

/**
 * Validates the uploaded file thoroughly.
 */
function validate_upload(): void {
    global $failures, $tmp_file;

    // Check if file was uploaded without errors
    if (!isset($_FILES['fileToUpload']) || $_FILES['fileToUpload']['error'] !== UPLOAD_ERR_OK) {
        $errors = [
            UPLOAD_ERR_INI_SIZE => 'File exceeds server upload limit.',
            UPLOAD_ERR_FORM_SIZE => 'File exceeds form upload limit.',
            UPLOAD_ERR_PARTIAL => 'File was only partially uploaded.',
            UPLOAD_ERR_NO_FILE => 'No file was uploaded.',
            UPLOAD_ERR_NO_TMP_DIR => 'Missing temporary folder.',
            UPLOAD_ERR_CANT_WRITE => 'Failed to write file to disk.',
            UPLOAD_ERR_EXTENSION => 'File upload stopped by extension.',
        ];
        $error_code = $_FILES['fileToUpload']['error'] ?? UPLOAD_ERR_NO_FILE;
        $failures[] = $errors[$error_code] ?? 'Unknown upload error.';
        return;
    }

    $file = $_FILES['fileToUpload'];

    // Check file size
    if ($file['size'] > MAX_FILE_SIZE) {
        $failures[] = sprintf('File too large. Maximum size: %d KB.', MAX_FILE_SIZE / 1024);
        return;
    }

    // Validate extension only (rely on Python for content validation)
    $extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
    if (!in_array($extension, ALLOWED_EXTENSIONS)) {
        $failures[] = 'Invalid file type. Only .txt files are allowed.';
        return;
    }

    // Create unique temporary filename
    $tmp_file = TEMP_DIR . '/' . bin2hex(random_bytes(16)) . '.txt';

    if (!move_uploaded_file($file['tmp_name'], $tmp_file)) {
        $failures[] = 'Failed to save uploaded file.';
        $tmp_file = null;
        return;
    }

    // Verify file was written successfully
    if (!file_exists($tmp_file) || filesize($tmp_file) === 0) {
        $failures[] = 'Uploaded file is empty or could not be saved.';
        if ($tmp_file && file_exists($tmp_file)) {
            unlink($tmp_file);
        }
        $tmp_file = null;
    }
}

/**
 * Executes the Python report generator.
 */
function run_report(): void {
    global $failures, $report_path, $tmp_file;

    // Verify Python script exists and is readable
    if (!file_exists(PYTHON_SCRIPT)) {
        $failures[] = 'Python script not found: ' . htmlspecialchars(PYTHON_SCRIPT);
        return;
    }

    if (!is_executable(PYTHON_SCRIPT) && !str_contains(PHP_OS, 'WIN')) {
        // On Unix-like systems, check executable bit
        $failures[] = 'Python script is not executable.';
        return;
    }

    // Build command with proper escaping
    $pycall = escapeshellcmd('python') 
        . ' ' . escapeshellarg(PYTHON_SCRIPT)
        . ' ' . escapeshellarg($tmp_file)
        . ' --usetitle';

    if (isset($_POST['backup']) && $_POST['backup'] === 'on') {
        $pycall .= ' --backup';
    }

    $pycall .= ' 2>&1';

    // Execute with timeout (30 seconds)
    $descriptorspec = [
        1 => ['pipe', 'w'],  // stdout
        2 => ['pipe', 'w'],  // stderr
    ];

    $process = proc_open($pycall, $descriptorspec, $pipes);

    if (!is_resource($process)) {
        $failures[] = 'Failed to execute Python script.';
        return;
    }

    // Set stream timeout
    stream_set_timeout($pipes[1], 30);
    stream_set_timeout($pipes[2], 30);

    $output = stream_get_contents($pipes[1]);
    $errors = stream_get_contents($pipes[2]);

    fclose($pipes[1]);
    fclose($pipes[2]);

    $retval = proc_close($process);

    if ($retval === 0 && !empty($output)) {
        // First line of output should be the report path
        $lines = explode("\n", trim($output));
        $report_path = trim($lines[0]);

        // Verify report was actually created
        if (!file_exists($report_path)) {
            $failures[] = 'Python script reported success but report file not found: ' . htmlspecialchars($report_path);
            $report_path = '';
        }
    } else {
        $error_msg = !empty($errors) ? $errors : $output;
        $failures[] = sprintf(
            'Python script failed (code %d): %s',
            $retval,
            htmlspecialchars(substr(trim($error_msg), 0, 5000))
        );
    }
}

// Determine result card CSS class
$result_class = empty($failures) ? 'success' : 'failed';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="style.css">
    <title>Word Count Reporter - Result</title>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Word Count Reporter</h1>
            <p>Report Generation Result</p>
        </div>
        <div class="content">
            <div class="result-card <?php echo $result_class; ?>">
                <h2><?php echo empty($failures) ? '✓ Success' : '✗ Failed'; ?></h2>
                <?php if (empty($failures)): ?>
                    <div class="report-path">📄 <?php echo htmlspecialchars($report_path); ?></div>
                <?php else: ?>
                    <ul class="failure-list">
                        <?php foreach ($failures as $failure): ?>
                            <li>⚠️ <?php echo htmlspecialchars($failure); ?></li>
                        <?php endforeach; ?>
                    </ul>
                <?php endif; ?>
            </div>
            <a href="index.html" class="back-link">← Upload Another File</a>
        </div>
    </div>
</body>
</html>
