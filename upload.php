<?php
$tmp_file = "tmpfile.txt";  // rel this script
$report_path = "";
$txtFileType = strtolower(pathinfo($tmp_file, PATHINFO_EXTENSION));

$failures = array();

check_txt();
check_exists();
check_size();
check_format();
if (count($failures) === 0) {
	run_report();
}

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
            <div class="result-card <?php echo count($failures) === 0 ? "success" : "failed"; ?>">
                <h2><?php echo count($failures) === 0 ? "✓ Success" : "✗ Failed"; ?></h2>
                <?php if (count($failures) === 0): ?>
                    <div class="report-path">📄 <?php echo htmlspecialchars($report_path); ?></div>
                <?php else: ?>
                    <ul class="failure-list">
                        <?php foreach ($failures as $x): ?>
                            <li>⚠️ <?php echo htmlspecialchars($x); ?></li>
                        <?php endforeach; ?>
                    </ul>
                <?php endif; ?>
            </div>
            <a href="index.html" class="back-link">← Upload Another File</a>
        </div>
    </div>
</body>
</html>
<?php

function check_txt() {
	global $failures;
	// Check if txt file is a actual txt or fake txt
	if (isset($_POST["submit"])) {
    	$check = filesize($_FILES["fileToUpload"]["tmp_name"]);
    	if ($check == false) {
        	$failures[] = "File is not an txt.";
    	}
	}
}

function check_exists() {
	global $failures;
	global $tmp_file;
	// Check if file already exists
	if (file_exists($tmp_file)) {
    	$failures[] = "Sorry, file $tmp_file already exists.";
	}
}

function check_size() {
	global $failures;
	// Check file size
	if ($_FILES["fileToUpload"]["size"] > 500000) {
    	$failures[] = "Sorry, your file is too large.";
	}
}

function check_format() {
	global $failures;
	global $txtFileType;
	// Allow certain file formats
	if ($txtFileType != "txt") {
    	$failures[] = "Sorry, only txt files are allowed.";
	}
}

function run_report() {
	global $failures;
	global $tmp_file;
	global $report_path;
    if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $tmp_file)) {
	    // call the python script
	    $pycall = "python word_count_reporter.py $tmp_file --usetitle";
	    if (isset($_POST["backup"])) {
	        $pycall .= " --backup";
	    }
	    $pycall .= " 2>&1";
	    exec($pycall, $output, $retval);
		if ($retval == 0) {
			$report_path = $output[0]; // path to report should be only output
		} else {
            $failures[] = "\nEncountered error code $retval when calling python. Error: ".var_export($output, true);
        }

        // delete the tmp file
        unlink($tmp_file);
    } else {
        $failures[] = "Sorry, there was an error uploading your file.";
    }
}
?>
